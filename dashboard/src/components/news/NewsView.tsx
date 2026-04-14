'use client';
import { useSearchParams, useRouter } from 'next/navigation';
import { useCallback } from 'react';
import { useNews } from '@/hooks/useNews';
import { NewsFilters } from './NewsFilters';
import { NewsGrid } from './NewsGrid';
import { PaginationControls } from '@/components/shared/PaginationControls';
import { ErrorAlert } from '@/components/shared/ErrorAlert';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { DEFAULT_TICKER, PAGE_SIZE } from '@/lib/constants';
import { getDefaultStartDate, getDefaultEndDate } from '@/lib/utils';

export function NewsView() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const ticker = searchParams.get('ticker') || DEFAULT_TICKER;
  const startDate = searchParams.get('start') || getDefaultStartDate();
  const endDate = searchParams.get('end') || getDefaultEndDate();
  const offset = parseInt(searchParams.get('offset') || '0', 10);

  const updateParams = useCallback(
    (updates: Record<string, string | undefined>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([k, v]) => {
        if (v === undefined) params.delete(k);
        else params.set(k, v);
      });
      if (!('offset' in updates)) params.set('offset', '0');
      router.replace(`?${params.toString()}`);
    },
    [router, searchParams]
  );

  const { data, error, isLoading } = useNews({
    ticker,
    start_date: startDate,
    end_date: endDate,
    offset,
    limit: PAGE_SIZE,
  });

  return (
    <div className="space-y-6">
      <NewsFilters
        ticker={ticker}
        startDate={startDate}
        endDate={endDate}
        onTickerChange={(t) => updateParams({ ticker: t })}
        onDateChange={(s, e) => updateParams({ start: s, end: e })}
      />
      {error && <ErrorAlert message={error.message} />}
      {isLoading && !error && <LoadingSkeleton rows={6} />}
      {!error && !isLoading && (
        <>
          <NewsGrid items={data?.items ?? []} />
          {data && (
            <PaginationControls
              total={data.total}
              offset={offset}
              limit={PAGE_SIZE}
              onPageChange={(o) => updateParams({ offset: String(o) })}
            />
          )}
        </>
      )}
    </div>
  );
}
