"use client";

import { useEffect, useState } from "react";
import { api, PortfolioResponse, RebalanceResponse } from "../api";

// Color palette for sector bars
const SECTOR_COLORS = [
  "#004ac6", "#505f76", "#bc4800", "#10b981", "#737686",
  "#0b5394", "#6c3483", "#1a5276", "#784212", "#1b4332",
];

export default function PortfolioIntelligencePage() {
  const [animateWidth, setAnimateWidth] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);

  const [portfolioInput, setPortfolioInput] = useState("TCS 50 3500\nINFY 100 1450\nRELIANCE 40 2800");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PortfolioResponse | null>(null);

  // Rebalancing Simulator State
  const [targetWeights, setTargetWeights] = useState<Record<string, number>>({});
  const [additionalCash, setAdditionalCash] = useState<number>(0);
  const [rebalanceLoading, setRebalanceLoading] = useState(false);
  const [rebalanceError, setRebalanceError] = useState<string | null>(null);
  const [rebalanceResult, setRebalanceResult] = useState<RebalanceResponse | null>(null);

  // Derived display values from API response
  const healthScore = result?.health_score ?? null;
  const holdings = result?.holdings ?? null;
  const holdingsDetail = result?.holdings_detail ?? null;
  const valuation = result?.valuation ?? null;
  const concentration = result?.concentration ?? null;
  const riskMetrics = result?.risk_metrics ?? null;
  const findings = result?.findings ?? [];
  const sectorWeights = result?.sector_weights ?? null;
  const hhi = result?.hhi ?? null;
  const report = result?.report ?? null;
  const aiStatus = result?.ai_status ?? null;
  const timestamp = result?.timestamp
    ? (() => {
        try { return new Date(result.timestamp).toLocaleString(); }
        catch { return result.timestamp; }
      })()
    : null;

  useEffect(() => {
    // Trigger bar animations after mount
    const t = setTimeout(() => setAnimateWidth(true), 100);
    return () => clearTimeout(t);
  }, [result]);

  // Load saved analysis on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedInput = localStorage.getItem("trade_portfolio_input");
      if (savedInput) setPortfolioInput(savedInput);

      const savedResult = localStorage.getItem("trade_portfolio_result");
      if (savedResult) {
        try {
          const parsed = JSON.parse(savedResult);
          setResult(parsed);
          initializeTargetWeights(parsed);
        } catch (e) {
          console.error("Failed to parse saved portfolio result", e);
        }
      }
    }

    const handleRefresh = () => {
      handleRunAnalysis();
    };
    window.addEventListener("refreshData", handleRefresh);
    return () => window.removeEventListener("refreshData", handleRefresh);
  }, []);

  const initializeTargetWeights = (res: PortfolioResponse) => {
    if (res.holdings) {
      const keys = Object.keys(res.holdings);
      const equalWeight = keys.length > 0 ? Math.round((100 / keys.length) * 10) / 10 : 0;
      const initial: Record<string, number> = {};
      keys.forEach((sym) => {
        initial[sym] = equalWeight;
      });
      setTargetWeights(initial);
    }
  };

  const handleRunAnalysis = async () => {
    const trimmed = portfolioInput.trim();
    if (!trimmed) {
      setError("Please enter at least one stock holding (e.g. TCS 60 or TCS 50 3500).");
      return;
    }

    setLoading(true);
    setError(null);
    setAnimateWidth(false);
    setRebalanceResult(null);

    try {
      const res = await api.analyzePortfolio(portfolioInput);
      if (res.success) {
        setResult(res);
        initializeTargetWeights(res);
        if (typeof window !== "undefined") {
          localStorage.setItem("trade_portfolio_result", JSON.stringify(res));
          localStorage.setItem("trade_portfolio_input", portfolioInput);
          if (res.health_score !== undefined && res.health_score !== null) {
            localStorage.setItem("trade_portfolio_health", res.health_score.toString());
          }
        }
        setTimeout(() => setAnimateWidth(true), 50);
      } else {
        throw new Error("Failed to diagnose portfolio");
      }
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "An error occurred during portfolio diagnosis");
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateRebalance = async () => {
    if (!result || Object.keys(targetWeights).length === 0) {
      setRebalanceError("No target weights configured.");
      return;
    }

    setRebalanceLoading(true);
    setRebalanceError(null);

    try {
      const res = await api.rebalancePortfolio(targetWeights, portfolioInput, additionalCash);
      if (res.success) {
        setRebalanceResult(res);
      } else {
        setRebalanceError(res.error || "Rebalancing simulation failed.");
      }
    } catch (err: unknown) {
      const e = err as Error;
      setRebalanceError(e.message || "Rebalancing simulation failed.");
    } finally {
      setRebalanceLoading(false);
    }
  };

  // Derive top holdings list
  const topHoldings = holdings
    ? Object.entries(holdings)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
    : null;

  // Derive sector list for bars
  const sectorList = sectorWeights
    ? Object.entries(sectorWeights).sort((a, b) => b[1] - a[1])
    : null;

  // HHI risk label
  const hhiLabel = concentration?.hhi_category ?? (
    hhi ? (hhi > 2500 ? "High Concentration" : hhi > 1500 ? "Moderate" : "Well Diversified") : null
  );

  // Health score color
  const scoreColor = healthScore !== null
    ? healthScore >= 75 ? "#10b981" : healthScore >= 50 ? "#bc4800" : "#ba1a1a"
    : "#004ac6";

  const targetWeightSum = Object.values(targetWeights).reduce((a, b) => a + (Number(b) || 0), 0);

  return (
    <div className="flex-1 bg-canvas py-6 px-6 font-body overflow-auto">
      <div className="max-w-7xl mx-auto">

        {/* Header Section */}
        <div className="flex justify-between items-end mb-6 border-b border-border-subtle pb-6">
          <div>
            <h1 className="font-display font-bold text-2xl text-text-primary mb-1 tracking-tight">
              Portfolio Intelligence &amp; Risk Engine
            </h1>
            <div className="flex items-center gap-4 text-text-muted text-xs">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined !text-sm">calendar_today</span>
                {timestamp ?? "Run analysis to generate report"}
              </span>
              {result && (
                <span className="flex items-center gap-1 font-mono">
                  <span className="material-symbols-outlined !text-sm">id_card</span>
                  ID: PRT-{Math.abs(portfolioInput.length * 37 + (healthScore ?? 0) * 13) % 9000 + 1000}-X
                </span>
              )}
              <span className="px-2 py-0.5 bg-secondary-container text-on-secondary-container text-[9px] font-bold rounded">
                NSE QUANTITATIVE SUITE
              </span>
              {aiStatus && (
                <span className={`px-2 py-0.5 text-[9px] font-bold rounded ${
                  aiStatus === "available"
                    ? "bg-[#10b981]/15 text-[#10b981]"
                    : "bg-alert-amber/15 text-alert-amber"
                }`}>
                  AI: {aiStatus.toUpperCase()}
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-3 no-print">
            <button
              onClick={() => {
                if (typeof window !== "undefined") {
                  navigator.clipboard.writeText(window.location.href);
                  setShareCopied(true);
                  setTimeout(() => setShareCopied(false), 2000);
                }
              }}
              className="px-4 py-2 bg-surface-base border border-border-subtle rounded-lg flex items-center gap-2 hover:bg-canvas transition-colors text-xs font-semibold text-text-primary active:scale-95 duration-100"
            >
              <span className="material-symbols-outlined !text-sm">share</span>
              {shareCopied ? <span className="text-[#10b981] font-bold">Copied!</span> : <span>Share</span>}
            </button>
            <button
              onClick={() => window.print()}
              className="px-4 py-2 bg-primary text-white rounded-lg flex items-center gap-2 hover:bg-primary-fixed-dim transition-colors text-xs font-semibold active:scale-95 duration-100"
            >
              <span className="material-symbols-outlined !text-sm">print</span> Print Report
            </button>
          </div>
        </div>

        {/* Input Panel */}
        <div className="bg-surface-base border border-border-subtle rounded-xl p-5 mb-6 shadow-sm no-print">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider mb-2">Analyze Portfolio Allocation</h3>
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <label className="text-[10px] font-bold text-text-muted uppercase block mb-1">
                Enter Holdings: &quot;SYMBOL QTY AVG_PRICE&quot; or &quot;SYMBOL WEIGHT&quot; (one per line)
              </label>
              <textarea
                value={portfolioInput}
                onChange={(e) => setPortfolioInput(e.target.value)}
                rows={3}
                className="w-full bg-canvas border border-border-subtle rounded-lg p-3 text-xs text-text-primary font-mono focus:border-primary outline-none resize-none"
                placeholder={"E.g.\nTCS 50 3500.00\nINFY 100 1450.50\nRELIANCE 40 2800.00"}
              />
            </div>
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="px-6 py-2.5 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-fixed-dim transition-colors active-press disabled:opacity-50 shrink-0 h-10 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span className="material-symbols-outlined !text-base">biotech</span>
              <span>{loading ? "Analyzing..." : "Analyze Portfolio"}</span>
            </button>
          </div>
          <p className="text-[9px] text-text-muted mt-2 font-mono">
            ℹ Accepts exact positions (e.g. &apos;TCS 50 3500.00&apos;) or percentage weights (e.g. &apos;TCS 60&apos;). Strict validation rejects negative or duplicate tickers.
          </p>
        </div>

        {/* ─── Empty State ─── */}
        {!result && !loading && !error && (
          <div className="bg-surface-base border border-border-subtle rounded-xl p-16 text-center shadow-sm">
            <span className="material-symbols-outlined text-border-subtle !text-5xl mb-4 block">biotech</span>
            <h3 className="font-display font-bold text-base text-text-primary mb-2">No Analysis Yet</h3>
            <p className="text-xs text-text-muted max-w-sm mx-auto leading-relaxed">
              Enter your portfolio holdings or weights above and click <strong>Analyze Portfolio</strong> to generate quantitative valuation, risk, and concentration analytics.
            </p>
          </div>
        )}

        {/* ─── Loading State ─── */}
        {loading && (
          <div className="bg-surface-base border border-border-subtle rounded-xl p-16 text-center shadow-sm">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
            <p className="text-xs font-bold text-text-muted uppercase tracking-wider animate-pulse mb-1">Computing Quantitative Portfolio Analytics...</p>
            <p className="text-[10px] text-text-muted font-mono">Valuation Engine → Sector Aggregator → Concentration (HHI) → Fixed-Quantity Proxy Risk → Diagnostic Findings</p>
          </div>
        )}

        {/* ─── Error State ─── */}
        {error && !loading && (
          <div className="bg-alert-red/5 border border-alert-red/20 rounded-xl p-8 text-center shadow-sm">
            <span className="material-symbols-outlined text-alert-red !text-4xl mb-3 block">warning_amber</span>
            <p className="text-xs font-bold text-alert-red uppercase tracking-wider mb-2">Analysis Failed</p>
            <p className="text-[11px] text-text-muted mb-4 leading-relaxed max-w-md mx-auto">{error}</p>
            <button
              onClick={handleRunAnalysis}
              className="px-4 py-2 bg-alert-red hover:opacity-90 text-white text-xs font-bold rounded-lg transition-colors active-press"
            >
              Retry Analysis
            </button>
          </div>
        )}

        {/* ─── Results: Only shown when result is available ─── */}
        {result && !loading && (
          <>
            {/* Row 1: Valuation & Core Portfolio Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">

              {/* Total Invested */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Invested Capital</span>
                <div className="mt-2">
                  <div className="text-2xl font-bold font-mono text-text-primary">
                    ₹{valuation ? valuation.total_invested.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : "—"}
                  </div>
                  <span className="text-[10px] text-text-muted">Holdings: {valuation?.holdings_count ?? holdingsDetail?.length ?? "—"} positions</span>
                </div>
              </div>

              {/* Current Market Value */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Market Value</span>
                <div className="mt-2">
                  <div className="text-2xl font-bold font-mono text-text-primary">
                    ₹{valuation ? valuation.current_market_value.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : "—"}
                  </div>
                  <span className="text-[10px] text-text-muted">NSE cash segment prices</span>
                </div>
              </div>

              {/* Unrealized PnL */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Unrealized PnL</span>
                <div className="mt-2">
                  <div className={`text-2xl font-bold font-mono ${
                    valuation && valuation.unrealized_pnl >= 0 ? "text-[#10b981]" : "text-alert-red"
                  }`}>
                    {valuation ? `${valuation.unrealized_pnl >= 0 ? "+" : ""}₹${valuation.unrealized_pnl.toLocaleString("en-IN", { maximumFractionDigits: 2 })}` : "—"}
                  </div>
                  <span className={`text-[10px] font-bold font-mono ${
                    valuation && valuation.unrealized_pnl_pct >= 0 ? "text-[#10b981]" : "text-alert-red"
                  }`}>
                    {valuation ? `${valuation.unrealized_pnl_pct >= 0 ? "+" : ""}${valuation.unrealized_pnl_pct.toFixed(2)}%` : "—"}
                  </span>
                </div>
              </div>

              {/* Portfolio Health Score */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Health Score</span>
                <div className="flex items-baseline gap-1.5 mt-2">
                  <span className="text-3xl font-bold tracking-tighter" style={{ color: scoreColor }}>
                    {healthScore ?? "—"}
                  </span>
                  <span className="text-xs text-text-muted">/100</span>
                </div>
                <div className="w-full bg-border-subtle/30 h-1.5 rounded-full mt-2">
                  <div
                    className="h-1.5 rounded-full transition-all duration-1000"
                    style={{
                      width: animateWidth ? `${healthScore ?? 0}%` : "0%",
                      backgroundColor: scoreColor,
                    }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Row 2: Concentration & Risk Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">

              {/* Concentration (HHI) */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase block mb-1">Concentration Index</span>
                <div className="text-lg font-bold text-text-primary">{hhiLabel ?? "—"}</div>
                <div className="text-xs font-mono font-bold text-text-muted mt-1">
                  HHI: {hhi ? hhi.toFixed(0) : "—"} {hhi && hhi > 2500 ? "⚠" : "✓"}
                </div>
                <div className="text-[10px] text-text-muted mt-2">
                  Effective Count: <strong className="font-mono text-text-primary">{concentration?.effective_n ?? "—"}</strong> stocks
                </div>
              </div>

              {/* Historical Volatility */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase block mb-1">Annualized Volatility</span>
                <div className="text-xl font-bold font-mono text-text-primary">
                  {riskMetrics?.annualized_volatility !== null && riskMetrics?.annualized_volatility !== undefined
                    ? `${riskMetrics.annualized_volatility.toFixed(1)}%`
                    : "N/A"}
                </div>
                <div className="text-[10px] text-text-muted mt-2">
                  1-Year Trading Days: <span className="font-mono">{riskMetrics?.observations_count ?? 0}</span>
                </div>
              </div>

              {/* Beta vs NIFTY 50 */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase block mb-1">Beta vs NIFTY 50</span>
                <div className="text-xl font-bold font-mono text-text-primary">
                  {riskMetrics?.beta_nifty50 !== null && riskMetrics?.beta_nifty50 !== undefined
                    ? riskMetrics.beta_nifty50.toFixed(2)
                    : "N/A"}
                </div>
                <div className="text-[10px] text-text-muted mt-2">
                  Benchmark: <span className="font-mono">^NSEI</span>
                </div>
              </div>

              {/* 1Y Max Drawdown */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase block mb-1">Historical Max Drawdown</span>
                <div className="text-xl font-bold font-mono text-alert-red">
                  {riskMetrics?.max_drawdown !== null && riskMetrics?.max_drawdown !== undefined
                    ? `${riskMetrics.max_drawdown.toFixed(1)}%`
                    : "N/A"}
                </div>
                <div className="text-[10px] text-text-muted mt-2">
                  Coverage: <span className="font-mono">{riskMetrics ? `${(riskMetrics.coverage_ratio * 100).toFixed(0)}%` : "—"}</span>
                </div>
              </div>
            </div>

            {/* Methodology Disclosure Pill */}
            {riskMetrics?.proxy_disclosure && (
              <div className="bg-canvas border border-border-subtle rounded-xl p-3 mb-6 flex items-start gap-3 text-xs text-text-muted">
                <span className="material-symbols-outlined text-primary !text-base shrink-0 mt-0.5">info</span>
                <div>
                  <strong className="text-text-primary uppercase text-[10px] tracking-wider block mb-0.5">Fixed-Quantity Historical Proxy Methodology</strong>
                  <p className="text-[11px] leading-relaxed">{riskMetrics.proxy_disclosure}</p>
                </div>
              </div>
            )}

            {/* Row 3: Sector Breakdown & Diagnostic Findings */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

              {/* Sector Breakdown */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Sector Allocation</span>
                  <span className="material-symbols-outlined text-primary !text-base">pie_chart</span>
                </div>
                {sectorList && sectorList.length > 0 ? (
                  <div className="space-y-3">
                    {sectorList.map(([sector, weight], idx) => (
                      <div key={sector} className="flex items-center gap-3">
                        <span className="text-xs font-semibold text-text-primary w-36 truncate">{sector}</span>
                        <div className="flex-1 bg-border-subtle/30 h-2 rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all duration-1000"
                            style={{
                              width: animateWidth ? `${Math.min(100, weight)}%` : "0%",
                              backgroundColor: SECTOR_COLORS[idx % SECTOR_COLORS.length],
                            }}
                          ></div>
                        </div>
                        <span className="text-xs font-mono font-bold text-text-muted w-12 text-right shrink-0">
                          {weight.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">No sector classifications available.</p>
                )}
              </div>

              {/* Diagnostic Findings */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Diagnostic Findings</span>
                    <span className="text-[10px] font-mono text-text-muted">{findings.length} findings</span>
                  </div>
                  <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
                    {findings && findings.length > 0 ? (
                      findings.map((f, i) => {
                        const isCrit = f.severity === "CRITICAL";
                        const isWarn = f.severity === "WARNING";
                        return (
                          <div
                            key={i}
                            className={`p-3 rounded-lg border text-xs ${
                              isCrit
                                ? "bg-alert-red/5 border-alert-red/20 text-alert-red"
                                : isWarn
                                ? "bg-alert-amber/5 border-alert-amber/20 text-alert-amber"
                                : "bg-primary/5 border-primary/20 text-text-primary"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold">{f.title}</span>
                              <span className="text-[9px] uppercase px-1.5 py-0.2 rounded font-mono font-bold">
                                {f.severity}
                              </span>
                            </div>
                            <p className="text-[11px] text-text-muted leading-relaxed">{f.detail}</p>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-text-muted">No adverse findings triggered.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Row 4: Detailed Holdings Table */}
            <div className="bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm mb-6">
              <div className="px-5 py-3 border-b border-border-subtle bg-canvas flex justify-between items-center">
                <span className="text-[10px] font-bold text-text-primary uppercase tracking-wider">
                  Holdings &amp; Valuation Detail
                </span>
                <span className="text-[10px] text-text-muted font-mono">
                  {holdingsDetail?.length ?? 0} holdings
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-canvas border-b border-border-subtle text-text-muted uppercase text-[9px] font-bold">
                    <tr>
                      <th className="px-4 py-2.5">Symbol</th>
                      <th className="px-4 py-2.5">Sector</th>
                      <th className="px-4 py-2.5 text-right font-mono">Qty</th>
                      <th className="px-4 py-2.5 text-right font-mono">Avg Price</th>
                      <th className="px-4 py-2.5 text-right font-mono">Current Price</th>
                      <th className="px-4 py-2.5 text-right font-mono">Market Value</th>
                      <th className="px-4 py-2.5 text-right font-mono">Unrealized PnL</th>
                      <th className="px-4 py-2.5 text-right font-mono">Weight</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle/30 font-medium text-text-primary">
                    {holdingsDetail && holdingsDetail.length > 0 ? (
                      holdingsDetail.map((h) => {
                        const pnl = h.unrealized_pnl ?? 0;
                        const pnlPct = h.unrealized_pnl_pct ?? 0;
                        const isPos = pnl >= 0;
                        return (
                          <tr key={h.symbol} className="hover:bg-canvas transition-colors">
                            <td className="px-4 py-3 font-bold font-mono">{h.symbol}</td>
                            <td className="px-4 py-3 text-text-muted truncate max-w-[150px]">{h.sector}</td>
                            <td className="px-4 py-3 text-right font-mono">{h.quantity.toLocaleString("en-IN")}</td>
                            <td className="px-4 py-3 text-right font-mono">₹{h.avg_buy_price.toFixed(2)}</td>
                            <td className="px-4 py-3 text-right font-mono">
                              {h.current_price ? `₹${h.current_price.toFixed(2)}` : "—"}
                            </td>
                            <td className="px-4 py-3 text-right font-mono font-bold">
                              ₹{(h.market_value ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                            </td>
                            <td className={`px-4 py-3 text-right font-mono font-bold ${isPos ? "text-[#10b981]" : "text-alert-red"}`}>
                              {isPos ? "+" : ""}₹{pnl.toFixed(2)} ({isPos ? "+" : ""}{pnlPct.toFixed(2)}%)
                            </td>
                            <td className="px-4 py-3 text-right font-mono font-bold">
                              {(h.weight_pct ?? 0).toFixed(1)}%
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={8} className="px-4 py-6 text-center text-text-muted text-[10px]">
                          No holdings available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Row 5: Pairwise Pearson Correlation Matrix */}
            {riskMetrics?.correlation_matrix && Object.keys(riskMetrics.correlation_matrix).length > 1 && (
              <div className="bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm mb-6 p-5">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h4 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                      Holdings Pairwise Correlation Matrix
                    </h4>
                    <p className="text-[10px] text-text-muted">
                      Pearson correlation of 1-year daily returns between portfolio assets.
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-primary !text-base">hub</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="text-xs text-center border-collapse">
                    <thead>
                      <tr>
                        <th className="p-2 border border-border-subtle bg-canvas font-bold text-[9px] uppercase">Asset</th>
                        {Object.keys(riskMetrics.correlation_matrix).map((sym) => (
                          <th key={sym} className="p-2 border border-border-subtle bg-canvas font-bold text-[9px] uppercase font-mono">
                            {sym}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(riskMetrics.correlation_matrix).map(([s1, row]) => (
                        <tr key={s1}>
                          <td className="p-2 border border-border-subtle font-bold font-mono bg-canvas text-left">{s1}</td>
                          {Object.entries(row).map(([s2, corr]) => {
                            const isSelf = s1 === s2;
                            const isHigh = corr >= 0.75 && !isSelf;
                            return (
                              <td
                                key={s2}
                                className={`p-2 border border-border-subtle font-mono text-[11px] ${
                                  isSelf
                                    ? "bg-border-subtle/10 font-bold"
                                    : isHigh
                                    ? "bg-alert-red/10 text-alert-red font-bold"
                                    : "text-text-primary"
                                }`}
                              >
                                {corr.toFixed(2)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Row 6: Interactive Rebalancing Simulator */}
            <div className="bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm mb-6 p-5">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                    Interactive Rebalancing Simulator
                  </h3>
                  <p className="text-[10px] text-text-muted">
                    Simulate integer-share portfolio reallocation and estimate statutory NSE delivery costs.
                  </p>
                </div>
                <span className="material-symbols-outlined text-primary !text-base">tune</span>
              </div>

              {/* Target weights input table */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="md:col-span-2">
                  <label className="text-[10px] font-bold text-text-muted uppercase block mb-1">
                    Target Weights (%) — Total: {targetWeightSum.toFixed(1)}% {Math.abs(targetWeightSum - 100) > 0.5 ? "⚠" : "✓"}
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {Object.keys(targetWeights).map((sym) => (
                      <div key={sym} className="flex items-center gap-1.5 bg-canvas border border-border-subtle rounded p-1.5">
                        <span className="text-[10px] font-bold font-mono w-16 truncate">{sym}</span>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max="100"
                          value={targetWeights[sym]}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            setTargetWeights((prev) => ({ ...prev, [sym]: val }));
                          }}
                          className="w-16 bg-surface-base border border-border-subtle rounded px-1.5 py-0.5 text-xs font-mono text-right outline-none"
                        />
                        <span className="text-[10px] text-text-muted">%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-text-muted uppercase block mb-1">
                    Additional Cash Injection (₹)
                  </label>
                  <input
                    type="number"
                    step="1000"
                    min="0"
                    value={additionalCash}
                    onChange={(e) => setAdditionalCash(parseFloat(e.target.value) || 0)}
                    className="w-full bg-canvas border border-border-subtle rounded p-2 text-xs font-mono text-text-primary outline-none mb-3"
                    placeholder="0"
                  />
                  <button
                    onClick={handleSimulateRebalance}
                    disabled={rebalanceLoading}
                    className="w-full py-2 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-fixed-dim transition-colors active-press disabled:opacity-50 flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <span className="material-symbols-outlined !text-sm">sync_alt</span>
                    <span>{rebalanceLoading ? "Simulating..." : "Calculate Rebalancing Trades"}</span>
                  </button>
                </div>
              </div>

              {rebalanceError && (
                <div className="p-3 bg-alert-red/5 border border-alert-red/20 rounded-lg text-alert-red text-xs mb-4">
                  {rebalanceError}
                </div>
              )}

              {/* Rebalance Output Table */}
              {rebalanceResult && rebalanceResult.actions && (
                <div className="mt-4 border-t border-border-subtle pt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="p-3 bg-canvas border border-border-subtle rounded-lg">
                      <span className="text-[9px] font-bold text-text-muted uppercase block">Total Turnover</span>
                      <span className="text-sm font-bold font-mono">
                        ₹{rebalanceResult.total_trade_value?.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="p-3 bg-canvas border border-border-subtle rounded-lg">
                      <span className="text-[9px] font-bold text-text-muted uppercase block">Estimated Friction</span>
                      <span className="text-sm font-bold font-mono text-alert-amber">
                        ₹{rebalanceResult.total_estimated_friction?.toFixed(2)}
                      </span>
                    </div>
                    <div className="p-3 bg-canvas border border-border-subtle rounded-lg">
                      <span className="text-[9px] font-bold text-text-muted uppercase block">Residual Cash</span>
                      <span className="text-sm font-bold font-mono text-text-primary">
                        ₹{rebalanceResult.residual_cash?.toFixed(2)}
                      </span>
                    </div>
                    <div className="p-3 bg-canvas border border-border-subtle rounded-lg">
                      <span className="text-[9px] font-bold text-text-muted uppercase block">Projected Total Value</span>
                      <span className="text-sm font-bold font-mono text-primary">
                        ₹{rebalanceResult.projected_total_value?.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-canvas border-b border-border-subtle text-text-muted uppercase text-[9px] font-bold">
                        <tr>
                          <th className="px-3 py-2">Symbol</th>
                          <th className="px-3 py-2 text-center">Action</th>
                          <th className="px-3 py-2 text-right font-mono">Current Qty</th>
                          <th className="px-3 py-2 text-right font-mono">Target Qty</th>
                          <th className="px-3 py-2 text-right font-mono">Trade Qty</th>
                          <th className="px-3 py-2 text-right font-mono">Price</th>
                          <th className="px-3 py-2 text-right font-mono">Turnover</th>
                          <th className="px-3 py-2 text-right font-mono">Est. Fees</th>
                          <th className="px-3 py-2 text-right font-mono">Target Wt</th>
                          <th className="px-3 py-2 text-right font-mono">Achieved Wt</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle/30 font-medium">
                        {rebalanceResult.actions.map((act) => {
                          const isBuy = act.action === "BUY";
                          const isSell = act.action === "SELL";
                          return (
                            <tr key={act.symbol} className="hover:bg-canvas transition-colors">
                              <td className="px-3 py-2.5 font-bold font-mono">{act.symbol}</td>
                              <td className="px-3 py-2.5 text-center">
                                <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                                  isBuy ? "bg-[#10b981]/15 text-[#10b981]" :
                                  isSell ? "bg-alert-red/15 text-alert-red" :
                                  "bg-border-subtle/20 text-text-muted"
                                }`}>
                                  {act.action}
                                </span>
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono">{act.current_qty}</td>
                              <td className="px-3 py-2.5 text-right font-mono font-bold">{act.target_qty}</td>
                              <td className="px-3 py-2.5 text-right font-mono">{Math.abs(act.delta_qty)}</td>
                              <td className="px-3 py-2.5 text-right font-mono">₹{act.current_price.toFixed(2)}</td>
                              <td className="px-3 py-2.5 text-right font-mono">₹{act.trade_value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</td>
                              <td className="px-3 py-2.5 text-right font-mono text-alert-amber">₹{act.estimated_fees.toFixed(2)}</td>
                              <td className="px-3 py-2.5 text-right font-mono">{act.target_weight_pct.toFixed(1)}%</td>
                              <td className="px-3 py-2.5 text-right font-mono font-bold">{act.projected_weight_pct.toFixed(1)}%</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {rebalanceResult.disclaimer && (
                    <p className="text-[9px] text-text-muted mt-3 font-mono">
                      ℹ {rebalanceResult.disclaimer}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Row 7: Executive Intelligence Report */}
            <div className="bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm mb-6">
              <div className="bg-canvas px-6 py-4 border-b border-border-subtle flex justify-between items-center">
                <div>
                  <h2 className="font-display font-bold text-base text-text-primary">
                    Executive Intelligence Summary
                  </h2>
                  <p className="text-xs text-text-muted mt-0.5">
                    Portfolio Report for: {Object.keys(holdings ?? {}).join(", ")}
                  </p>
                </div>
                <span className="text-[10px] font-mono text-text-muted">
                  {aiStatus === "available" ? "Gemini 1.5 Pro" : "Deterministic Engine"}
                </span>
              </div>

              <div className="p-6 min-h-[250px]">
                {report ? (
                  <div className="whitespace-pre-wrap text-xs text-text-primary leading-relaxed font-mono bg-canvas p-5 border border-border-subtle rounded-lg overflow-x-auto select-text max-h-[600px] overflow-y-auto custom-scrollbar">
                    {report}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">No report data available.</p>
                )}
              </div>
            </div>
          </>
        )}

        {/* Footer Disclaimer */}
        <footer className="mt-12 pt-6 border-t border-[#c3c6d7] text-center pb-6">
          <p className="text-[9px] text-[#737686] max-w-2xl mx-auto leading-relaxed uppercase tracking-wider">
            Confidential Report. This analysis is for educational and analytical purposes only and does not constitute investment advice or a SEBI-regulated recommendation.
            TradeGPT India assumes no liability for trading decisions based on this model.
            Past performance is not indicative of future results. All market data subject to 15-minute terminal delay.
          </p>
        </footer>
      </div>
    </div>
  );
}
