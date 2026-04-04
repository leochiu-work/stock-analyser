import { NewsItem } from '@/lib/types';
import { NewsCard } from './NewsCard';

interface NewsGridProps {
  items: NewsItem[];
}

export function NewsGrid({ items }: NewsGridProps) {
  if (!items.length) {
    return <p className="text-muted-foreground text-center py-8">No news articles found.</p>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {items.map((item) => (
        <NewsCard key={item.finnhub_id} item={item} />
      ))}
    </div>
  );
}
