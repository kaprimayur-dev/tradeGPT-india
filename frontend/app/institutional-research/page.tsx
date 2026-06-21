"use client";

import { useState, useEffect } from "react";
import { api } from "../api";

export default function InstitutionalResearchPage() {
  const [searchSymbol, setSearchSymbol] = useState("RELIANCE");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bind values from API
  const [recommendation, setRecommendation] = useState("OVERWEIGHT");
  const [targetPrice, setTargetPrice] = useState(3450.00);
  const [upside, setUpside] = useState(15.6);
  const [report, setReport] = useState<string | null>(null);
  
  const [growthDrivers, setGrowthDrivers] = useState([
    {
      title: "New Energy Ecosystem",
      icon: "bolt",
      desc: "Implementation of the Dhirubhai Ambani Green Energy Giga Complex. Expected reduction in hydrogen production costs to $1/kg by 2030."
    },
    {
      title: "Jio 5G Monetization",
      icon: "signal_cellular_alt",
      desc: "ARPU (Average Revenue Per User) expansion through 5G standalone adoption and fixed wireless access (JioAirFiber)."
    }
  ]);

  const [riskFactors, setRiskFactors] = useState([
    { factor: "Crude Volatility", impact: "High", prob: "Medium", score: 8.2 },
    { factor: "Regulatory Headwinds", impact: "Moderate", prob: "Low", score: 6.5 },
    { factor: "Capex Overrun", impact: "Medium", prob: "Medium", score: 7.4 },
  ]);

  const [citations, setCitations] = useState([
    { title: "Annual Report FY2025-26", meta: "SEC | 128 Pages | PDF" },
    { title: "Q4 Earnings Presentation", meta: "IR Portal | 45 Pages | PDF" },
    { title: "Strategic New Energy Roadmap", meta: "Exchange Filing | 12 Pages | PDF" },
    { title: "Sustainability Report 2026", meta: "ESG Filing | 88 Pages | PDF" },
  ]);

  const [technicalMetrics, setTechnicalMetrics] = useState({
    rsi: 58.42,
    sma_50: 2845.10,
    sma_200: 2612.45,
    volume: "6.8M",
    vwap: 2991.05
  });

  const [ownership, setOwnership] = useState({
    promoter: 50.39,
    fii: 22.12,
    dii: 16.55,
    public: 10.94
  });

  const [price, setPrice] = useState(2984.45);
  const [change, setChange] = useState(-0.42);
  const [mktCap, setMktCap] = useState("20.21T");
  const [peRatio, setPeRatio] = useState(28.4);
  const [beta, setBeta] = useState(0.92);
  const [timestamp, setTimestamp] = useState("20 JUN 2026, 09:30 AM IST");

  const runSearch = async (symbol: string) => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getStockResearch(symbol);
      if (res.success) {
        setRecommendation(res.recommendation);
        setTargetPrice(res.target_price);
        setUpside(res.upside);
        setReport(res.report);
        setGrowthDrivers(res.growth_drivers || []);
        setRiskFactors(res.risk_matrix || []);
        setCitations(res.citations || []);
        setTechnicalMetrics(res.technical_metrics);
        setOwnership(res.ownership);
        setPrice(res.price);
        setChange(res.change);
        setMktCap(res.mkt_cap);
        setPeRatio(res.pe_ratio);
        setBeta(res.beta);
        if (res.timestamp) {
          try {
            const date = new Date(res.timestamp);
            setTimestamp(date.toLocaleString());
          } catch {
            setTimestamp(res.timestamp);
          }
        }
        // Cache in global window for Header to consume without duplicate API call
        if (typeof window !== "undefined") {
          (window as any).__tradeGPTResearchCache = (window as any).__tradeGPTResearchCache || {};
          (window as any).__tradeGPTResearchCache[symbol.toUpperCase()] = res;
        }
      } else {
        throw new Error("Failed to compile research");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during equity research");
    } finally {
      setLoading(false);
    }
  };

  const handleRunResearch = async () => {
    if (!searchSymbol.trim()) return;
    
    // Sync URL parameter and dispatch event to header
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("symbol", searchSymbol);
      window.history.pushState(null, "", `${url.pathname}?${url.searchParams.toString()}`);
      window.dispatchEvent(new Event("symbolChanged"));
    }
    
    await runSearch(searchSymbol);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const symbolFromUrl = params.get("symbol");
      if (symbolFromUrl) {
        setSearchSymbol(symbolFromUrl);
        runSearch(symbolFromUrl);
        return;
      }
    }
    handleRunResearch();
  }, []);

  return (
    <div className="flex-1 bg-[#faf8ff] p-6 font-body">
      
      {/* Search Header (No Print) */}
      <div className="bg-white border border-[#c3c6d7] rounded-xl p-5 mb-6 shadow-sm no-print">
        <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider mb-2">Institutional Research Query</h3>
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="text-[10px] font-bold text-[#737686] uppercase block mb-1">Stock Ticker Symbol or Company Name</label>
            <input
              type="text"
              value={searchSymbol}
              onChange={(e) => setSearchSymbol(e.target.value)}
              className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded-lg px-3 py-2 text-xs text-[#191b23] font-semibold focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none uppercase font-mono h-10"
              placeholder="E.g. TCS, RELIANCE, INFY"
            />
          </div>
          <button
            onClick={handleRunResearch}
            disabled={loading}
            className="px-6 py-2 bg-[#004ac6] text-white rounded-lg text-xs font-bold hover:bg-[#003ea8] transition-colors active:scale-95 duration-100 disabled:opacity-50 h-10 flex items-center justify-center gap-1.5 shrink-0"
          >
            <span className="material-symbols-outlined !text-base">search</span>
            <span>{loading ? "Researching..." : "Run Analysis"}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 relative min-h-[500px]">
        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center z-30 rounded-xl">
            <div className="w-10 h-10 border-4 border-[#004ac6] border-t-transparent rounded-full animate-spin mb-3"></div>
            <p className="text-xs font-bold text-[#434655] uppercase tracking-wider animate-pulse">Running RAG Analyst Node...</p>
            <p className="text-[10px] text-[#737686] mt-1 font-mono">Fetching ChromaDB context and Yahoo pricing data</p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="col-span-12 bg-red-50 border border-red-200 rounded-xl p-6 text-center my-6">
            <span className="material-symbols-outlined text-[#ba1a1a] !text-4xl mb-2">warning</span>
            <h3 className="font-display font-bold text-base text-[#ba1a1a] uppercase tracking-wider">Research Failed</h3>
            <p className="text-xs text-[#737686] mt-2 mb-4 max-w-lg mx-auto leading-relaxed">{error}</p>
            <button
              onClick={handleRunResearch}
              className="px-5 py-2 bg-[#ba1a1a] hover:bg-[#a61717] text-white text-xs font-bold rounded-lg transition-all active:scale-95"
            >
              Retry Research
            </button>
          </div>
        )}

        {!error && (
          <>
            {/* Left Column (Wide): Research Note */}
            <div className="col-span-12 lg:col-span-8 flex flex-col gap-6 pr-0 lg:pr-6">
              
              {/* Document Header */}
              <div className="border-b border-[#c3c6d7] pb-6">
                <div className="flex items-center justify-between mb-2 text-xs">
                  <span className="text-[#004ac6] font-bold tracking-widest uppercase">
                    Research Report #{searchSymbol.toUpperCase()}-2026
                  </span>
                  <span className="text-[#737686] font-mono uppercase font-semibold">
                    Updated: {timestamp}
                  </span>
                </div>
                <h2 className="font-display font-bold text-2xl text-[#191b23] tracking-tight">
                  Integrated Financial Intelligence &amp; SWOT Summary
                </h2>
                <div className="flex items-center gap-3 mt-2 text-xs flex-wrap">
                  <span className="font-bold text-[#191b23] font-mono bg-slate-100 border px-2 py-0.5 rounded">
                    Price: ₹{price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <span className={`font-semibold font-mono px-2 py-0.5 rounded ${change >= 0 ? "bg-green-50 text-[#10b981] border-green-200" : "bg-red-50 text-[#ba1a1a] border-red-200"} border`}>
                    {change >= 0 ? "+" : ""}{change.toFixed(2)}%
                  </span>
                  <span className="text-[#737686] font-mono">
                    Mkt Cap: {mktCap}
                  </span>
                  <span className="text-[#737686] font-mono">
                    P/E: {peRatio ? peRatio.toFixed(1) : "N/A"}x
                  </span>
                  <span className="text-[#737686] font-mono">
                    Beta: {beta.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Executive Summary */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-1 h-5 bg-[#004ac6]"></div>
                  <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Executive Summary</h3>
                </div>
                <div className="text-xs text-[#434655] leading-relaxed space-y-4 font-mono whitespace-pre-wrap select-text bg-[#faf8ff] p-4 border rounded border-slate-200 overflow-x-auto">
                  {report || `Reliance Industries Limited (RIL) continues to demonstrate robust resilience across its diversified business segments...`}
                </div>

                <div className="grid grid-cols-3 gap-4 py-4 border-y border-[#c3c6d7] font-mono mt-4">
                  <div className="flex flex-col">
                    <span className="text-[9px] text-[#737686] uppercase font-bold">Recommendation</span>
                    <span className="text-[#004ac6] font-bold text-sm uppercase">{recommendation}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] text-[#737686] uppercase font-bold">Price Target (12M)</span>
                    <span className="text-[#191b23] font-bold text-sm">₹{targetPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] text-[#737686] uppercase font-bold">Upside</span>
                    <span className={`font-bold text-sm ${upside >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
                      {upside >= 0 ? "+" : ""}{upside.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </section>

              {/* Growth Drivers (Bento style) */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-1 h-5 bg-[#004ac6]"></div>
                  <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Primary Growth Drivers</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {growthDrivers.slice(0, 2).map((driver, idx) => (
                    <div key={idx} className="p-4 border border-[#c3c6d7] rounded-lg bg-white shadow-sm flex flex-col justify-between">
                      <div>
                        <span className="material-symbols-outlined text-[#004ac6] mb-2 !text-base">
                          {driver.icon === "bolt" ? "bolt" : driver.icon === "signal_cellular_alt" ? "signal_cellular_alt" : "trending_up"}
                        </span>
                        <h4 className="text-xs font-bold text-[#191b23] mb-1.5">{driver.title}</h4>
                        <p className="text-[11px] text-[#434655] leading-normal">{driver.desc}</p>
                      </div>
                    </div>
                  ))}
                  
                  {growthDrivers.length > 2 && (
                    <div className="p-4 border border-[#c3c6d7] rounded-lg bg-white shadow-sm col-span-1 sm:col-span-2 flex gap-4 items-center">
                      <div className="w-16 h-16 flex-shrink-0 bg-[#f3f3fe] rounded flex items-center justify-center border border-[#c3c6d7]">
                        <span className="material-symbols-outlined text-xl text-[#737686]">layers</span>
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[#191b23] mb-1">{growthDrivers[2].title}</h4>
                        <p className="text-[11px] text-[#434655] leading-normal">
                          {growthDrivers[2].desc}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </section>

              {/* Risk Matrix Table */}
              <section className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-1 h-5 bg-[#004ac6]"></div>
                  <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Risk Matrix</h3>
                </div>
                <div className="overflow-x-auto border border-[#c3c6d7] rounded-lg shadow-sm">
                  <table className="w-full text-xs text-left border-collapse bg-white">
                    <thead>
                      <tr className="bg-[#f3f3fe] text-[#737686] font-mono uppercase text-[9px] border-b border-[#c3c6d7] font-bold">
                        <th className="px-4 py-2.5">Risk Factor</th>
                        <th className="px-4 py-2.5">Impact</th>
                        <th className="px-4 py-2.5">Probability</th>
                        <th className="px-4 py-2.5 text-right">Severity Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e7e7f3] text-[#434655]">
                      {riskFactors.map((risk, idx) => (
                        <tr key={idx} className="hover:bg-[#faf8ff] transition-colors">
                          <td className="px-4 py-3 font-semibold text-[#191b23]">{risk.factor}</td>
                          <td className="px-4 py-3">{risk.impact}</td>
                          <td className="px-4 py-3">{risk.prob}</td>
                          <td className="px-4 py-3 text-right font-mono font-bold text-[#004ac6]">{Number(risk.score).toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {/* Right Column (Narrow): Metrics & Citations */}
            <div className="col-span-12 lg:col-span-4 border-l-0 lg:border-l border-[#c3c6d7] pl-0 lg:pl-6 space-y-8">
              
              {/* Technical Metrics */}
              <div>
                <h3 className="text-[10px] font-bold text-[#737686] tracking-wider uppercase mb-4">
                  Technical Metrics
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                    <span className="text-xs text-[#434655] font-medium">RSI (14-Day)</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[#191b23]">{technicalMetrics.rsi.toFixed(2)}</span>
                      <div className="w-12 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden shrink-0">
                        <span className="block h-full bg-[#004ac6]" style={{ width: `${Math.min(100, Math.max(0, technicalMetrics.rsi))}%` }}></span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                    <span className="text-xs text-[#434655] font-medium">50-Day Moving Avg</span>
                    <span className="font-mono font-bold text-[#191b23]">₹{technicalMetrics.sma_50.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                    <span className="text-xs text-[#434655] font-medium">200-Day Moving Avg</span>
                    <span className="font-mono font-bold text-[#191b23]">₹{technicalMetrics.sma_200.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                    <span className="text-xs text-[#434655] font-medium">Volume (Latest)</span>
                    <span className="font-mono font-bold text-[#191b23]">{technicalMetrics.volume}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                    <span className="text-xs text-[#434655] font-medium">VWAP</span>
                    <span className="font-mono font-bold text-[#191b23]">₹{technicalMetrics.vwap.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                  </div>
                </div>
              </div>

              {/* Citations badges */}
              <div>
                <h3 className="text-[10px] font-bold text-[#737686] tracking-wider uppercase mb-4">
                  Institutional Citations
                </h3>
                <div className="space-y-3">
                  {citations.map((cit, idx) => (
                    <a 
                      key={idx} 
                      href={`https://www.google.com/search?q=${encodeURIComponent(searchSymbol + " " + cit.title)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group p-2.5 border border-[#c3c6d7] rounded bg-white hover:border-[#004ac6] hover:text-[#004ac6] cursor-pointer transition-all flex items-center justify-between block"
                    >
                      <div className="overflow-hidden">
                        <p className="text-xs font-bold text-[#191b23] group-hover:text-[#004ac6] transition-colors truncate">
                          {cit.title}
                        </p>
                        <p className="text-[9px] text-[#737686] font-mono mt-0.5 truncate">{cit.meta}</p>
                      </div>
                      <span className="material-symbols-outlined text-[#737686] group-hover:text-[#004ac6] !text-sm flex-shrink-0">
                        open_in_new
                      </span>
                    </a>
                  ))}
                </div>
              </div>

              {/* Ownership Breakdown */}
              <div className="p-4 bg-white border border-[#c3c6d7] rounded-xl shadow-sm">
                <h4 className="text-[10px] font-bold text-[#191b23] uppercase tracking-wider mb-3">
                  Ownership Structure
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-[#004ac6] rounded-sm"></div>
                    <span className="text-xs text-[#434655] flex-1">Promoter Group</span>
                    <span className="text-xs font-mono font-bold text-[#191b23]">{ownership.promoter.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-[#505f76] rounded-sm"></div>
                    <span className="text-xs text-[#434655] flex-1">FII / FPI</span>
                    <span className="text-xs font-mono font-bold text-[#191b23]">{ownership.fii.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-[#c3c6d7] rounded-sm"></div>
                    <span className="text-xs text-[#434655] flex-1">DII / Mutual Funds</span>
                    <span className="text-xs font-mono font-bold text-[#191b23]">{ownership.dii.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-[#e7e7f3] rounded-sm"></div>
                    <span className="text-xs text-[#434655] flex-1">Public &amp; Others</span>
                    <span className="text-xs font-mono font-bold text-[#191b23]">{ownership.public.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
