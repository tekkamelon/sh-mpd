// @ts-check
const { test, expect } = require('@playwright/test');

const INDEX_URL = '/cgi-bin/index.cgi';

test.describe('Home page', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX_URL);
  });

  test('search feature is removed', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Search' })).toHaveCount(0);
    await expect(page.locator('form[name="search_form"]')).toHaveCount(0);
    await expect(page.locator('input[name="search"]')).toHaveCount(0);

    const content = await page.content();
    expect(content).not.toMatch(/searchplay/i);
  });

  test('control panel and other sections remain', async ({ page }) => {
    await expect(page).toHaveTitle(/HOME/);
    await expect(page.locator('form[name="control_form"] button')).toHaveCount(16);
    await expect(page.getByRole('heading', { name: 'Now Playing' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Next in Queue' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

});
