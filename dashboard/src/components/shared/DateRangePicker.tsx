'use client';
import { useState } from 'react';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

interface DateRangePickerProps {
  startDate?: string;
  endDate?: string;
  onChange: (startDate: string | undefined, endDate: string | undefined) => void;
}

export function DateRangePicker({ startDate, endDate, onChange }: DateRangePickerProps) {
  const [startOpen, setStartOpen] = useState(false);
  const [endOpen, setEndOpen] = useState(false);

  const start = startDate ? new Date(startDate + 'T00:00:00') : undefined;
  const end = endDate ? new Date(endDate + 'T00:00:00') : undefined;

  const fmt = (d: Date) => d.toISOString().split('T')[0];

  return (
    <div className="flex items-center gap-2">
      <Popover open={startOpen} onOpenChange={setStartOpen}>
        <PopoverTrigger
          className={cn(
            'inline-flex h-8 w-36 items-center justify-start gap-1.5 rounded-lg border border-border bg-background px-2.5 text-sm font-normal transition-colors hover:bg-muted',
            !start && 'text-muted-foreground'
          )}
        >
          <CalendarIcon className="h-4 w-4 shrink-0" />
          {start ? format(start, 'MMM d, yyyy') : 'Start date'}
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={start}
            onSelect={(d) => {
              if (d) {
                const f = fmt(d);
                if (!end || f <= endDate!) onChange(f, endDate);
              } else {
                onChange(undefined, endDate);
              }
              setStartOpen(false);
            }}
            disabled={(d) => (end ? d > end : false)}
          />
        </PopoverContent>
      </Popover>
      <span className="text-muted-foreground text-sm">to</span>
      <Popover open={endOpen} onOpenChange={setEndOpen}>
        <PopoverTrigger
          className={cn(
            'inline-flex h-8 w-36 items-center justify-start gap-1.5 rounded-lg border border-border bg-background px-2.5 text-sm font-normal transition-colors hover:bg-muted',
            !end && 'text-muted-foreground'
          )}
        >
          <CalendarIcon className="h-4 w-4 shrink-0" />
          {end ? format(end, 'MMM d, yyyy') : 'End date'}
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={end}
            onSelect={(d) => {
              if (d) {
                const f = fmt(d);
                if (!start || f >= startDate!) onChange(startDate, f);
              } else {
                onChange(startDate, undefined);
              }
              setEndOpen(false);
            }}
            disabled={(d) => (start ? d < start : false)}
          />
        </PopoverContent>
      </Popover>
      {(startDate || endDate) && (
        <Button variant="ghost" size="sm" onClick={() => onChange(undefined, undefined)}>
          Reset
        </Button>
      )}
    </div>
  );
}
