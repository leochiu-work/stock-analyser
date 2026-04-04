import { Suspense } from 'react';
import { NewsView } from '@/components/news/NewsView';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

export const metadata = { title: 'News — Stock Analyser' };

export default function NewsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Stock News</h1>
      <Suspense fallback={<LoadingSkeleton rows={6} />}>
        <NewsView />
      </Suspense>
    </div>
  );
}
