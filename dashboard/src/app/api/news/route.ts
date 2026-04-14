import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker');

  if (!ticker) {
    return NextResponse.json({ error: 'ticker is required' }, { status: 400 });
  }

  const upstreamParams = new URLSearchParams();
  ['start_date', 'end_date', 'offset', 'limit'].forEach((key) => {
    const val = searchParams.get(key);
    if (val !== null) upstreamParams.set(key, val);
  });

  const baseUrl = process.env.NEWS_API_BASE_URL || 'http://localhost:8001';
  const url = `${baseUrl}/api/v1/news/${encodeURIComponent(ticker.toUpperCase())}?${upstreamParams.toString()}`;

  try {
    const upstream = await fetch(url, { cache: 'no-store' });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ error: 'Failed to reach news service' }, { status: 502 });
  }
}
