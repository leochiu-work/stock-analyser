import { StrategyItem, StrategyWithResult } from '@/lib/types';

export async function fetchStrategies(params: {
  ticker?: string;
  status?: string;
} = {}): Promise<StrategyItem[]> {
  const searchParams = new URLSearchParams();
  if (params.ticker) searchParams.set('ticker', params.ticker);
  if (params.status) searchParams.set('status', params.status);

  const res = await fetch(`/api/strategies?${searchParams.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function createStrategy(ticker: string): Promise<StrategyItem> {
  const res = await fetch('/api/strategies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchStrategyById(id: string): Promise<StrategyWithResult> {
  const res = await fetch(`/api/strategies/${id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function deleteStrategy(id: string): Promise<void> {
  const res = await fetch(`/api/strategies/${id}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || `HTTP ${res.status}`);
  }
}
