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

export type StrategyStatus = "pending" | "running" | "completed" | "failed";

export interface StrategyItem {
  id: string;
  ticker: string;
  name: string | null;
  description: string | null;
  hypothesis: string | null;
  status: StrategyStatus;
  iterations: number;
  created_at: string;
  updated_at: string;
}

export interface BacktestResult {
  id: string;
  strategy_id: string;
  sharpe_ratio: number | null;
  total_return_pct: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  num_trades: number | null;
  backtest_start: string | null;
  backtest_end: string | null;
  ai_evaluation: string | null;
  ai_score: number | null;
  approved: boolean;
  rejection_reason: string | null;
  created_at: string;
}

export interface StrategyWithResult extends BacktestResult {}
