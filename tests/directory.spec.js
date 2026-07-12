// @ts-check
const { test, expect } = require('@playwright/test');

const DIRECTORY_URL = '/cgi-bin/directory/directory.cgi';

test.describe('Directory filer UI', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(DIRECTORY_URL);
  });

  test('page renders title and sections', async ({ page }) => {
    await expect(page).toHaveTitle(/Directory/);
    await expect(page.locator('h1')).toHaveText('Directory');
    await expect(page.getByRole('heading', { name: 'Files' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible();
  });

  test('uses details/summary tree instead of flat list', async ({ page }) => {
    const trees = page.locator('form.directory-list details.dir-tree');
    await expect(trees.first()).toBeVisible();
    await expect(await trees.count()).toBeGreaterThan(0);

    const summaries = page.locator('form.directory-list details.dir-tree > summary');
    await expect(summaries.first()).toBeVisible();
    await expect(await summaries.count()).toBeGreaterThan(0);
  });

  test('child details open when summary is clicked (no JS required)', async ({ page }) => {
    const root = page.locator('form.directory-list > details.dir-tree').first();
    await expect(root).toBeVisible();

    // 初期状態は閉じている
    await expect(root).not.toHaveAttribute('open', '');

    await root.locator('> summary').click();
    await expect(root).toHaveAttribute('open', '');

    // 子階層またはファイルボタンが現れる
    const childDetails = root.locator('> details.dir-tree');
    const childButtons = root.locator('> p > button[name="add"]');
    const hasChildDir = (await childDetails.count()) > 0;
    const hasFile = (await childButtons.count()) > 0;
    expect(hasChildDir || hasFile).toBeTruthy();

    if (hasChildDir) {
      await childDetails.first().locator('> summary').click();
      await expect(childDetails.first()).toHaveAttribute('open', '');
    }
  });

  test('file buttons have add name and numeric value', async ({ page }) => {
    // ネストが深い場合でもボタンに到達できるよう open を付与して展開
    await page.evaluate(() => {
      document.querySelectorAll('form.directory-list details.dir-tree').forEach((el) => {
        el.setAttribute('open', '');
      });
    });

    const addButtons = page.locator('form.directory-list button[name="add"]');
    await expect(addButtons.first()).toBeVisible();
    const value = await addButtons.first().getAttribute('value');
    expect(value).toMatch(/^\d+$/);
  });

  test('no script tags or inline event handlers', async ({ page }) => {
    const scripts = page.locator('script');
    await expect(scripts).toHaveCount(0);

    const withOnclick = page.locator('[onclick]');
    await expect(withOnclick).toHaveCount(0);

    const content = await page.content();
    expect(content).not.toMatch(/javascript:/i);
  });

  test('scroll navigation uses pure HTML anchors', async ({ page }) => {
    const bottomLink = page.locator('a[href="#bottom"]').first();
    const topLink = page.locator('a[href="#top"]').first();
    await expect(bottomLink).toBeVisible();
    await expect(topLink).toBeVisible();
    await expect(page.locator('#top')).toHaveCount(1);
    await expect(page.locator('#bottom')).toHaveCount(1);
  });

  test('search expands matching tree branches', async ({ page }) => {
    await page.fill('input[name="search_word"]', 'Biosphere');
    await Promise.all([
      page.waitForNavigation(),
      page.click('button[type="submit"]'),
    ]);

    await expect(page).toHaveURL(/search_word=Biosphere|search_word=/);

    const openTrees = page.locator('form.directory-list details.dir-tree[open]');
    await expect(openTrees.first()).toBeVisible();

    // 検索結果に含まれるファイルボタンが表示される
    const buttons = page.locator('form.directory-list button[name="add"]');
    await expect(buttons.first()).toBeVisible();
  });

  test('menu navigation links are present', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/cgi-bin/index.cgi');
    await expect(page.getByRole('link', { name: 'Queued' })).toHaveAttribute('href', '/cgi-bin/queued/queued.cgi');
    await expect(page.getByRole('link', { name: 'Playlist' })).toHaveAttribute('href', '/cgi-bin/playlist/playlist.cgi');
    await expect(page.getByRole('link', { name: 'Settings' })).toHaveAttribute('href', '/cgi-bin/settings/settings.cgi');
  });

});
