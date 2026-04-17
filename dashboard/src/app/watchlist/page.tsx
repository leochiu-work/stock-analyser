import { Suspense } from 'react';
import { WatchlistView } from '@/components/watchlist/WatchlistView';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

export const metadata = { title: 'Watchlist — Stock Analyser' };

export default function WatchlistPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Watchlist</h1>
      <Suspense fallback={<LoadingSkeleton rows={5} />}>
        <WatchlistView />
      </Suspense>
    </div>
  );
}
