import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

export const mockPriceData = {
  ticker: 'AAPL',
  total: 2,
  offset: 0,
  limit: 50,
  items: [
    { ticker: 'AAPL', date: '2024-01-15', open: 185.0, high: 188.5, low: 184.0, close: 187.2 },
    { ticker: 'AAPL', date: '2024-01-16', open: 187.2, high: 190.0, low: 186.0, close: 185.5 },
  ],
};

export const mockNewsData = {
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
      headline: 'Apple Vision Pro Launch Date Confirmed',
      summary: null,
      source: 'Bloomberg',
      url: 'https://example.com/news/2',
      image: 'https://example.com/images/apple.jpg',
      category: 'technology',
      published_at: '2024-01-16T14:00:00Z',
    },
  ],
};

export const handlers = [
  http.get('http://localhost/api/prices', ({ request }) => {
    const url = new URL(request.url);
    const ticker = url.searchParams.get('ticker');
    if (!ticker) {
      return HttpResponse.json({ error: 'ticker is required' }, { status: 400 });
    }
    return HttpResponse.json({ ...mockPriceData, ticker });
  }),
  http.get('http://localhost/api/news', ({ request }) => {
    const url = new URL(request.url);
    const ticker = url.searchParams.get('ticker');
    if (!ticker) {
      return HttpResponse.json({ error: 'ticker is required' }, { status: 400 });
    }
    return HttpResponse.json(mockNewsData);
  }),
];

export const server = setupServer(...handlers);
