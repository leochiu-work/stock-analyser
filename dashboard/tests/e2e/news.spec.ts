import { test, expect } from '@playwright/test';

const mockNewsResponse = JSON.stringify({
  total: 2,
  offset: 0,
  limit: 50,
  items: [
    {
      ticker_symbol: 'AAPL',
      finnhub_id: 1001,
      headline: 'Apple Reports Strong Q1 Earnings',
      summary: 'Apple Inc. reported earnings above expectations.',
      source: 'Reuters',
      url: 'https://example.com/news/1',
      image: null,
      category: 'company news',
      published_at: '2024-01-15T10:00:00Z',
    },
    {
      ticker_symbol: 'AAPL',
      finnhub_id: 1002,
      headline: 'Apple Vision Pro Launch',
      summary: null,
      source: 'Bloomberg',
      url: 'https://example.com/news/2',
      image: null,
      category: 'technology',
      published_at: '2024-01-16T14:00:00Z',
    },
  ],
});

test.beforeEach(async ({ page }) => {
  await page.route('**/api/news**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: mockNewsResponse,
    })
  );
});

test('loads news page heading', async ({ page }) => {
  await page.goto('/news');
  await expect(page.getByRole('heading', { name: /stock news/i })).toBeVisible();
});

test('renders news card headlines', async ({ page }) => {
  await page.goto('/news');
  await expect(page.getByText('Apple Reports Strong Q1 Earnings')).toBeVisible();
  await expect(page.getByText('Apple Vision Pro Launch')).toBeVisible();
});

test('news card shows source', async ({ page }) => {
  await page.goto('/news');
  await expect(page.getByText('Reuters')).toBeVisible();
  await expect(page.getByText('Bloomberg')).toBeVisible();
});

test('news card shows category badge', async ({ page }) => {
  await page.goto('/news');
  await expect(page.getByText('company news')).toBeVisible();
  await expect(page.getByText('technology')).toBeVisible();
});

test('news card has correct external link', async ({ page }) => {
  await page.goto('/news');
  const links = page.getByRole('link', { name: /read more/i });
  await expect(links.first()).toHaveAttribute('href', 'https://example.com/news/1');
  await expect(links.first()).toHaveAttribute('target', '_blank');
});

test('shows empty state when no news articles', async ({ page }) => {
  await page.route('**/api/news**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, offset: 0, limit: 50, items: [] }),
    })
  );
  await page.goto('/news');
  await expect(page.getByText(/no news articles found/i)).toBeVisible();
});

test('shows error alert when news API fails', async ({ page }) => {
  await page.route('**/api/news**', (route) =>
    route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Failed to reach news service' }),
    })
  );
  await page.goto('/news');
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByText(/failed to reach news service/i)).toBeVisible();
});

test('pagination is not shown when only one page', async ({ page }) => {
  await page.goto('/news');
  // total=2, limit=50 → 1 page → no pagination
  await expect(page.getByRole('navigation', { name: /pagination/i })).not.toBeVisible();
});

test('news card shows summary when provided', async ({ page }) => {
  await page.goto('/news');
  await expect(page.getByText(/Apple Inc. reported earnings above expectations/i)).toBeVisible();
});
