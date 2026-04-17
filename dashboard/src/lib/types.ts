export interface StockPriceItem {
  ticker: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface StockPriceListResponse {
  ticker: string;
  total: number;
  offset: number;
  limit: number;
  items: StockPriceItem[];
}

export interface NewsItem {
  ticker_symbol: string;
  finnhub_id: number;
  headline: string;
  summary: string | null;
  source: string | null;
  url: string | null;
  image: string | null;
  category: string | null;
  published_at: string;
}

export interface NewsListResponse {
  total: number;
  offset: number;
  limit: number;
  items: NewsItem[];
}

export interface PriceQueryParams {
  ticker: string;
  start_date?: string;
  end_date?: string;
  offset?: number;
  limit?: number;
}

export interface NewsQueryParams {
  ticker: string;
  start_date?: string;
  end_date?: string;
  offset?: number;
  limit?: number;
}

export interface WatchlistItem {
  symbol: string;
  created_at: string;
}

export interface WatchlistResponse {
  total: number;
  items: WatchlistItem[];
}
