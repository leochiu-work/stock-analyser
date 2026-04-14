/**
 * Integration tests for the /api/prices Next.js route handler.
 * We import the handler directly and call it with mock NextRequest objects.
 *
 * Uses the node test environment so that Node 20's native Web Fetch globals
 * (Request, Response, Headers) are available — required by NextRequest.
 *
 * @jest-environment node
 */
import { GET } from '@/app/api/prices/route';
import { NextRequest } from 'next/server';

function makeRequest(search: string): NextRequest {
  return new NextRequest(`http://localhost/api/prices${search}`);
}

const mockUpstreamData = {
  ticker: 'AAPL',
  total: 1,
  offset: 0,
  limit: 50,
  items: [{ ticker: 'AAPL', date: '2024-01-15', open: 185, high: 188, low: 184, close: 187 }],
};

describe('GET /api/prices route', () => {
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
    expect(body.ticker).toBe('AAPL');
    expect(body.items).toHaveLength(1);
  });

  it('uppercases the ticker when building upstream URL', async () => {
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

    await GET(makeRequest('?ticker=AAPL&start_date=2024-01-01&end_date=2024-01-31&offset=10&limit=25'));
    const [calledUrl] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('start_date=2024-01-01');
    expect(calledUrl).toContain('end_date=2024-01-31');
    expect(calledUrl).toContain('offset=10');
    expect(calledUrl).toContain('limit=25');
  });

  it('returns 502 when upstream fetch throws', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Connection refused'));

    const response = await GET(makeRequest('?ticker=AAPL'));
    expect(response.status).toBe(502);
    const body = await response.json();
    expect(body).toEqual({ error: 'Failed to reach price service' });
  });

  it('proxies upstream error status codes', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: jest.fn().mockResolvedValue({ detail: 'Not found' }),
    });

    const response = await GET(makeRequest('?ticker=UNKNOWN'));
    expect(response.status).toBe(404);
  });
});
