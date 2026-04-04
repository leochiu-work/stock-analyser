'use client';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

interface PaginationControlsProps {
  total: number;
  offset: number;
  limit: number;
  onPageChange: (offset: number) => void;
}

export function PaginationControls({ total, offset, limit, onPageChange }: PaginationControlsProps) {
  const hasPrev = offset > 0;
  const hasNext = offset + limit < total;

  if (!hasPrev && !hasNext) return null;

  return (
    <div className="flex items-center justify-between text-sm text-muted-foreground">
      <span>
        Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
      </span>
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              onClick={() => hasPrev && onPageChange(Math.max(0, offset - limit))}
              aria-disabled={!hasPrev}
              className={!hasPrev ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>
          <PaginationItem>
            <PaginationNext
              onClick={() => hasNext && onPageChange(offset + limit)}
              aria-disabled={!hasNext}
              className={!hasNext ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
}
