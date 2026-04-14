/**
 * Integration tests for the /api/news Next.js route handler.
 *
 * Uses the node test environment so that Node 20's native Web Fetch globals
 * (Request, Response, Headers) are available — required by NextRequest.
 *
 * @jest-environment node
 */
import { GET } from '@/app/api/news/route';
import { NextRequest } from 'next/server';

function makeRequest(search: string): NextRequest {
  return new NextRequest(`http://localhost/api/news${search}`);
}

const mockUpstreamData = {
  total: 1,
  offset: 0,
  limit: 50,
  items: [
    {
      ticker_symbol: 'AAPL',
      finnhub_id: 1001,
      headline: 'Apple Reports Strong Q1 Earnings',
      summary: 'Apple reported strong earnings.',
      source: 'Reuters',
      url: 'https://example.com/news/1',
      image: null,
      category: 'company news',
      published_at: '2024-01-15T10:00:00Z',
    },
  ],
};

describe('GET /api/news route', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns 400 when ticker is missing', async () => {
    const response = await GET(makeRequest(''));
    expect(response.status).toBe(400);
    const body = await response.json();
    expect(body).toEqual({ error: 'ticker is required' });
  });

  it('proxies successful upstream response', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockUpstreamData),
    });

    const response = await GET(makeRequest('?ticker=AAPL'));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.total).toBe(1);
    expect(body.items[0].headline).toBe('Apple Reports Strong Q1 Earnings');
  });

  it('uppercases ticker in upstream URL', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockUpstreamData),
    });

    await GET(makeRequest('?ticker=aapl'));
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('AAPL');
  });

  it('forwards optional query params to upstream', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockUpstreamData),
    });

    await GET(makeRequest('?ticker=AAPL&start_date=2024-01-01&end_date=2024-01-31&limit=10'));
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('start_date=2024-01-01');
    expect(calledUrl).toContain('end_date=2024-01-31');
    expect(calledUrl).toContain('limit=10');
  });

  it('returns 502 when upstream fetch throws', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Connection refused'));

    const response = await GET(makeRequest('?ticker=AAPL'));
    expect(response.status).toBe(502);
    const body = await response.json();
    expect(body).toEqual({ error: 'Failed to reach news service' });
  });

  it('proxies upstream error status codes', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: jest.fn().mockResolvedValue({ detail: 'Service Unavailable' }),
    });

    const response = await GET(makeRequest('?ticker=AAPL'));
    expect(response.status).toBe(503);
  });
});
