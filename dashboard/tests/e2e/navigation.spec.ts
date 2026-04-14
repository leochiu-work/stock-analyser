import { test, expect } from '@playwright/test';

const mockPriceResponse = JSON.stringify({
  ticker: 'AAPL',
  total: 1,
  offset: 0,
  limit: 50,
  items: [{ ticker: 'AAPL', date: '2024-01-15', open: 185, high: 188, low: 184, close: 187 }],
});

const mockNewsResponse = JSON.stringify({
  total: 0,
  offset: 0,
  limit: 50,
  items: [],
});

test.beforeEach(async ({ page }) => {
  await page.route('**/api/prices**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: mockPriceResponse,
    })
  );
  await page.route('**/api/news**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: mockNewsResponse,
    })
  );
});

test('root / redirects to /prices', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL('/prices');
});

test('sidebar link navigates to News page', async ({ page }) => {
  await page.goto('/prices');
  await page.getByRole('link', { name: /^News$/i }).click();
  await expect(page).toHaveURL('/news');
  await expect(page.getByRole('heading', { name: /stock news/i })).toBeVisible();
});

test('sidebar link navigates to Prices page', async ({ page }) => {
  await page.goto('/news');
  await page.getByRole('link', { name: /^Prices$/i }).click();
  await expect(page).toHaveURL('/prices');
  await expect(page.getByRole('heading', { name: /stock prices/i })).toBeVisible();
});

test('page title is set correctly for prices', async ({ page }) => {
  await page.goto('/prices');
  await expect(page).toHaveTitle(/prices/i);
});

test('page title is set correctly for news', async ({ page }) => {
  await page.goto('/news');
  await expect(page).toHaveTitle(/news/i);
});
