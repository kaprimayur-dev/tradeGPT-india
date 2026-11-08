export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Reusable fetch wrapper with strict truthfulness & retry policy:
 * - Never retries 4xx client errors (400, 401, 403, 404, 422).
 * - Never retries 503 Service Unavailable by default.
 * - Never retries non-idempotent requests (POST, PUT, DELETE, PATCH).
 * - Retries at most 2 times only on idempotent GET requests experiencing transient 502/504 or network failures.
 */
async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 2, delay = 1000): Promise<unknown> {
  const method = (options.method || "GET").toUpperCase();
  const isIdempotent = method === "GET" || method === "HEAD";

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
      let errorData: unknown;
      try {
        const errorJson = (await res.json()) as { detail?: string };
        errorMessage = errorJson.detail || errorMessage;
        errorData = errorJson;
      } catch {
        try {
          const errorText = await res.text();
          errorMessage = errorText || errorMessage;
        } catch {/* ignore secondary parse errors */}
      }

      const apiErr = new ApiError(errorMessage, res.status, errorData);

      // Do NOT retry 4xx errors, 503 service unavailable, or non-idempotent operations
      const isRetryableStatus = res.status === 502 || res.status === 504;
      if (isIdempotent && isRetryableStatus && retries > 0) {
        console.warn(`Idempotent ${method} to ${url} failed with status ${res.status}. Retrying in ${delay}ms... (${retries} retries left)`);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return fetchWithRetry(url, options, retries - 1, delay * 1.5);
      }

      throw apiErr;
    }

    return await res.json();
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network / connection drop errors
    const err = error as Error;
    if (isIdempotent && retries > 0) {
      console.warn(`Network failure on ${method} to ${url}: ${err.message}. Retrying in ${delay}ms... (${retries} retries left)`);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    throw error;
  }
}

export type DataIntegrityStatus = "available" | "degraded" | "unavailable";

export interface IndexTicker {
  price?: number | null;
  change?: number | null;
  sparkline?: number[];
  status?: DataIntegrityStatus;
}

export interface SectorItem {
  name: string;
  weight: number;
  change?: number | null;
  status?: DataIntegrityStatus;
}

export interface BreadthData {
  advancing?: number | null;
  declining?: number | null;
  unchanged?: number | null;
  status?: DataIntegrityStatus;
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
  status?: DataIntegrityStatus;
  source?: string;
  as_of?: string | null;
  indices: Record<string, IndexTicker>;
  breadth: BreadthData;
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
  rsi?: number | null;
  sma_50?: number | null;
  sma_200?: number | null;
  volume?: string | null;
  vwap?: number | null;
}

export interface OwnershipStructure {
  promoter?: number | null;
  fii?: number | null;
  dii?: number | null;
  public?: number | null;
  status?: DataIntegrityStatus;
}

export interface CitationBadge {
  title: string;
  meta: string;
}

export interface ResearchResponse {
  success: boolean;
  status?: DataIntegrityStatus;
  source?: string;
  as_of?: string | null;
  symbol: string;
  ticker: string;
  price?: number | null;
  change?: number | null;
  mkt_cap?: string | null;
  pe_ratio?: number | null;
  beta?: number | null;
  recommendation?: string | null;
  target_price?: number | null;
  upside?: number | null;
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
