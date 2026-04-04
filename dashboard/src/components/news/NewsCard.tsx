import Image from 'next/image';
import { ExternalLink } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { NewsItem } from '@/lib/types';
import { formatDate } from '@/lib/utils';

interface NewsCardProps {
  item: NewsItem;
}

export function NewsCard({ item }: NewsCardProps) {
  return (
    <Card className="flex flex-col h-full">
      {item.image && (
        <div className="relative h-40 w-full overflow-hidden rounded-t-lg">
          <Image
            src={item.image}
            alt={item.headline}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
          />
        </div>
      )}
      <CardHeader className="pb-2">
        <CardTitle className="text-base line-clamp-2 leading-snug">{item.headline}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        {item.summary && (
          <p className="text-sm text-muted-foreground line-clamp-3">{item.summary}</p>
        )}
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-2 pt-2">
        <div className="flex items-center gap-2 flex-wrap">
          {item.category && <Badge variant="secondary" className="text-xs">{item.category}</Badge>}
          {item.source && <span className="text-xs text-muted-foreground">{item.source}</span>}
          <span className="text-xs text-muted-foreground">{formatDate(item.published_at)}</span>
        </div>
        {item.url && (
          <Button
            variant="outline"
            size="sm"
            render={<a href={item.url} target="_blank" rel="noopener noreferrer" />}
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            Read more
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
