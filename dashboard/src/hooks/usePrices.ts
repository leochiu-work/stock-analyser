import useSWR from 'swr';
import { fetchPrices } from '@/lib/api/prices';
import { PriceQueryParams, StockPriceListResponse } from '@/lib/types';

export function usePrices(params: PriceQueryParams | null) {
  return useSWR<StockPriceListResponse>(
    params ? ['prices', JSON.stringify(params)] : null,
    () => fetchPrices(params!),
    { keepPreviousData: true }
  );
}
