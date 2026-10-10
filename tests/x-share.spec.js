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

// キュー上のタグを1行1曲で取得する(値が無い曲は空行)
function queueTags(tag) {
  return mpc(['playlist', '-f', `%${tag}%`]).split('\n');
}

// 条件に合う曲をキューから探しファイル名を返す(見つからない場合はnull)
function findQueuedFile(predicate) {
  const files = queueTags('file');
  const artists = queueTags('artist');
  const titles = queueTags('title');
  const albums = queueTags('album');

  for (let i = 0; i < files.length; i += 1) {
    // ストリーム(http)はsearchplayで再現できないため除外
    if (files[i].startsWith('http')) {
      continue;
    }
    if (predicate({
      file: files[i], artist: artists[i], title: titles[i], album: albums[i],
    })) {
      return files[i];
    }
  }

  return null;
}

// 実装と同じ規則でタグより本文を算出する(独立検算用)
function expectedBody() {
  const artist = mpc(['current', '-f', '%artist%']);
  const title = mpc(['current', '-f', '%title%']);
  const album = mpc(['current', '-f', '%album%']);

  if (artist !== '' && title !== '' && album !== '') {
    return mpc(['current', '-f', DEFAULT_TEMPLATE]);
  }
  if (artist !== '' && title !== '') {
    return `Now Playing: ${artist} - ${title}`;
  }
  if (artist !== '') {
    return `Now Playing: ${artist}`;
  }
  if (title !== '') {
    return `Now Playing: ${title}`;
  }

  const name = mpc(['current', '-f', '%name%']);
  return `Now Playing: ${name !== '' ? name : mpc(['current', '-f', '%file%'])}`;
}

// ページより共有本文を取り出す(URLデコード後)
async function shareBody(page) {
  const link = page.locator(SHARE_LINK).first();
  await expect(link).toHaveCount(1);

  const href = await link.getAttribute('href');
  expect(href).not.toBeNull();
  if (href === null) {
    return '';
  }

  const raw = rawShareText(href.slice(INTENT_PREFIX.length));
  expect(raw).not.toBeNull();
  if (raw === null) {
    return '';
  }

  return decodeURIComponent(raw);
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

    // 本文はタグの状態より独立に算出した値と一致する
    expect(decodeURIComponent(raw)).toBe(expectedBody());
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

  test('radio-like track (artist missing, title present) shares the title only', async ({ page }) => {
    const file = findQueuedFile((song) => song.artist === '' && song.title !== '');
    test.skip(file === null, 'アーティスト空・タイトル有の曲がキューに無い');
    if (file === null) {
      return;
    }

    // 当該の曲を再生する
    mpc(['searchplay', 'filename', file]);
    const title = mpc(['current', '-f', '%title%']);

    await page.goto(INDEX_URL);

    const body = await shareBody(page);
    expect(body).toBe(`Now Playing: ${title}`);
    // 区切り記号と空の括弧が残らない
    expect(body).not.toMatch(/\(\s*\)/);
    expect(body).not.toContain('Now Playing:  ');
    expect(body).not.toMatch(/ - $/);
  });

  test('album-less track shares artist and title without empty parentheses', async ({ page }) => {
    const file = findQueuedFile(
      (song) => song.artist !== '' && song.title !== '' && song.album === '',
    );
    test.skip(file === null, 'アルバム名が空の曲がキューに無い');
    if (file === null) {
      return;
    }

    // 当該の曲を再生する
    mpc(['searchplay', 'filename', file]);
    const artist = mpc(['current', '-f', '%artist%']);
    const title = mpc(['current', '-f', '%title%']);

    await page.goto(INDEX_URL);

    const body = await shareBody(page);
    expect(body).toBe(`Now Playing: ${artist} - ${title}`);
    expect(body).not.toMatch(/\(\s*\)/);
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
