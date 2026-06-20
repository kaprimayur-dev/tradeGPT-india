"use client";

import { useState } from "react";

export default function QuantitativeStrategyPage() {
  const [strategy, setStrategy] = useState("SMA Crossover (v2.1)");
  const [ticker, setTicker] = useState("AAPL.US");
  const [dateRange, setDateRange] = useState("2023-01-01 – 2023-12-31");
  const [isRunning, setIsRunning] = useState(false);

  const handleRunBacktest = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      alert("Backtest completed successfully!");
    }, 1500);
  };

  const ledgerTrades = [
    { datetime: "2023-12-14 10:30", side: "Buy", asset: "AAPL.US", qty: 150, price: 194.20, value: "29,130.00", pnl: "+1.45%", positive: true },
    { datetime: "2023-12-12 14:15", side: "Sell", asset: "AAPL.US", qty: 200, price: 192.45, value: "38,490.00", pnl: "-0.22%", positive: false },
    { datetime: "2023-12-10 09:45", side: "Buy", asset: "AAPL.US", qty: 100, price: 195.10, value: "19,510.00", pnl: "+2.10%", positive: true },
    { datetime: "2023-12-08 11:20", side: "Sell", asset: "AAPL.US", qty: 50, price: 197.80, value: "9,890.00", pnl: "+0.85%", positive: true },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden h-[calc(100vh-3.5rem)] font-body select-none">
      
      {/* Config Rail (Internal Header) */}
      <div className="h-14 bg-white border-b border-[#c3c6d7] flex items-center px-6 gap-4 z-10 shrink-0">
        <div className="flex items-center bg-[#f3f3fe] px-3 py-1.5 rounded-lg border border-[#c3c6d7]">
          <span className="text-[10px] font-bold text-[#737686] mr-2">STRATEGY</span>
          <select 
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="bg-transparent border-none p-0 text-xs font-bold text-[#004ac6] focus:ring-0 cursor-pointer outline-none"
          >
            <option value="SMA Crossover (v2.1)">SMA Crossover (v2.1)</option>
            <option value="RSI Mean Reversion">RSI Mean Reversion</option>
            <option value="Bollinger Breakout">Bollinger Breakout</option>
          </select>
        </div>

        <div className="flex items-center bg-[#f3f3fe] px-3 py-1.5 rounded-lg border border-[#c3c6d7]">
          <span className="text-[10px] font-bold text-[#737686] mr-2">TICKER</span>
          <span className="text-xs font-bold text-[#191b23]">{ticker}</span>
        </div>

        <div className="flex items-center bg-[#f3f3fe] px-3 py-1.5 rounded-lg border border-[#c3c6d7]">
          <span className="text-[10px] font-bold text-[#737686] mr-2">RANGE</span>
          <span className="text-xs font-bold text-[#191b23]">{dateRange}</span>
        </div>

        <div className="h-6 w-px bg-[#c3c6d7] mx-1"></div>

        <button 
          onClick={() => alert("Configure model parameter boundaries.")}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[#434655] hover:text-[#191b23] hover:bg-[#f3f3fe] transition-colors rounded-lg text-xs font-semibold"
        >
          <span className="material-symbols-outlined !text-[1.1rem]">tune</span>
          <span>Inputs</span>
        </button>

        <div className="ml-auto">
          <button
            onClick={handleRunBacktest}
            disabled={isRunning}
            className="bg-[#004ac6] text-white px-5 py-1.5 rounded-lg text-xs font-semibold hover:bg-[#003ea8] transition-colors active:scale-95 duration-100 disabled:opacity-50"
          >
            {isRunning ? "Running..." : "Run Backtest"}
          </button>
        </div>
      </div>

      {/* Content Canvas */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
        
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
                  <span className="text-[10px] font-bold text-[#737686] uppercase tracking-wider">BENCHMARK (S&amp;P 500)</span>
                </div>
              </div>
            </div>
            
            {/* SVG Chart curve rendering */}
            <div className="p-6 h-[320px] bg-white relative">
              <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(#004ac6 1px, transparent 1px), linear-gradient(90deg, #004ac6 1px, transparent 1px)", backgroundSize: "40px 40px" }}></div>
              <svg className="w-full h-full text-xs font-mono" viewBox="0 0 800 240">
                {/* Horizontal guide grids */}
                <line x1="40" y1="40" x2="760" y2="40" stroke="#e1e2ed" strokeDasharray="4 4" />
                <line x1="40" y1="100" x2="760" y2="100" stroke="#e1e2ed" strokeDasharray="4 4" />
                <line x1="40" y1="160" x2="760" y2="160" stroke="#e1e2ed" strokeDasharray="4 4" />
                <line x1="40" y1="220" x2="760" y2="220" stroke="#c3c6d7" />

                {/* Benchmark S&P 500 Line (Grey) */}
                <path
                  d="M 40,180 Q 200,165 300,150 T 560,110 T 760,95"
                  fill="none"
                  stroke="#505f76"
                  strokeWidth="2"
                  strokeDasharray="2"
                />

                {/* Strategy SMA Line (Blue) */}
                <path
                  d="M 40,180 Q 150,150 260,120 T 480,80 T 680,45 T 760,35"
                  fill="none"
                  stroke="#004ac6"
                  strokeWidth="3.5"
                />

                {/* Price labels */}
                <text x="765" y="44" fill="#737686">+124.8%</text>
                <text x="765" y="104" fill="#737686">+80.0%</text>
                <text x="765" y="164" fill="#737686">+40.0%</text>
                <text x="765" y="224" fill="#737686">Base</text>

                {/* Month labels */}
                <text x="40" y="238" fill="#737686">Jan</text>
                <text x="184" y="238" fill="#737686">Apr</text>
                <text x="328" y="238" fill="#737686">Jul</text>
                <text x="472" y="238" fill="#737686">Oct</text>
                <text x="616" y="238" fill="#737686">Dec</text>
              </svg>
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
                    <p className="text-base font-bold text-[#191b23]">24.8%</p>
                  </div>
                  <span className="text-[10px] text-[#10b981] font-bold mb-0.5">+12.4% vs Bm</span>
                </div>
                <div className="flex justify-between items-end border-b border-[#e7e7f3] pb-1.5">
                  <div>
                    <p className="text-[10px] text-[#737686]">Sharpe Ratio</p>
                    <p className="text-base font-bold text-[#191b23]">1.82</p>
                  </div>
                  <span className="text-[10px] text-[#10b981] font-bold mb-0.5">Excellent</span>
                </div>
                <div className="flex justify-between items-end border-b border-[#e7e7f3] pb-1.5">
                  <div>
                    <p className="text-[10px] text-[#737686]">Max Drawdown</p>
                    <p className="text-base font-bold text-[#191b23] text-[#ba1a1a]">-11.4%</p>
                  </div>
                  <span className="text-[10px] text-[#737686] font-semibold mb-0.5">68 days</span>
                </div>
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-[10px] text-[#737686]">Win Rate</p>
                    <p className="text-base font-bold text-[#191b23]">58.2%</p>
                  </div>
                  <div className="w-16 h-1 bg-[#e7e7f3] rounded-full overflow-hidden mb-1.5">
                    <div className="h-full bg-[#004ac6]" style={{ width: "58%" }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Score Block */}
            <div className="bg-[#004ac6] text-white rounded-xl p-4 shadow-sm">
              <p className="text-[9px] font-bold opacity-80 tracking-wider">STRATEGY SCORE</p>
              <div className="flex items-baseline gap-1 mt-1.5">
                <span className="text-3xl font-display font-bold">88</span>
                <span className="text-xs opacity-80">/ 100</span>
              </div>
              <p className="text-[11px] leading-snug mt-2 opacity-90">
                This strategy exhibits robust risk-adjusted returns during bearish volatility windows.
              </p>
            </div>
          </div>
        </div>

        {/* Transaction Ledger Table */}
        <div className="bg-white border border-[#c3c6d7] rounded-xl flex flex-col overflow-hidden shadow-sm">
          <div className="px-6 py-3.5 border-b border-[#c3c6d7] flex items-center justify-between bg-[#faf8ff]">
            <div className="flex items-center gap-3">
              <h3 className="font-display font-bold text-sm text-[#191b23]">Transaction Ledger</h3>
              <span className="bg-[#e7e7f3] text-[#0b1c30] px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                142 TRADES
              </span>
            </div>
            <div className="flex gap-2 text-xs">
              <button 
                onClick={() => alert("Ledger exported as CSV.")}
                className="px-3 py-1 rounded-lg border border-[#c3c6d7] bg-white text-[#191b23] hover:bg-[#faf8ff] transition-colors font-semibold"
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
                {ledgerTrades.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-[#faf8ff] transition-colors h-10">
                    <td className="px-6 py-2 font-mono text-[#191b23]">{trade.datetime}</td>
                    <td className="px-6 py-2">
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                        trade.side === "Buy"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-6 py-2 font-semibold text-[#191b23]">{trade.asset}</td>
                    <td className="px-6 py-2 text-right font-mono font-bold text-[#191b23]">{trade.qty}</td>
                    <td className="px-6 py-2 text-right font-mono">{trade.price.toFixed(2)}</td>
                    <td className="px-6 py-2 text-right font-mono">{trade.value}</td>
                    <td className={`px-6 py-2 text-right font-mono font-bold ${
                      trade.positive ? "text-[#10b981]" : "text-[#ba1a1a]"
                    }`}>
                      {trade.pnl}
                    </td>
                    <td className="px-6 py-2 text-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] inline-block"></span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
