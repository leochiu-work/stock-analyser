import useSWR from 'swr';
import { fetchWatchlist } from '@/lib/api/watchlist';
import { WatchlistResponse } from '@/lib/types';

export function useWatchlist() {
  return useSWR<WatchlistResponse>('watchlist', fetchWatchlist);
}
