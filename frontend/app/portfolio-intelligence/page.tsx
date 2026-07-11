"use client";

import { useEffect, useState } from "react";
import { api, PortfolioResponse } from "../api";

// Color palette for sector bars
const SECTOR_COLORS = [
  "#004ac6", "#505f76", "#bc4800", "#10b981", "#737686",
  "#0b5394", "#6c3483", "#1a5276", "#784212", "#1b4332",
];

export default function PortfolioIntelligencePage() {
  const [animateWidth, setAnimateWidth] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);

  const [portfolioInput, setPortfolioInput] = useState("TCS 60\nInfosys 40");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PortfolioResponse | null>(null);

  // Derived display values from API response
  const healthScore = result?.health_score ?? null;
  const holdings = result?.holdings ?? null;
  const sectorWeights = result?.sector_weights ?? null;
  const hhi = result?.hhi ?? null;
  const report = result?.report ?? null;
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
          setResult(JSON.parse(savedResult));
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
  }, [portfolioInput]);

  const handleRunAnalysis = async () => {
    const trimmed = portfolioInput.trim();
    if (!trimmed) {
      setError("Please enter at least one stock allocation (e.g. TCS 60).");
      return;
    }
    // Validate lines: each must be "SYMBOL NUMBER" format
    const lines = trimmed.split("\n").map(l => l.trim()).filter(Boolean);
    for (const line of lines) {
      const parts = line.split(/\s+/);
      if (parts.length < 2) {
        setError(`Invalid entry "${line}" — expected format: SYMBOL WEIGHT (e.g. TCS 60)`);
        return;
      }
      const weight = parseFloat(parts[parts.length - 1]);
      if (isNaN(weight) || weight < 0) {
        setError(`Invalid weight in "${line}" — weights must be non-negative numbers.`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    setAnimateWidth(false);

    try {
      const res = await api.analyzePortfolio(portfolioInput);
      if (res.success) {
        setResult(res);
        if (typeof window !== "undefined") {
          localStorage.setItem("trade_portfolio_result", JSON.stringify(res));
          localStorage.setItem("trade_portfolio_input", portfolioInput);
          if (res.health_score !== undefined) {
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

  // Derive top holdings list for the Alpha Drivers table
  const topHoldings = holdings
    ? Object.entries(holdings)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
    : null;

  // Derive sector list for bars
  const sectorList = sectorWeights
    ? Object.entries(sectorWeights).sort((a, b) => b[1] - a[1])
    : null;

  // HHI risk label
  const hhiLabel = hhi
    ? hhi > 2500 ? "High Concentration" : hhi > 1500 ? "Moderate" : "Well Diversified"
    : null;

  // Health score color
  const scoreColor = healthScore !== null
    ? healthScore >= 75 ? "#10b981" : healthScore >= 50 ? "#bc4800" : "#ba1a1a"
    : "#004ac6";

  return (
    <div className="flex-1 bg-canvas py-6 px-6 font-body overflow-auto">
      <div className="max-w-7xl mx-auto">

        {/* Header Section */}
        <div className="flex justify-between items-end mb-6 border-b border-border-subtle pb-6">
          <div>
            <h1 className="font-display font-bold text-2xl text-text-primary mb-1 tracking-tight">
              Portfolio Intelligence Report
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
                EQUITY RESEARCH
              </span>
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
                Enter Stocks &amp; Weight/Qty (one per line)
              </label>
              <textarea
                value={portfolioInput}
                onChange={(e) => setPortfolioInput(e.target.value)}
                rows={3}
                className="w-full bg-canvas border border-border-subtle rounded-lg p-3 text-xs text-text-primary font-mono focus:border-primary outline-none resize-none"
                placeholder={"E.g.\nTCS 60\nInfosys 40\nHDFC Bank 30"}
              />
            </div>
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="px-6 py-2.5 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-fixed-dim transition-colors active-press disabled:opacity-50 shrink-0 h-10 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span className="material-symbols-outlined !text-base">biotech</span>
              <span>{loading ? "Orchestrating..." : "Diagnose Portfolio"}</span>
            </button>
          </div>
          <p className="text-[9px] text-text-muted mt-2 font-mono">
            ℹ One stock per line. Format: SYMBOL WEIGHT (e.g. TCS 60). Weights need not sum to 100.
          </p>
        </div>

        {/* ─── Empty State ─── */}
        {!result && !loading && !error && (
          <div className="bg-surface-base border border-border-subtle rounded-xl p-16 text-center shadow-sm">
            <span className="material-symbols-outlined text-border-subtle !text-5xl mb-4 block">biotech</span>
            <h3 className="font-display font-bold text-base text-text-primary mb-2">No Analysis Yet</h3>
            <p className="text-xs text-text-muted max-w-sm mx-auto leading-relaxed">
              Enter your portfolio allocations above and click <strong>Diagnose Portfolio</strong> to generate a live AI-powered intelligence report.
            </p>
          </div>
        )}

        {/* ─── Loading State ─── */}
        {loading && (
          <div className="bg-surface-base border border-border-subtle rounded-xl p-16 text-center shadow-sm">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
            <p className="text-xs font-bold text-text-muted uppercase tracking-wider animate-pulse mb-1">Orchestrating Master Copilot...</p>
            <p className="text-[10px] text-text-muted font-mono">Running Portfolio Doctor → Stock Analyzer → Macro Analyzer → RAG Query → Gemini Synthesis</p>
            <div className="mt-6 grid grid-cols-5 gap-2 max-w-xs mx-auto">
              {["Portfolio Doctor", "Stock Analyzer", "Macro Analyzer", "RAG Context", "AI Synthesis"].map((step, i) => (
                <div key={step} className="flex flex-col items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${i < 2 ? "bg-primary animate-pulse" : "bg-border-subtle"}`}></div>
                  <p className="text-[8px] text-text-muted text-center leading-tight">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── Error State ─── */}
        {error && !loading && (
          <div className="bg-alert-red/5 border border-alert-red/20 rounded-xl p-8 text-center shadow-sm">
            <span className="material-symbols-outlined text-alert-red !text-4xl mb-3 block">warning_amber</span>
            <p className="text-xs font-bold text-alert-red uppercase tracking-wider mb-2">Diagnosis Failed</p>
            <p className="text-[11px] text-text-muted mb-4 leading-relaxed max-w-md mx-auto">{error}</p>
            <button
              onClick={handleRunAnalysis}
              className="px-4 py-2 bg-alert-red hover:opacity-90 text-white text-xs font-bold rounded-lg transition-colors active-press"
            >
              Retry Diagnosis
            </button>
          </div>
        )}

        {/* ─── Results: Only shown when result is available ─── */}
        {result && !loading && (
          <>
            {/* Top Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">

              {/* Health Score */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm hover:-translate-y-0.5 hover:shadow-md transition-all duration-300">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Portfolio Health Score</span>
                <div className="flex items-baseline gap-1.5 mt-3">
                  <span className="text-3xl font-bold tracking-tighter" style={{ color: scoreColor }}>
                    {healthScore ?? "—"}
                  </span>
                  <span className="text-xs text-text-muted">/100</span>
                </div>
                <div className="w-full bg-border-subtle/30 h-1.5 rounded-full mt-4">
                  <div
                    className="h-1.5 rounded-full transition-all duration-1000"
                    style={{
                      width: animateWidth ? `${healthScore ?? 0}%` : "0%",
                      backgroundColor: scoreColor
                    }}
                  ></div>
                </div>
              </div>

              {/* HHI / Concentration */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle flex flex-col justify-between shadow-sm hover:-translate-y-0.5 hover:shadow-md transition-all duration-300">
                <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Concentration Index</span>
                <div className="mt-3">
                  <div className="text-xl font-bold text-text-primary">{hhiLabel ?? "—"}</div>
                  <div className="text-[11px] text-text-muted font-semibold mt-1 font-mono">
                    HHI: {hhi ? hhi.toFixed(0) : "—"} {hhi && hhi > 2500 ? "⚠" : hhi && hhi < 1500 ? "✓" : ""}
                  </div>
                </div>
                <div className="flex gap-1.5 mt-3">
                  <div className={`h-1.5 flex-1 rounded-full ${hhi && hhi < 2500 ? "bg-[#10b981]" : "bg-alert-red"}`}></div>
                  <div className={`h-1.5 flex-1 rounded-full ${hhi && hhi < 1500 ? "bg-[#10b981]" : "bg-border-subtle/30"}`}></div>
                  <div className={`h-1.5 flex-1 rounded-full ${hhi && hhi < 1000 ? "bg-[#10b981]" : "bg-border-subtle/30"}`}></div>
                  <div className="h-1.5 flex-1 bg-border-subtle/30 rounded-full"></div>
                </div>
              </div>

              {/* Sector Exposure */}
              <div className="bg-surface-base p-5 rounded-xl border border-border-subtle col-span-1 md:col-span-2 shadow-sm hover:-translate-y-0.5 hover:shadow-md transition-all duration-300">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[10px] font-bold text-text-muted tracking-wider uppercase">Sector Exposures</span>
                  <span className="material-symbols-outlined text-primary !text-base">pie_chart</span>
                </div>
                {sectorList && sectorList.length > 0 ? (
                  <div className="space-y-2">
                    {sectorList.slice(0, 4).map(([sector, weight], idx) => (
                      <div key={sector} className="flex items-center gap-3">
                        <span className="text-xs font-semibold text-text-primary w-28 truncate">{sector}</span>
                        <div className="flex-1 bg-border-subtle/30 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all duration-1000"
                            style={{
                              width: animateWidth ? `${Math.min(100, weight)}%` : "0%",
                              backgroundColor: SECTOR_COLORS[idx % SECTOR_COLORS.length]
                            }}
                          ></div>
                        </div>
                        <span className="text-xs font-mono font-bold text-text-muted w-10 text-right shrink-0">
                          {weight.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">Sector data loading...</p>
                )}
              </div>
            </div>

            {/* Main Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

              {/* Left: AI Report */}
              <div className="lg:col-span-2 bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm">
                <div className="bg-canvas px-6 py-5 border-b border-border-subtle">
                  <h2 className="font-display font-bold text-base text-text-primary">
                    Executive Intelligence Summary
                  </h2>
                  <p className="text-xs text-text-muted mt-1">
                    AI-generated analysis based on your portfolio: {Object.keys(holdings ?? {}).join(", ")}
                  </p>
                </div>

                <div className="p-6 min-h-[350px]">
                  {report ? (
                    <div className="whitespace-pre-wrap text-xs text-text-primary leading-relaxed font-mono bg-canvas p-5 border border-border-subtle rounded-lg overflow-x-auto select-text max-h-[600px] overflow-y-auto custom-scrollbar">
                      {report}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted">No report data available.</p>
                  )}
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-6">

                {/* Holdings Table */}
                <div className="bg-surface-base rounded-xl border border-border-subtle overflow-hidden shadow-sm">
                  <div className="px-5 py-3 border-b border-border-subtle bg-canvas">
                    <span className="text-[10px] font-bold text-text-primary uppercase tracking-wider">
                      Portfolio Holdings
                    </span>
                  </div>
                  <table className="w-full text-xs text-left">
                    <thead className="bg-canvas border-b border-border-subtle text-text-muted uppercase text-[9px] font-bold">
                      <tr>
                        <th className="px-4 py-2.5">Ticker</th>
                        <th className="px-4 py-2.5 text-right font-mono">Weight</th>
                        <th className="px-4 py-2.5 text-right">Concentration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle/30 font-medium text-text-primary">
                      {topHoldings && topHoldings.length > 0 ? (
                        topHoldings.map(([symbol, weight]) => {
                          const isHigh = weight > 40;
                          const isMed = weight > 20 && !isHigh;
                          return (
                            <tr key={symbol} className="hover:bg-canvas transition-colors">
                              <td className="px-4 py-3 font-semibold">{symbol}</td>
                              <td className="px-4 py-3 text-right font-mono font-bold">
                                {weight.toFixed(1)}%
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                                  isHigh ? "bg-alert-red/10 text-alert-red" :
                                  isMed ? "bg-alert-amber/10 text-alert-amber" :
                                  "bg-[#10b981]/10 text-[#10b981]"
                                }`}>
                                  {isHigh ? "HIGH" : isMed ? "MED" : "LOW"}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={3} className="px-4 py-6 text-center text-text-muted text-[10px]">
                            Holdings data not available
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Stress Exposure — derived from HHI */}
                <div className="bg-surface-base p-5 rounded-xl border border-border-subtle shadow-sm">
                  <h4 className="text-[10px] font-bold text-text-primary uppercase tracking-wider mb-4">
                    Concentration Risk Signals
                  </h4>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-muted font-medium">Portfolio Concentration (HHI)</span>
                        <span className={`font-bold ${hhi && hhi > 2500 ? "text-alert-red" : hhi && hhi > 1500 ? "text-alert-amber" : "text-[#10b981]"}`}>
                          {hhiLabel ?? "—"}
                        </span>
                      </div>
                      <div className="w-full h-2.5 bg-border-subtle/30 rounded-full flex overflow-hidden">
                        <div
                          className={`h-full transition-all duration-1000 ${hhi && hhi > 2500 ? "bg-alert-red" : hhi && hhi > 1500 ? "bg-alert-amber" : "bg-[#10b981]"}`}
                          style={{ width: animateWidth ? `${Math.min(100, ((hhi ?? 0) / 10000) * 100)}%` : "0%" }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-muted font-medium">Largest Single Holding</span>
                        <span className={`font-bold ${topHoldings && topHoldings[0]?.[1] > 50 ? "text-alert-red" : topHoldings && topHoldings[0]?.[1] > 30 ? "text-alert-amber" : "text-[#10b981]"}`}>
                          {topHoldings?.[0] ? `${topHoldings[0][1].toFixed(1)}%` : "—"}
                        </span>
                      </div>
                      <div className="w-full h-2.5 bg-border-subtle/30 rounded-full flex overflow-hidden">
                        <div
                          className={`h-full transition-all duration-1000 ${topHoldings && topHoldings[0]?.[1] > 50 ? "bg-alert-red" : topHoldings && topHoldings[0]?.[1] > 30 ? "bg-alert-amber" : "bg-[#10b981]"}`}
                          style={{ width: animateWidth ? `${topHoldings?.[0]?.[1] ?? 0}%` : "0%" }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-muted font-medium">Health Score</span>
                        <span className={`font-bold`} style={{ color: scoreColor }}>
                          {healthScore !== null ? `${healthScore}/100` : "—"}
                        </span>
                      </div>
                      <div className="w-full h-2.5 bg-border-subtle/30 rounded-full flex overflow-hidden">
                        <div
                          className="h-full transition-all duration-1000"
                          style={{
                            width: animateWidth ? `${healthScore ?? 0}%` : "0%",
                            backgroundColor: scoreColor
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Footer Disclaimer */}
        <footer className="mt-12 pt-6 border-t border-[#c3c6d7] text-center pb-6">
          <p className="text-[9px] text-[#737686] max-w-2xl mx-auto leading-relaxed uppercase tracking-wider">
            Confidential Report. This analysis is for informational purposes only and does not constitute investment advice.
            TradeGPT India assumes no liability for trading decisions based on this model.
            Past performance is not indicative of future results. All data subject to 15-minute terminal delay.
          </p>
        </footer>
      </div>
    </div>
  );
}
