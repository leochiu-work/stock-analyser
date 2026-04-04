'use client';
import { TickerInput } from '@/components/shared/TickerInput';
import { DateRangePicker } from '@/components/shared/DateRangePicker';

interface PriceFiltersProps {
  ticker: string;
  startDate?: string;
  endDate?: string;
  onTickerChange: (ticker: string) => void;
  onDateChange: (start?: string, end?: string) => void;
}

export function PriceFilters({ ticker, startDate, endDate, onTickerChange, onDateChange }: PriceFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4">
      <TickerInput value={ticker} onChange={onTickerChange} />
      <DateRangePicker startDate={startDate} endDate={endDate} onChange={onDateChange} />
    </div>
  );
}
