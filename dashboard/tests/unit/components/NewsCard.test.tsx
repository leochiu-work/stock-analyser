import { render, screen } from '@testing-library/react';
import { NewsCard } from '@/components/news/NewsCard';
import { NewsItem } from '@/lib/types';

const baseItem: NewsItem = {
  ticker_symbol: 'AAPL',
  finnhub_id: 1001,
  headline: 'Apple Reports Strong Q1 Earnings',
  summary: 'Apple Inc. reported earnings above expectations for Q1.',
  source: 'Reuters',
  url: 'https://example.com/news/1',
  image: null,
  category: 'company news',
  published_at: '2024-01-15T10:00:00Z',
};

describe('NewsCard', () => {
  it('renders headline', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.getByText('Apple Reports Strong Q1 Earnings')).toBeInTheDocument();
  });

  it('renders source', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.getByText('Reuters')).toBeInTheDocument();
  });

  it('renders summary when provided', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.getByText(/reported earnings/i)).toBeInTheDocument();
  });

  it('does not render summary when null', () => {
    render(<NewsCard item={{ ...baseItem, summary: null }} />);
    expect(screen.queryByText(/reported earnings/i)).not.toBeInTheDocument();
  });

  it('renders category badge when category is provided', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.getByText('company news')).toBeInTheDocument();
  });

  it('does not render category badge when category is null', () => {
    render(<NewsCard item={{ ...baseItem, category: null }} />);
    expect(screen.queryByText('company news')).not.toBeInTheDocument();
  });

  it('renders external link with correct href', () => {
    render(<NewsCard item={baseItem} />);
    // @base-ui/react Button with render=<a href=...> keeps implicit link role
    const link = screen.getByRole('link', { name: /read more/i });
    expect(link).toHaveAttribute('href', 'https://example.com/news/1');
  });

  it('renders external link with target="_blank"', () => {
    render(<NewsCard item={baseItem} />);
    const link = screen.getByRole('link', { name: /read more/i });
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('renders external link with rel="noopener noreferrer"', () => {
    render(<NewsCard item={baseItem} />);
    const link = screen.getByRole('link', { name: /read more/i });
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('does not render Read more link when url is null', () => {
    render(<NewsCard item={{ ...baseItem, url: null }} />);
    expect(screen.queryByRole('link', { name: /read more/i })).not.toBeInTheDocument();
  });

  it('does not render image when image is null', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('renders image when image url is provided', () => {
    render(<NewsCard item={{ ...baseItem, image: 'https://example.com/img.jpg' }} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('image has correct alt text from headline', () => {
    render(<NewsCard item={{ ...baseItem, image: 'https://example.com/img.jpg' }} />);
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'Apple Reports Strong Q1 Earnings');
  });

  it('does not render source when source is null', () => {
    render(<NewsCard item={{ ...baseItem, source: null }} />);
    expect(screen.queryByText('Reuters')).not.toBeInTheDocument();
  });
});
