import { PriceQueryParams, StockPriceListResponse } from '@/lib/types';

export async function fetchPrices(params: PriceQueryParams): Promise<StockPriceListResponse> {
  const searchParams = new URLSearchParams({ ticker: params.ticker });
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.offset !== undefined) searchParams.set('offset', String(params.offset));
  if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

  const res = await fetch(`/api/prices?${searchParams.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}
