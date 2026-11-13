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

export interface HoldingDetail {
  symbol: string;
  exchange: string;
  quantity: number;
  avg_buy_price: number;
  current_price?: number | null;
  market_value?: number | null;
  invested_value?: number | null;
  unrealized_pnl?: number | null;
  unrealized_pnl_pct?: number | null;
  weight_pct?: number | null;
  sector: string;
  price_source?: string | null;
}

export interface ValuationSummary {
  total_invested: number;
  current_market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  currency: string;
  holdings_count: number;
}

export interface ConcentrationMetrics {
  hhi: number;
  hhi_category: string;
  effective_n: number;
  top_holding_symbol: string;
  top_holding_weight: number;
  top_5_weight: number;
  health_score: number;
  score_breakdown?: Record<string, unknown>;
  interpretation: string;
}

export interface RiskMetrics {
  annualized_volatility?: number | null;
  beta_nifty50?: number | null;
  max_drawdown?: number | null;
  correlation_matrix?: Record<string, Record<string, number>>;
  benchmark_symbol: string;
  observations_count: number;
  coverage_ratio: number;
  start_date?: string | null;
  end_date?: string | null;
  is_historical_proxy: boolean;
  proxy_disclosure: string;
  status: string;
}

export interface FindingItem {
  category: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  title: string;
  detail: string;
  metric_value?: number | null;
}

export interface RebalanceAction {
  symbol: string;
  current_qty: number;
  target_qty: number;
  delta_qty: number;
  action: "BUY" | "SELL" | "HOLD";
  current_price: number;
  trade_value: number;
  estimated_fees: number;
  current_weight_pct: number;
  target_weight_pct: number;
  projected_weight_pct: number;
}

export interface RebalanceResponse {
  success: boolean;
  actions?: RebalanceAction[];
  total_trade_value?: number;
  total_estimated_friction?: number;
  residual_cash?: number;
  projected_total_value?: number;
  disclaimer?: string;
  error?: string;
}

export interface PortfolioResponse {
  success: boolean;
  report: string;
  timestamp: string;
  health_score?: number;
  holdings?: Record<string, number>;
  sector_weights?: Record<string, number>;
  hhi?: number;
  holdings_detail?: HoldingDetail[];
  valuation?: ValuationSummary;
  concentration?: ConcentrationMetrics;
  risk_metrics?: RiskMetrics;
  findings?: FindingItem[];
  ai_status?: string;
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
  brokerage?: number;
  stt?: number;
  exchange_charges?: number;
  gst?: number;
  stamp_duty?: number;
  slippage_paid?: number;
  all_in_friction?: number;
}

export interface ChartPoint {
  date: string;
  strategy: number;
  benchmark: number;
}

export interface CostBreakdown {
  turnover: number;
  brokerage: number;
  stt: number;
  exchange_charges: number;
  gst: number;
  sebi_charges: number;
  stamp_duty: number;
  slippage: number;
  total_costs: number;
  statutory_charges_total?: number;
  transaction_fees_total?: number;
  all_in_friction_total?: number;
}

export interface BacktestResponse {
  success: boolean;
  report: string;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number | null;
  final_value: number;
  total_return: number;
  num_trades: number;
  outperformance: number;
  profit_factor: number | null;
  profit_factor_status?: string;
  annualized_volatility?: number;
  market_exposure_pct?: number;
  assumed_risk_free_rate?: number;
  risk_free_rate_note?: string;
  total_costs?: number;
  total_slippage?: number;
  all_in_friction_total?: number;
  cost_breakdown?: CostBreakdown;
  strategy_params?: Record<string, unknown>;
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
   * POST /analyze/rebalance
   */
  async rebalancePortfolio(
    targetWeights: Record<string, number>,
    portfolio?: string,
    additionalCash: number = 0
  ): Promise<RebalanceResponse> {
    return fetchWithRetry(`${API_BASE_URL}/analyze/rebalance`, {
      method: "POST",
      body: JSON.stringify({
        target_weights: targetWeights,
        portfolio,
        additional_cash: additionalCash,
      }),
    }) as Promise<RebalanceResponse>;
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
    initialCapital: number = 100000.0,
    slippagePct: number = 0.0005,
    riskFreeRate: number = 0.065,
    strategyParams?: Record<string, unknown>
  ): Promise<BacktestResponse> {
    return fetchWithRetry(`${API_BASE_URL}/backtest`, {
      method: "POST",
      body: JSON.stringify({
        strategy,
        symbol,
        period,
        initial_capital: initialCapital,
        slippage_pct: slippagePct,
        risk_free_rate: riskFreeRate,
        strategy_params: strategyParams,
      }),
    }) as Promise<BacktestResponse>;
  },
};
