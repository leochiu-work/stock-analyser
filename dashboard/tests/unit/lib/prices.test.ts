import { fetchPrices } from '@/lib/api/prices';

const mockPriceResponse = {
  ticker: 'AAPL',
  total: 2,
  offset: 0,
  limit: 50,
  items: [
    { ticker: 'AAPL', date: '2024-01-15', open: 185.0, high: 188.5, low: 184.0, close: 187.2 },
    { ticker: 'AAPL', date: '2024-01-16', open: 187.2, high: 190.0, low: 186.0, close: 185.5 },
  ],
};

function makeFetchMock(body: unknown, status = 200) {
  return jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(body),
  });
}

describe('fetchPrices', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns price data on success', async () => {
    global.fetch = makeFetchMock(mockPriceResponse);
    const result = await fetchPrices({ ticker: 'AAPL' });
    expect(result.ticker).toBe('AAPL');
    expect(result.items).toHaveLength(2);
    expect(result.items[0]).toMatchObject({ date: '2024-01-15', open: 185.0, close: 187.2 });
  });

  it('throws error with server message on non-2xx response', async () => {
    global.fetch = makeFetchMock({ error: 'Service unavailable' }, 503);
    await expect(fetchPrices({ ticker: 'AAPL' })).rejects.toThrow('Service unavailable');
  });

  it('throws HTTP status error when response body has no error field', async () => {
    global.fetch = makeFetchMock({}, 500);
    await expect(fetchPrices({ ticker: 'AAPL' })).rejects.toThrow('HTTP 500');
  });

  it('builds URL with only ticker when no optional params given', async () => {
    global.fetch = makeFetchMock(mockPriceResponse);
    await fetchPrices({ ticker: 'AAPL' });
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('ticker=AAPL');
    expect(calledUrl).not.toContain('start_date');
    expect(calledUrl).not.toContain('end_date');
    expect(calledUrl).not.toContain('offset');
    expect(calledUrl).not.toContain('limit');
  });

  it('builds correct query string with all params', async () => {
    global.fetch = makeFetchMock({ ticker: 'TSLA', total: 0, offset: 10, limit: 25, items: [] });
    await fetchPrices({
      ticker: 'TSLA',
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      offset: 10,
      limit: 25,
    });
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('ticker=TSLA');
    expect(calledUrl).toContain('start_date=2024-01-01');
    expect(calledUrl).toContain('end_date=2024-01-31');
    expect(calledUrl).toContain('offset=10');
    expect(calledUrl).toContain('limit=25');
  });
});
