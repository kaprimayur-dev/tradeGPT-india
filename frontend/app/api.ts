const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Reusable fetch wrapper with automatic retry support and exponential backoff.
 */
async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 3, delay = 1000): Promise<unknown> {
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMessage = `HTTP error! status: ${res.status}`;
      try {
        const errorJson = await res.json() as { detail?: string };
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        try {
          const errorText = await res.text();
          errorMessage = errorText || errorMessage;
        } catch {/* ignore secondary parse errors */}
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (error: unknown) {
    const err = error as Error;
    if (retries > 0) {
      console.warn(`Fetch to ${url} failed: ${err.message}. Retrying in ${delay}ms... (${retries} retries left)`);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    throw error;
  }
}

export interface IndexTicker {
  price: number;
  change: number;
  sparkline?: number[];
}

export interface SectorItem {
  name: string;
  weight: number;
  change: number;
}

export interface NewsArticle {
  title: string;
  publisher: string;
  date: string;
  link: string;
  summary: string;
}

export interface CandleItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDataResponse {
  success: boolean;
  indices: Record<string, IndexTicker>;
  breadth: { advancing: number; declining: number; unchanged?: number };
  sectors: SectorItem[];
  news: NewsArticle[];
  timestamp: string;
  history?: Record<string, CandleItem[]>;
  watchlist?: Record<string, IndexTicker>;
}

export interface PortfolioResponse {
  success: boolean;
  report: string;
  timestamp: string;
  health_score?: number;
  holdings?: Record<string, number>;
  sector_weights?: Record<string, number>;
  hhi?: number;
}

export interface GrowthDriver {
  title: string;
  icon: string;
  desc: string;
}

export interface RiskMatrixItem {
  factor: string;
  impact: string;
  prob: string;
  score: number;
}

export interface TechnicalMetrics {
  rsi: number;
  sma_50: number;
  sma_200: number;
  volume: string;
  vwap: number;
}

export interface OwnershipStructure {
  promoter: number;
  fii: number;
  dii: number;
  public: number;
}

export interface CitationBadge {
  title: string;
  meta: string;
}

export interface ResearchResponse {
  success: boolean;
  symbol: string;
  ticker: string;
  price: number;
  change: number;
  mkt_cap: string;
  pe_ratio: number;
  beta: number;
  recommendation: string;
  target_price: number;
  upside: number;
  report: string;
  growth_drivers: GrowthDriver[];
  risk_matrix: RiskMatrixItem[];
  technical_metrics: TechnicalMetrics;
  citations: CitationBadge[];
  ownership: OwnershipStructure;
  timestamp: string;
}

export interface TradeItem {
  datetime: string;
  side: string;
  asset: string;
  qty: number;
  price: number;
  value: string;
  pnl: string;
  positive: boolean;
}

export interface ChartPoint {
  date: string;
  strategy: number;
  benchmark: number;
}

export interface BacktestResponse {
  success: boolean;
  report: string;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  final_value: number;
  total_return: number;
  num_trades: number;
  outperformance: number;
  trades: TradeItem[];
  chart_data: ChartPoint[];
  timestamp: string;
}

export const api = {
  async getMarketData(interval?: string, period?: string, watchlist?: string[]): Promise<MarketDataResponse> {
    const query = new URLSearchParams();
    if (interval) query.append("interval", interval);
    if (period) query.append("period", period);
    if (watchlist && watchlist.length > 0) query.append("watchlist", watchlist.join(","));
    const url = `${API_BASE_URL}/market-data` + (query.toString() ? `?${query.toString()}` : "");
    return fetchWithRetry(url, { method: "GET" }) as Promise<MarketDataResponse>;
  },

  /**
   * POST /analyze
   */
  async analyzePortfolio(portfolio: string): Promise<PortfolioResponse> {
    return fetchWithRetry(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body: JSON.stringify({ portfolio }),
    }) as Promise<PortfolioResponse>;
  },

  /**
   * POST /research
   */
  async getStockResearch(symbol: string): Promise<ResearchResponse> {
    return fetchWithRetry(`${API_BASE_URL}/research`, {
      method: "POST",
      body: JSON.stringify({ symbol }),
    }) as Promise<ResearchResponse>;
  },

  /**
   * POST /backtest
   */
  async runBacktest(
    strategy: string,
    symbol: string,
    period: string = "5y",
    initialCapital: number = 100000.0
  ): Promise<BacktestResponse> {
    return fetchWithRetry(`${API_BASE_URL}/backtest`, {
      method: "POST",
      body: JSON.stringify({
        strategy,
        symbol,
        period,
        initial_capital: initialCapital,
      }),
    }) as Promise<BacktestResponse>;
  },
};
