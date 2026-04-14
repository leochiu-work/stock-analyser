'use client';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface TickerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
}

export function TickerInput({ value, onChange, onSubmit }: TickerInputProps) {
  return (
    <div className="flex items-center gap-2">
      <Input
        placeholder="Ticker (e.g. AAPL)"
        value={value}
        onChange={(e) => onChange(e.target.value.toUpperCase())}
        onKeyDown={(e) => e.key === 'Enter' && onSubmit?.()}
        className="w-40 uppercase"
        aria-label="Stock ticker symbol"
      />
      {value && <Badge variant="secondary">{value}</Badge>}
    </div>
  );
}
