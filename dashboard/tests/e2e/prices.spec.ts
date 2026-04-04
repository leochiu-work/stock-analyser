import { test, expect } from '@playwright/test';

function makePriceResponse(ticker: string) {
  return JSON.stringify({
    ticker,
    total: 2,
    offset: 0,
    limit: 50,
    items: [
      { ticker, date: '2024-01-15', open: 185, high: 188, low: 184, close: 187 },
      { ticker, date: '2024-01-16', open: 187, high: 190, low: 186, close: 185 },
    ],
  });
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/prices**', (route) => {
    const url = new URL(route.request().url());
    const ticker = url.searchParams.get('ticker') || 'AAPL';
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: makePriceResponse(ticker),
    });
  });
});

test('loads prices page', async ({ page }) => {
  await page.goto('/prices');
  await expect(page.getByRole('heading', { name: /stock prices/i })).toBeVisible();
});

test('ticker input has default AAPL value', async ({ page }) => {
  await page.goto('/prices');
  const tickerInput = page.getByRole('textbox', { name: /stock ticker symbol/i });
  await expect(tickerInput).toHaveValue('AAPL');
});

test('renders price chart SVG', async ({ page }) => {
  await page.goto('/prices');
  // Recharts renders an SVG element
  await expect(page.locator('svg').first()).toBeVisible();
});

test('renders OHLC table column headers', async ({ page }) => {
  await page.goto('/prices');
  await expect(page.getByRole('columnheader', { name: 'Open' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'High' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Low' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Close' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Date' })).toBeVisible();
});

test('renders 2 data rows in OHLC table', async ({ page }) => {
  await page.goto('/prices');
  // 1 header row + 2 data rows = 3 total
  await expect(page.getByRole('row')).toHaveCount(3);
});

test('shows error alert when prices API fails', async ({ page }) => {
  await page.route('**/api/prices**', (route) =>
    route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Failed to reach price service' }),
    })
  );
  await page.goto('/prices');
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByText(/failed to reach price service/i)).toBeVisible();
});

test('pagination is not shown when only one page of results', async ({ page }) => {
  await page.goto('/prices');
  // total=2, limit=50 → only 1 page → no pagination nav
  await expect(page.getByRole('navigation', { name: /pagination/i })).not.toBeVisible();
});

test('chart is not rendered when there is an error', async ({ page }) => {
  await page.route('**/api/prices**', (route) =>
    route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Failed to reach price service' }),
    })
  );
  await page.goto('/prices');
  // When error is shown the chart section is hidden
  await expect(page.getByRole('alert')).toBeVisible();
  // There should be no recharts SVG rendered
  await expect(page.locator('.recharts-wrapper')).not.toBeVisible();
});
