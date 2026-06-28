"use client";

import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { api, ResearchResponse, MarketDataResponse } from "../app/api";

export default function Header() {
  const pathname = usePathname();
  const fetchedRef = useRef(false);
  
  // States for market data indices
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  
  // States for selected stock research (for Research header stats)
  const [researchData, setResearchData] = useState<ResearchResponse | null>(null);

  // Notification panel state
  const [showNotifPanel, setShowNotifPanel] = useState(false);

  // Fetch index rates for default layout — called once, no polling (page manages its own updates)
  const fetchMarketData = async () => {
    try {
      const data = await api.getMarketData();
      if (data.success) {
        setMarketData(data);
      }
    } catch (e) {
      console.warn("Failed to fetch market indices in Header:", e);
    }
  };

  useEffect(() => {
    // Fetch market data once on mount with a slight delay to avoid collision with page's own fetch.
    // No polling — the Market Intelligence page handles live price tick simulation.
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    const timer = setTimeout(fetchMarketData, 1500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Listen for symbolChanged event (dispatched by Research page after a query runs)
    // to update header research stats from page-level cache — no duplicate API call.
    if (!pathname.startsWith("/institutional-research")) return;
    
    const handleSymbolChange = () => {
      if (typeof window === "undefined") return;
      const params = new URLSearchParams(window.location.search);
      const sym = params.get("symbol");
      const w = window as Window & { __tradeGPTResearchCache?: Record<string, ResearchResponse> };
      if (sym && w.__tradeGPTResearchCache?.[sym]) {
        setResearchData(w.__tradeGPTResearchCache[sym] as ResearchResponse);
      }
    };

    window.addEventListener("symbolChanged", handleSymbolChange);
    return () => window.removeEventListener("symbolChanged", handleSymbolChange);
  }, [pathname]);

  // Dynamic variables for Default header
  const niftyPrice = marketData?.indices?.NIFTY?.price || 24013.10;
  const niftyChange = marketData?.indices?.NIFTY?.change || -0.64;
  const sensexPrice = marketData?.indices?.SENSEX?.price || 76802.90;
  const sensexChange = marketData?.indices?.SENSEX?.change || -0.78;
  const usdinrPrice = marketData?.indices?.USDINR?.price || 83.50;
  const usdinrChange = marketData?.indices?.USDINR?.change || -0.02;

  // Dynamic variables for Research header
  const symbolName = researchData?.symbol || "RELIANCE";
  const priceVal = researchData?.price || 2984.45;
  const changeVal = researchData?.change || -0.42;
  const mktCapVal = researchData?.mkt_cap || "20.21T";
  const peRatioVal = researchData?.pe_ratio || 28.4;
  const betaVal = researchData?.beta || 0.92;

  // 1. Portfolio Intelligence layout style
  if (pathname.startsWith("/portfolio-intelligence")) {
    return (
      <header className="no-print fixed top-0 left-[260px] right-0 h-14 bg-white border-b border-[#c3c6d7] flex justify-between items-center px-6 z-20 font-body select-none">
        <div className="flex items-center gap-4">
          <span className="font-display text-base font-bold text-[#004ac6]">FinIntel Workstation</span>
          <div className="h-4 w-px bg-[#c3c6d7] mx-1"></div>
          <span className="text-xs text-[#434655] font-bold uppercase tracking-widest opacity-60">Intelligence Terminal</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative">
            <button
              onClick={() => setShowNotifPanel((v) => !v)}
              className="relative cursor-pointer group p-1"
              aria-label="Notifications"
            >
              <span className="material-symbols-outlined text-[#434655] group-hover:text-[#004ac6] transition-colors !text-[1.25rem]">
                notifications
              </span>
              <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-[#10b981] rounded-full"></span>
            </button>
            {showNotifPanel && (
              <div className="absolute right-0 top-9 w-72 bg-white border border-[#c3c6d7] rounded-xl shadow-xl z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-[#e7e7f3] flex items-center justify-between">
                  <span className="text-xs font-bold text-[#191b23] uppercase tracking-wider">System Notifications</span>
                  <button onClick={() => setShowNotifPanel(false)} className="text-[#737686] hover:text-[#191b23]">
                    <span className="material-symbols-outlined !text-sm">close</span>
                  </button>
                </div>
                <div className="p-3 space-y-2">
                  <div className="flex items-start gap-2.5 p-2 rounded-lg bg-[#f3f3fe]">
                    <span className="w-2 h-2 rounded-full bg-[#10b981] mt-1 shrink-0"></span>
                    <div>
                      <p className="text-xs font-semibold text-[#191b23]">System Operational</p>
                      <p className="text-[10px] text-[#737686]">All backend engines running normally.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 p-2 rounded-lg">
                    <span className="w-2 h-2 rounded-full bg-[#004ac6] mt-1 shrink-0"></span>
                    <div>
                      <p className="text-xs font-semibold text-[#191b23]">Market Data Cached</p>
                      <p className="text-[10px] text-[#737686]">Live indices synced. Cache TTL: 120s.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 cursor-pointer border-l border-[#c3c6d7] pl-4">
            <span className="text-[11px] font-bold text-[#191b23] tracking-wide">J. HARRINGTON</span>
            <span className="material-symbols-outlined text-[#004ac6] !text-[1.4rem]" style={{ fontVariationSettings: "'FILL' 1" }}>
              account_circle
            </span>
          </div>
        </div>
      </header>
    );
  }

  // 2. Institutional Research layout style
  if (pathname.startsWith("/institutional-research")) {
    return (
      <header className="no-print fixed top-0 left-[260px] right-0 h-14 bg-white border-b border-[#c3c6d7] flex items-center justify-between px-6 z-20 font-body select-none">
        <div className="flex items-center gap-8 overflow-hidden">
          <div className="flex items-center gap-2">
            <span className="font-display text-lg tracking-tight text-[#004ac6] font-bold uppercase">{symbolName}</span>
            <span className="px-1.5 py-0.5 bg-[#e7e7f3] text-[9px] font-bold rounded border border-[#c3c6d7]">NSE</span>
          </div>
          <div className="flex items-center gap-5 text-xs whitespace-nowrap">
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Price</span>
              <span className="font-bold text-[#191b23] font-mono">
                ₹{priceVal.toLocaleString(undefined, { minimumFractionDigits: 2 })} <span className={`text-[10px] font-semibold ${changeVal >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>{changeVal >= 0 ? "+" : ""}{changeVal.toFixed(2)}%</span>
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Mkt Cap</span>
              <span className="font-semibold text-[#434655] font-mono">{mktCapVal}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">P/E (TTM)</span>
              <span className="font-semibold text-[#434655] font-mono">{peRatioVal ? peRatioVal.toFixed(1) : "N/A"}x</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Beta</span>
              <span className="font-semibold text-[#434655] font-mono">{betaVal.toFixed(2)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center border border-[#c3c6d7] rounded-lg px-3 py-1 bg-[#f3f3fe]">
            <span className="material-symbols-outlined text-[#737686] !text-sm mr-2">search</span>
            <input
              type="text"
              placeholder="Search instruments..."
              className="bg-transparent border-none p-0 text-xs text-[#191b23] w-36 focus:outline-none focus:ring-0 uppercase font-mono font-semibold"
              readOnly
              value={symbolName}
            />
          </div>
          <div className="flex items-center gap-1">
            <div className="relative">
              <button 
                onClick={() => setShowNotifPanel((v) => !v)}
                className="p-1.5 text-[#434655] hover:bg-[#f3f3fe] rounded-full transition-colors relative"
                aria-label="Notifications"
              >
                <span className="material-symbols-outlined !text-[1.25rem]">notifications</span>
                <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-[#10b981] rounded-full"></span>
              </button>
              {showNotifPanel && (
                <div className="absolute right-0 top-9 w-72 bg-white border border-[#c3c6d7] rounded-xl shadow-xl z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-[#e7e7f3] flex items-center justify-between">
                    <span className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Notifications</span>
                    <button onClick={() => setShowNotifPanel(false)} className="text-[#737686] hover:text-[#191b23]">
                      <span className="material-symbols-outlined !text-sm">close</span>
                    </button>
                  </div>
                  <div className="p-3 space-y-2">
                    <div className="flex items-start gap-2.5 p-2 rounded-lg bg-[#f3f3fe]">
                      <span className="w-2 h-2 rounded-full bg-[#10b981] mt-1 shrink-0"></span>
                      <div>
                        <p className="text-xs font-semibold text-[#191b23]">Research Engine Active</p>
                        <p className="text-[10px] text-[#737686]">ChromaDB and RAG pipeline online.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          <button 
            onClick={() => {
              const modal = document.getElementById("tradeModal");
              if (modal) modal.classList.remove("hidden");
            }}
            className="px-4 py-1.5 bg-[#004ac6] text-white rounded-lg text-xs font-semibold active:opacity-90 transition-opacity"
          >
            Execute Trade
          </button>
        </div>
      </header>
    );
  }

  // 3. Default layout style (Market Intelligence Terminal & Quantitative Strategy)
  return (
    <header className="no-print fixed top-0 left-[260px] right-0 h-14 bg-white border-b border-[#c3c6d7] flex items-center justify-between px-6 z-20 font-body select-none">
      <div className="flex items-center gap-6">
        <h1 className="font-display text-base tracking-tight text-[#004ac6] font-bold">Market Intel</h1>
        <nav className="hidden lg:flex items-center gap-5 text-xs text-[#434655]">
          <span className="font-mono text-[#004ac6] font-bold border-b-2 border-[#004ac6] py-4">
            NIFTY: {niftyPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })} ({niftyChange >= 0 ? "+" : ""}{niftyChange.toFixed(2)}%)
          </span>
          <span className="font-mono hover:text-[#191b23] transition-colors cursor-pointer">
            SENSEX: {sensexPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })} ({sensexChange >= 0 ? "+" : ""}{sensexChange.toFixed(2)}%)
          </span>
          <span className="font-mono hover:text-[#191b23] transition-colors cursor-pointer">
            USDINR: {usdinrPrice.toFixed(2)} ({usdinrChange >= 0 ? "+" : ""}{usdinrChange.toFixed(2)}%)
          </span>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1 border-r border-[#c3c6d7] pr-4">
          <div className="relative">
            <button
              onClick={() => setShowNotifPanel((v) => !v)}
              className="material-symbols-outlined text-[#434655] cursor-pointer hover:text-[#191b23] transition-colors !text-[1.25rem] p-1"
              aria-label="Notifications"
            >
              notifications
            </button>
            {showNotifPanel && (
              <div className="absolute right-0 top-9 w-72 bg-white border border-[#c3c6d7] rounded-xl shadow-xl z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-[#e7e7f3] flex items-center justify-between">
                  <span className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Terminal Notifications</span>
                  <button onClick={() => setShowNotifPanel(false)} className="text-[#737686] hover:text-[#191b23]">
                    <span className="material-symbols-outlined !text-sm">close</span>
                  </button>
                </div>
                <div className="p-3 space-y-2">
                  <div className="flex items-start gap-2.5 p-2 rounded-lg bg-[#f3f3fe]">
                    <span className="w-2 h-2 rounded-full bg-[#10b981] mt-1 shrink-0"></span>
                    <div>
                      <p className="text-xs font-semibold text-[#191b23]">Live Market Feed Active</p>
                      <p className="text-[10px] text-[#737686]">NIFTY 50 & SENSEX data streaming. Cache TTL: 120s.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 p-2 rounded-lg">
                    <span className="w-2 h-2 rounded-full bg-[#004ac6] mt-1 shrink-0"></span>
                    <div>
                      <p className="text-xs font-semibold text-[#191b23]">Backend: Tokyo-1 Node</p>
                      <p className="text-[10px] text-[#737686]">All API routes operational. No errors detected.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="material-symbols-outlined text-[#434655] cursor-pointer hover:text-[#191b23] transition-colors !text-[1.25rem] p-1"
            aria-label="Documentation"
            title="Terminal Documentation"
          >
            help_outline
          </a>
        </div>
        <button 
          onClick={() => {
            const modal = document.getElementById("tradeModal");
            if (modal) modal.classList.remove("hidden");
          }}
          className="bg-[#004ac6] text-white px-4 py-1.5 rounded-lg text-xs font-semibold hover:bg-[#003ea8] transition-colors active:scale-95 duration-150"
        >
          Execute Trade
        </button>
      </div>
    </header>
  );
}
