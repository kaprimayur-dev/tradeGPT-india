"use client";

import { useState, useEffect } from "react";
import { api, BacktestResponse } from "../api";

export default function QuantitativeStrategyPage() {
  const [strategy, setStrategy] = useState("SMA Crossover");
  const [ticker, setTicker] = useState("TCS");
  const [period, setPeriod] = useState("5y");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);
  const [showInputsPanel, setShowInputsPanel] = useState(false);

  const handleRunBacktest = async () => {
    if (!ticker.trim()) return;
    setIsRunning(true);
    setError(null);
    try {
      const res = await api.runBacktest(strategy, ticker, period, initialCapital);
      if (res.success) {
        setBacktestResult(res);
      } else {
        throw new Error(res.report || "Backtest execution failed.");
      }
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "An unexpected error occurred during backtesting");
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    handleRunBacktest();
    
    const handleRefresh = () => {
      handleRunBacktest();
    };
    window.addEventListener("refreshData", handleRefresh);
    return () => window.removeEventListener("refreshData", handleRefresh);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, strategy, period, initialCapital]);

  // Generate SVG path for chart data
  let strategyPath = "";
  let benchmarkPath = "";
  let chartTicks: { x: number; label: string }[] = [];
  let minPct = "Base";
  let maxPct = "+100%";
  let midPct = "+50%";

  if (backtestResult && backtestResult.chart_data && backtestResult.chart_data.length > 0) {
    const data = backtestResult.chart_data;
    const len = data.length;
    
    // Find min and max values to scale
    const stratVals = data.map(d => d.strategy);
    const benchVals = data.map(d => d.benchmark);
    const allVals = [...stratVals, ...benchVals];
    const minVal = Math.min(...allVals);
    const maxVal = Math.max(...allVals);
    const range = maxVal - minVal || 1;
    
    // Map to coordinates (800x240, active area x: 40 to 760, y: 40 to 220)
    const points = data.map((d, i) => {
      const x = 40 + (i / (len - 1)) * 720;
      const yStrat = 220 - ((d.strategy - minVal) / range) * 180;
      const yBench = 220 - ((d.benchmark - minVal) / range) * 180;
      return { x, yStrat, yBench, date: d.date };
    });
    
    strategyPath = "M " + points.map(p => `${p.x.toFixed(1)},${p.yStrat.toFixed(1)}`).join(" L ");
    benchmarkPath = "M " + points.map(p => `${p.x.toFixed(1)},${p.yBench.toFixed(1)}`).join(" L ");
    
    // Generate horizontal labels based on percentages from initial capital
    const maxPctVal = ((maxVal - initialCapital) / initialCapital) * 100;
    const minPctVal = ((minVal - initialCapital) / initialCapital) * 100;
    const midPctVal = ((minVal + range / 2 - initialCapital) / initialCapital) * 100;
    
    maxPct = `${maxPctVal >= 0 ? "+" : ""}${maxPctVal.toFixed(1)}%`;
    minPct = `${minPctVal >= 0 ? "+" : ""}${minPctVal.toFixed(1)}%`;
    midPct = `${midPctVal >= 0 ? "+" : ""}${midPctVal.toFixed(1)}%`;

    // Pick 5 ticks evenly distributed along the time axis
    const tickIndices = [0, Math.floor(len * 0.25), Math.floor(len * 0.5), Math.floor(len * 0.75), len - 1];
    chartTicks = tickIndices.map(idx => {
      const pt = points[idx] || points[points.length - 1];
      let dateLabel = "";
      if (pt && pt.date) {
        const dateObj = new Date(pt.date);
        dateLabel = isNaN(dateObj.getTime()) ? pt.date : dateObj.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
      }
      return {
        x: pt ? pt.x : 40,
        label: dateLabel
      };
    });
  }

  const score = backtestResult
    ? Math.round(Math.min(100, Math.max(10, backtestResult.win_rate + (backtestResult.sharpe_ratio * 15))))
    : 88;

  const handleExportCSV = () => {
    if (!backtestResult || !backtestResult.trades || backtestResult.trades.length === 0) {
      return; // Button is disabled in this state
    }
    const headers = ["Date/Time", "Side", "Asset", "Qty", "Price", "Value", "PnL (%)"];
    const csvRows = [
      headers.join(","),
      ...backtestResult.trades.map(t => [
        t.datetime,
        t.side,
        t.asset,
        t.qty,
        t.price,
        t.value.replace(/[^0-9.]/g, ""), // strip non-numeric elements from formatted string
        t.pnl
      ].join(","))
    ];
    
    const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(csvRows.join("\n"));
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `backtest_${ticker}_${strategy.replace(/\s+/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleShowInputs = () => {
    setShowInputsPanel((v) => !v);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden h-full font-body bg-canvas">
      
      {/* Config Rail (Internal Header) */}
      <div className="h-14 bg-surface-base border-b border-border-subtle flex items-center px-6 gap-4 z-10 shrink-0">
        <div className="flex items-center bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle">
          <span className="text-[10px] font-bold text-text-muted mr-2">STRATEGY</span>
          <select 
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="bg-transparent border-none p-0 text-xs font-bold text-primary focus:ring-0 cursor-pointer outline-none"
          >
            <option value="SMA Crossover">SMA Crossover</option>
            <option value="Mean Reversion">Mean Reversion</option>
            <option value="MACD Breakout">MACD Breakout</option>
          </select>
        </div>

        <div className="flex items-center bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle">
          <span className="text-[10px] font-bold text-text-muted mr-2">TICKER</span>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="bg-transparent border-none p-0 text-xs font-mono font-bold text-text-primary focus:ring-0 outline-none w-14 uppercase"
            placeholder="INFY"
          />
        </div>

        <div className="flex items-center bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle">
          <span className="text-[10px] font-bold text-text-muted mr-2">PERIOD</span>
          <select 
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-transparent border-none p-0 text-xs font-bold text-text-primary focus:ring-0 cursor-pointer outline-none font-mono"
          >
            <option value="1y">1 Year</option>
            <option value="2y">2 Years</option>
            <option value="5y">5 Years (Default)</option>
          </select>
        </div>

        <div className="flex items-center bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle">
          <span className="text-[10px] font-bold text-text-muted mr-2">CAPITAL</span>
          <input 
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
            className="bg-transparent border-none p-0 text-xs font-bold text-text-primary focus:ring-0 outline-none w-24 font-mono"
          />
        </div>

        <div className="h-6 w-px bg-border-subtle mx-1"></div>

        <button 
          onClick={handleShowInputs}
          className="flex items-center gap-1.5 px-3 py-1.5 text-text-muted hover:text-text-primary hover:bg-canvas transition-colors rounded-lg text-xs font-semibold"
        >
          <span className="material-symbols-outlined !text-[1.1rem]">tune</span>
          <span>Inputs</span>
        </button>

        <div className="ml-auto">
          <button
            onClick={handleRunBacktest}
            disabled={isRunning}
            className="bg-primary text-white px-5 py-1.5 rounded-lg text-xs font-semibold hover:bg-primary-fixed-dim transition-colors active-press disabled:opacity-50 cursor-pointer"
          >
            {isRunning ? "Running Simulation..." : "Run Backtest"}
          </button>
        </div>
      </div>

      {/* Simulation Parameters Panel */}
      {showInputsPanel && (
        <div className="bg-[#f3f3fe] border-b border-[#c3c6d7] px-6 py-3 flex flex-wrap gap-6 text-xs shrink-0">
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Initial Capital</span>
            <span className="font-mono font-bold text-[#191b23]">₹{initialCapital.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Strategy</span>
            <span className="font-mono font-bold text-[#004ac6]">{strategy}</span>
          </div>
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Target Ticker</span>
            <span className="font-mono font-bold text-[#191b23]">{ticker.toUpperCase()}</span>
          </div>
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Backtest Range</span>
            <span className="font-mono font-bold text-[#191b23]">{period.toUpperCase()}</span>
          </div>
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Commission</span>
            <span className="font-mono font-bold text-[#191b23]">0.05% flat</span>
          </div>
          <div>
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider block">Slippage Model</span>
            <span className="font-mono font-bold text-[#191b23]">Flat Close ticks</span>
          </div>
        </div>
      )}

      {/* Content Canvas */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 relative">
        {/* Loading Overlay */}
        {isRunning && (
          <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center z-30 rounded-xl">
            <div className="w-10 h-10 border-4 border-[#004ac6] border-t-transparent rounded-full animate-spin mb-3"></div>
            <p className="text-xs font-bold text-[#434655] uppercase tracking-wider animate-pulse">Running Backtesting Engine...</p>
            <p className="text-[10px] text-[#737686] mt-1 font-mono">Simulating strategy triggers across historical Close ticks</p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center my-4">
            <span className="material-symbols-outlined text-[#ba1a1a] !text-4xl mb-2">warning</span>
            <h3 className="font-display font-bold text-base text-[#ba1a1a] uppercase tracking-wider">Simulation Failed</h3>
            <p className="text-xs text-[#737686] mt-2 mb-4 max-w-lg mx-auto leading-relaxed">{error}</p>
            <button
              onClick={handleRunBacktest}
              className="px-5 py-2 bg-[#ba1a1a] hover:bg-[#a61717] text-white text-xs font-bold rounded-lg transition-all active:scale-95"
            >
              Retry Simulation
            </button>
          </div>
        )}

        {!error && (
          <>
            {/* Equity Curve & Attribution Card Row */}
            <div className="grid grid-cols-12 gap-6">
              
              {/* Equity Chart Card */}
              <div className="col-span-12 lg:col-span-9 bg-white border border-[#c3c6d7] rounded-xl overflow-hidden flex flex-col shadow-sm">
                <div className="px-6 py-4 border-b border-[#c3c6d7] flex items-center justify-between">
                  <h3 className="font-display font-bold text-sm text-[#191b23]">Equity Growth (Compounded)</h3>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 bg-[#004ac6] rounded-full"></div>
                      <span className="text-[10px] font-bold text-[#737686] uppercase tracking-wider">STRATEGY</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 bg-[#505f76] rounded-full"></div>
                      <span className="text-[10px] font-bold text-[#737686] uppercase tracking-wider">BENCHMARK</span>
                    </div>
                  </div>
                </div>
                
                {/* SVG Chart curve rendering */}
                <div className="p-6 h-[320px] bg-white relative">
                  <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(#004ac6 1px, transparent 1px), linear-gradient(90deg, #004ac6 1px, transparent 1px)", backgroundSize: "40px 40px" }}></div>
                  {backtestResult && backtestResult.chart_data && backtestResult.chart_data.length > 0 ? (
                    <svg className="w-full h-full text-xs font-mono" viewBox="0 0 800 240">
                      {/* Horizontal guide grids */}
                      <line x1="40" y1="40" x2="760" y2="40" stroke="#e1e2ed" strokeDasharray="4 4" />
                      <line x1="40" y1="100" x2="760" y2="100" stroke="#e1e2ed" strokeDasharray="4 4" />
                      <line x1="40" y1="160" x2="760" y2="160" stroke="#e1e2ed" strokeDasharray="4 4" />
                      <line x1="40" y1="220" x2="760" y2="220" stroke="#c3c6d7" />

                      {/* Benchmark Line (Grey) */}
                      {benchmarkPath && (
                        <path
                          d={benchmarkPath}
                          fill="none"
                          stroke="#505f76"
                          strokeWidth="2"
                          strokeDasharray="2"
                        />
                      )}

                      {/* Strategy Line (Blue) */}
                      {strategyPath && (
                        <path
                          d={strategyPath}
                          fill="none"
                          stroke="#004ac6"
                          strokeWidth="3.5"
                        />
                      )}

                      {/* Price labels */}
                      <text x="765" y="44" fill="#737686">{maxPct}</text>
                      <text x="765" y="104" fill="#737686">{midPct}</text>
                      <text x="765" y="164" fill="#737686">{minPct}</text>
                      <text x="765" y="224" fill="#737686">Base</text>

                      {/* Date ticks */}
                      {chartTicks.map((tick, idx) => (
                        <text key={idx} x={tick.x} y="238" fill="#737686" textAnchor="middle">
                          {tick.label}
                        </text>
                      ))}
                    </svg>
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-[#737686]">
                      No historical simulation chart data available.
                    </div>
                  )}
                </div>
              </div>

              {/* Attribution & Score Panel */}
              <div className="col-span-12 lg:col-span-3 flex flex-col gap-4">
                
                {/* Performance Stats */}
                <div className="bg-white border border-[#c3c6d7] rounded-xl p-4 shadow-sm flex-1 flex flex-col justify-between">
                  <h4 className="text-[10px] font-bold text-[#737686] mb-3 flex items-center justify-between uppercase tracking-wider">
                    Attribution
                    <span className="material-symbols-outlined text-[13px] text-[#737686] cursor-pointer">info</span>
                  </h4>
                  <div className="space-y-3.5">
                    <div className="flex justify-between items-end border-b border-[#e7e7f3] pb-1.5">
                      <div>
                        <p className="text-[10px] text-[#737686]">CAGR</p>
                        <p className="text-base font-bold text-[#191b23]">
                          {backtestResult ? `${backtestResult.cagr.toFixed(1)}%` : "0.0%"}
                        </p>
                      </div>
                      <span className="text-[10px] text-[#10b981] font-bold mb-0.5">
                        {backtestResult ? `${backtestResult.outperformance.toFixed(1)}% vs Bm` : "-"}
                      </span>
                    </div>
                    <div className="flex justify-between items-end border-b border-[#e7e7f3] pb-1.5">
                      <div>
                        <p className="text-[10px] text-[#737686]">Sharpe Ratio</p>
                        <p className="text-base font-bold text-[#191b23]">
                          {backtestResult ? backtestResult.sharpe_ratio.toFixed(2) : "0.00"}
                        </p>
                      </div>
                      <span className="text-[10px] text-[#10b981] font-bold mb-0.5">
                        {backtestResult && backtestResult.sharpe_ratio > 1.5 ? "Excellent" : backtestResult && backtestResult.sharpe_ratio > 1.0 ? "Good" : "Moderate"}
                      </span>
                    </div>
                    <div className="flex justify-between items-end border-b border-[#e7e7f3] pb-1.5">
                      <div>
                        <p className="text-[10px] text-[#737686]">Max Drawdown</p>
                        <p className="text-base font-bold text-[#ba1a1a]">
                          {backtestResult ? `${backtestResult.max_drawdown.toFixed(1)}%` : "0.0%"}
                        </p>
                      </div>
                      <span className="text-[10px] text-[#737686] font-semibold mb-0.5">Peak Drawdown</span>
                    </div>
                    <div className="flex justify-between items-end">
                      <div>
                        <p className="text-[10px] text-[#737686]">Win Rate</p>
                        <p className="text-base font-bold text-[#191b23]">
                          {backtestResult ? `${backtestResult.win_rate.toFixed(1)}%` : "0.0%"}
                        </p>
                      </div>
                      <div className="w-16 h-1 bg-[#e7e7f3] rounded-full overflow-hidden mb-1.5">
                        <div 
                          className="h-full bg-[#004ac6]" 
                          style={{ width: `${backtestResult ? backtestResult.win_rate : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Score Block */}
                <div className="bg-[#004ac6] text-white rounded-xl p-4 shadow-sm">
                  <p className="text-[9px] font-bold opacity-80 tracking-wider">STRATEGY SCORE</p>
                  <div className="flex items-baseline gap-1 mt-1.5">
                    <span className="text-3xl font-display font-bold">{score}</span>
                    <span className="text-xs opacity-80">/ 100</span>
                  </div>
                  <p className="text-[11px] leading-snug mt-2 opacity-90">
                    {backtestResult && backtestResult.sharpe_ratio > 1.2 
                      ? "This strategy exhibits robust risk-adjusted returns during historical volatility windows."
                      : "This strategy displays standard performance parameters inside high-beta asset distributions."}
                  </p>
                </div>
              </div>
            </div>

            {/* Strategy Copilot Report Card */}
            {backtestResult?.report && (
              <div className="bg-white border border-[#c3c6d7] rounded-xl overflow-hidden shadow-sm p-6">
                <div className="flex items-center gap-2 mb-4 border-b border-[#e7e7f3] pb-3">
                  <span className="material-symbols-outlined text-[#004ac6] !text-lg">psychology</span>
                  <h3 className="font-display font-bold text-sm text-[#191b23]">Strategy Backtest Copilot Report</h3>
                </div>
                <div className="text-xs text-[#434655] leading-relaxed font-mono whitespace-pre-wrap select-text bg-[#faf8ff] p-5 border border-[#c3c6d7] rounded-lg overflow-x-auto">
                  {backtestResult.report}
                </div>
              </div>
            )}

            {/* Transaction Ledger Table */}
            <div className="bg-white border border-[#c3c6d7] rounded-xl flex flex-col overflow-hidden shadow-sm">
              <div className="px-6 py-3.5 border-b border-[#c3c6d7] flex items-center justify-between bg-[#faf8ff]">
                <div className="flex items-center gap-3">
                  <h3 className="font-display font-bold text-sm text-[#191b23]">Transaction Ledger</h3>
                  <span className="bg-[#e7e7f3] text-[#0b1c30] px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                    {backtestResult ? `${backtestResult.num_trades} TRADES` : "0 TRADES"}
                  </span>
                </div>
                <div className="flex gap-2 text-xs">
                  <button 
                    onClick={handleExportCSV}
                    disabled={!backtestResult || !backtestResult.trades || backtestResult.trades.length === 0}
                    title={!backtestResult || !backtestResult.trades || backtestResult.trades.length === 0 ? "No trade records available to export" : "Export transaction ledger as CSV"}
                    className="px-3 py-1 rounded-lg border border-[#c3c6d7] bg-white text-[#191b23] hover:bg-[#faf8ff] transition-colors font-semibold font-mono text-[10px] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white"
                  >
                    Export CSV
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full text-xs text-left border-collapse bg-white">
                  <thead className="bg-[#f8fafc] border-b border-[#c3c6d7] text-[#737686] uppercase text-[9px] font-bold">
                    <tr>
                      <th className="px-6 py-2.5">Date/Time</th>
                      <th className="px-6 py-2.5">Side</th>
                      <th className="px-6 py-2.5">Asset</th>
                      <th className="px-6 py-2.5 text-right font-mono">Qty</th>
                      <th className="px-6 py-2.5 text-right font-mono">Price</th>
                      <th className="px-6 py-2.5 text-right font-mono">Value</th>
                      <th className="px-6 py-2.5 text-right font-mono">PnL (%)</th>
                      <th className="px-6 py-2.5 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#e7e7f3] font-medium text-[#434655]">
                    {backtestResult && backtestResult.trades && backtestResult.trades.length > 0 ? (
                      backtestResult.trades.map((trade, idx) => (
                        <tr key={idx} className="hover:bg-[#faf8ff] transition-colors h-10">
                          <td className="px-6 py-2 font-mono text-[#191b23]">{trade.datetime}</td>
                          <td className="px-6 py-2">
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                              trade.side.toUpperCase() === "BUY"
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }`}>
                              {trade.side}
                            </span>
                          </td>
                          <td className="px-6 py-2 font-semibold text-[#191b23]">{trade.asset}</td>
                          <td className="px-6 py-2 text-right font-mono font-bold text-[#191b23]">{trade.qty}</td>
                          <td className="px-6 py-2 text-right font-mono">₹{trade.price.toFixed(2)}</td>
                          <td className="px-6 py-2 text-right font-mono">{trade.value}</td>
                          <td className={`px-6 py-2 text-right font-mono font-bold ${
                            trade.positive ? "text-[#10b981]" : "text-[#ba1a1a]"
                          }`}>
                            {trade.pnl}
                          </td>
                          <td className="px-6 py-2 text-center">
                            <span className={`w-1.5 h-1.5 rounded-full inline-block ${trade.positive ? "bg-[#10b981]" : "bg-[#ba1a1a]"}`}></span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={8} className="px-6 py-8 text-center text-xs text-[#737686]">
                          No transaction triggers occurred in this timeframe.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
