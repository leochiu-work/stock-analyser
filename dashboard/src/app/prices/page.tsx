import { Suspense } from 'react';
import { PricesView } from '@/components/prices/PricesView';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

export const metadata = { title: 'Prices — Stock Analyser' };

export default function PricesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Stock Prices</h1>
      <Suspense fallback={<LoadingSkeleton rows={8} />}>
        <PricesView />
      </Suspense>
    </div>
  );
}
