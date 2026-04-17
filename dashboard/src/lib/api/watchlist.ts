import { WatchlistItem, WatchlistResponse } from '@/lib/types';

export async function fetchWatchlist(): Promise<WatchlistResponse> {
  const res = await fetch('/api/watchlist');
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function addTicker(symbol: string): Promise<WatchlistItem> {
  const res = await fetch('/api/watchlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string; error?: string }).detail || (err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function deleteTicker(symbol: string): Promise<void> {
  const res = await fetch(`/api/watchlist/${encodeURIComponent(symbol)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string; error?: string }).detail || (err as { error?: string }).error || `HTTP ${res.status}`);
  }
}
