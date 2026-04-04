'use client';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/shared/DataTable';
import { StockPriceItem } from '@/lib/types';
import { formatDate, formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

const columns: ColumnDef<StockPriceItem>[] = [
  {
    accessorKey: 'date',
    header: 'Date',
    cell: ({ getValue }) => formatDate(getValue<string>()),
  },
  {
    accessorKey: 'open',
    header: 'Open',
    cell: ({ getValue }) => formatCurrency(getValue<number>()),
  },
  {
    accessorKey: 'high',
    header: 'High',
    cell: ({ getValue }) => formatCurrency(getValue<number>()),
  },
  {
    accessorKey: 'low',
    header: 'Low',
    cell: ({ getValue }) => formatCurrency(getValue<number>()),
  },
  {
    accessorKey: 'close',
    header: 'Close',
    cell: ({ row }) => {
      const close = row.original.close;
      const open = row.original.open;
      const isUp = close >= open;
      return (
        <span className={cn('font-medium', isUp ? 'text-green-600' : 'text-red-600')}>
          {formatCurrency(close)}
        </span>
      );
    },
  },
];

interface PriceTableProps {
  data: StockPriceItem[];
  isLoading?: boolean;
}

export function PriceTable({ data, isLoading }: PriceTableProps) {
  return <DataTable columns={columns} data={data} isLoading={isLoading} />;
}
