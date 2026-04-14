import { fetchNews } from '@/lib/api/news';

const mockNewsResponse = {
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
  ],
};

function makeFetchMock(body: unknown, status = 200) {
  return jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(body),
  });
}

describe('fetchNews', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns news data on success', async () => {
    global.fetch = makeFetchMock(mockNewsResponse);
    const result = await fetchNews({ ticker: 'AAPL' });
    expect(result.total).toBe(2);
    expect(result.items).toHaveLength(1);
    expect(result.items[0].headline).toBe('Apple Reports Strong Q1 Earnings');
  });

  it('throws error with server message on non-2xx response', async () => {
    global.fetch = makeFetchMock({ error: 'Not found' }, 404);
    await expect(fetchNews({ ticker: 'AAPL' })).rejects.toThrow('Not found');
  });

  it('throws HTTP status error when response body has no error field', async () => {
    global.fetch = makeFetchMock({}, 502);
    await expect(fetchNews({ ticker: 'AAPL' })).rejects.toThrow('HTTP 502');
  });

  it('builds URL with only ticker when no optional params given', async () => {
    global.fetch = makeFetchMock(mockNewsResponse);
    await fetchNews({ ticker: 'AAPL' });
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('ticker=AAPL');
    expect(calledUrl).not.toContain('start_date');
    expect(calledUrl).not.toContain('limit');
  });

  it('builds correct query string with all params', async () => {
    global.fetch = makeFetchMock({ total: 0, offset: 0, limit: 10, items: [] });
    await fetchNews({ ticker: 'MSFT', limit: 10, offset: 0 });
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('ticker=MSFT');
    expect(calledUrl).toContain('limit=10');
  });

  it('includes date params when provided', async () => {
    global.fetch = makeFetchMock({ total: 0, offset: 0, limit: 50, items: [] });
    await fetchNews({ ticker: 'GOOG', start_date: '2024-01-01', end_date: '2024-01-31' });
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('start_date=2024-01-01');
    expect(calledUrl).toContain('end_date=2024-01-31');
  });
});
