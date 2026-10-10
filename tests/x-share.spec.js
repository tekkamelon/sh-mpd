// @ts-check
const { test, expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');

const INDEX_URL = '/cgi-bin/index.cgi';
const INTENT_PREFIX = 'https://twitter.com/intent/tweet?';
const SHARE_LINK = `a[href^="${INTENT_PREFIX}"]`;
const DEFAULT_TEMPLATE = 'Now Playing: %artist% - %title% (%album%)';

// 予約されていない文字 + パーセントエンコードのみで構成されているか
const STRICTLY_ENCODED = /^(?:%[0-9A-F]{2}|[A-Za-z0-9\-._~])*$/;

// MPDの操作にはmpcを使用 (MPD_HOST, MPD_PORTは実行環境より継承)
function mpc(args) {
  return execFileSync('mpc', args, { encoding: 'utf8', env: process.env })
    .replace(/\n$/, '');
}

// hrefより本文(textパラメータ)のエンコード済み文字列を抽出
function rawShareText(href) {
  const match = href.match(/(?:^|[?&])text=([^&]*)/);
  return match ? match[1] : null;
}

test.describe('X share link (Now Playing)', () => {

  test('stopped: no share link is rendered', async ({ page }) => {
    mpc(['stop']);
    await page.goto(INDEX_URL);

    await expect(page.getByRole('heading', { name: 'Now Playing' })).toBeVisible();
    await expect(page.locator(SHARE_LINK)).toHaveCount(0);
  });

  test('playing: link points to web intent with strictly encoded text', async ({ page }) => {
    mpc(['play']);
    await page.goto(INDEX_URL);

    const link = page.locator(SHARE_LINK);
    await expect(link).toHaveCount(1);
    await expect(link).toBeVisible();

    const href = await link.getAttribute('href');
    expect(href).not.toBeNull();
    if (href === null) return;

    expect(href.startsWith(INTENT_PREFIX)).toBeTruthy();

    const query = href.slice(INTENT_PREFIX.length);
    const raw = rawShareText(query);
    expect(raw).not.toBeNull();
    if (raw === null) return;

    // 生の空白,+,&,?,# などを含まず,予約外の文字はすべてエンコードされている
    expect(raw).toMatch(STRICTLY_ENCODED);
    expect(decodeURIComponent(raw)).not.toHaveLength(0);

    // 本文はテンプレートより独立に算出した値と一致する
    const expected = mpc(['current', '-f', DEFAULT_TEMPLATE]);
    if (expected.length > 0) {
      expect(decodeURIComponent(raw)).toBe(expected);
    }
  });

  test('share link opens in a separate tab without JS', async ({ page }) => {
    mpc(['play']);
    await page.goto(INDEX_URL);

    const link = page.locator(SHARE_LINK).first();
    await expect(link).toHaveAttribute('target', '_blank');
    await expect(link).toHaveAttribute('rel', /noopener/);
  });

  test('hashtags parameter is HTML escaped in the source', async ({ page }) => {
    mpc(['play']);
    await page.goto(INDEX_URL);

    const content = await page.content();
    // 属性値の&はエンティティで出力される
    expect(content).toMatch(/href="https:\/\/twitter\.com\/intent\/tweet\?text=[^"]*"/);
    expect(content).not.toMatch(/href="https:\/\/twitter\.com\/intent\/tweet\?[^"]*[^;]&[^a]/);
  });

  test('no script tags or inline event handlers on the home page', async ({ page }) => {
    await page.goto(INDEX_URL);

    await expect(page.locator('script')).toHaveCount(0);

    const content = await page.content();
    expect(content).not.toMatch(/javascript:/i);
  });

  test('existing controls remain after adding the share link', async ({ page }) => {
    await page.goto(INDEX_URL);

    await expect(page).toHaveTitle(/HOME/);
    await expect(page.locator('form[name="control_form"] button')).toHaveCount(16);
    await expect(page.locator('form[name="search_form"]')).toBeVisible();
    await expect(page.locator('img.cover-art')).toHaveCount(1);
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

});
