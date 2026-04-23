import { Suspense } from 'react';
import { StrategiesView } from '@/components/strategies/StrategiesView';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

export const metadata = { title: 'Strategies — Stock Analyser' };

export default function StrategiesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trading Strategies</h1>
      <Suspense fallback={<LoadingSkeleton rows={5} />}>
        <StrategiesView />
      </Suspense>
    </div>
  );
}
