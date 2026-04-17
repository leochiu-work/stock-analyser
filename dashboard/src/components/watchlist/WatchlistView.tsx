'use client';
import { useState, KeyboardEvent } from 'react';
import { useSWRConfig } from 'swr';
import { Trash2 } from 'lucide-react';
import { useWatchlist } from '@/hooks/useWatchlist';
import { addTicker, deleteTicker } from '@/lib/api/watchlist';
import { ErrorAlert } from '@/components/shared/ErrorAlert';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { formatDate } from '@/lib/utils';

export function WatchlistView() {
  const { data, error, isLoading } = useWatchlist();
  const { mutate } = useSWRConfig();

  const [symbol, setSymbol] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [deletingSymbol, setDeletingSymbol] = useState<string | null>(null);

  async function handleAdd() {
    const trimmed = symbol.trim().toUpperCase();
    if (!trimmed) return;
    setAdding(true);
    setAddError(null);
    try {
      await addTicker(trimmed);
      setSymbol('');
      mutate('watchlist');
    } catch (err) {
      setAddError(err instanceof Error ? err.message : 'Failed to add ticker');
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(sym: string) {
    setDeletingSymbol(sym);
    try {
      await deleteTicker(sym);
      mutate('watchlist');
    } catch {
      // ignore — list will remain unchanged
    } finally {
      setDeletingSymbol(null);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleAdd();
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-2 items-start">
        <div className="flex flex-col gap-1 w-48">
          <Input
            placeholder="e.g. AAPL"
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              setAddError(null);
            }}
            onKeyDown={handleKeyDown}
            disabled={adding}
          />
          {addError && (
            <p className="text-sm text-destructive">{addError}</p>
          )}
        </div>
        <Button onClick={handleAdd} disabled={adding || !symbol.trim()}>
          {adding ? 'Adding…' : 'Add'}
        </Button>
      </div>

      {error && <ErrorAlert message={error.message} />}

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Symbol</th>
                <th className="px-4 py-3 text-left font-medium">Added</th>
                <th className="px-4 py-3 text-right font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {data?.items.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                    No tickers in watchlist. Add one above.
                  </td>
                </tr>
              ) : (
                data?.items.map((item) => (
                  <tr key={item.symbol} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="px-4 py-3 font-mono font-semibold">{item.symbol}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatDate(item.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={deletingSymbol === item.symbol}
                        onClick={() => handleDelete(item.symbol)}
                        aria-label={`Remove ${item.symbol}`}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
