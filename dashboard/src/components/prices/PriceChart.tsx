'use client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { TooltipContentProps } from 'recharts/types/component/Tooltip';
import { StockPriceItem } from '@/lib/types';
import { formatDate, formatCurrency } from '@/lib/utils';

interface PriceChartProps {
  data: StockPriceItem[];
  ticker: string;
}

function CustomTooltip({ active, payload, label }: TooltipContentProps<number, string>) {
  if (!active || !payload?.length) return null;
  const item = (payload[0] as { payload: StockPriceItem }).payload;
  return (
    <div className="rounded-lg border bg-background p-3 shadow-sm text-sm space-y-1">
      <p className="font-medium">{formatDate(String(label))}</p>
      <p>Open: {formatCurrency(item.open)}</p>
      <p>High: {formatCurrency(item.high)}</p>
      <p>Low: {formatCurrency(item.low)}</p>
      <p className="font-semibold">Close: {formatCurrency(item.close)}</p>
    </div>
  );
}

export function PriceChart({ data, ticker }: PriceChartProps) {
  if (!data.length) {
    return <p className="text-muted-foreground text-center py-8">No price data for {ticker}</p>;
  }

  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="h-72" aria-label={`Close price chart for ${ticker}`} role="img">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sorted} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={(d: string) =>
              new Date(d + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            }
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            tick={{ fontSize: 12 }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={(props) => <CustomTooltip {...(props as TooltipContentProps<number, string>)} />} />
          <Line
            type="monotone"
            dataKey="close"
            stroke="hsl(221.2 83.2% 53.3%)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
