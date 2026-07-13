"use client";

import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { api, ResearchResponse, MarketDataResponse } from "../app/api";

interface HeaderProps {
  collapsed?: boolean;
  theme?: "light" | "dark";
  onToggleTheme?: () => void;
  onOpenSearch?: () => void;
}

export default function Header({
  collapsed = false,
  theme = "light",
  onToggleTheme = () => {},
  onOpenSearch = () => {},
}: HeaderProps) {
  const pathname = usePathname();
  const fetchedRef = useRef(false);
  const [isMounted, setIsMounted] = useState(false);
  
  // States for market data indices
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  
  // States for selected stock research
  const [researchData, setResearchData] = useState<ResearchResponse | null>(null);

  // Notification panel state
  const [showNotifPanel, setShowNotifPanel] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 1, title: "Live Market Stream Connected", desc: "Realtime data feed linked to Tokyo-1 Node.", time: "Just now", unread: true, type: "success" },
    { id: 2, title: "Backtest Finished", desc: "Momentum breakout simulation completed.", time: "12m ago", unread: true, type: "info" },
    { id: 3, title: "System Operational", desc: "All background tasks and API routes healthy.", time: "1h ago", unread: false, type: "system" }
  ]);

  const hasUnread = notifications.some(n => n.unread);

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const fetchMarketData = async () => {
    try {
      const data = await api.getMarketData();
      if (data.success) {
        setMarketData(data);
        if (typeof window !== "undefined") {
          localStorage.setItem("tradeGPT_market_data_cache", JSON.stringify(data));
        }
      }
    } catch (e) {
      console.warn("Failed to fetch market indices in Header:", e);
    }
  };

  useEffect(() => {
    setIsMounted(true);
    if (typeof window !== "undefined") {
      const cache = localStorage.getItem("tradeGPT_market_data_cache");
      if (cache) {
        try {
          const parsed = JSON.parse(cache);
          if (parsed && parsed.success) {
            setMarketData(parsed);
          }
        } catch (e) {
          console.warn("Failed to parse market cache in Header:", e);
        }
      }
    }
  }, []);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    const timer = setTimeout(fetchMarketData, 500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!pathname.startsWith("/institutional-research")) return;
    
    const handleSymbolChange = () => {
      if (typeof window === "undefined") return;
      const params = new URLSearchParams(window.location.search);
      const sym = params.get("symbol");
      const w = window as any;
      if (sym && w.__tradeGPTResearchCache?.[sym]) {
        setResearchData(w.__tradeGPTResearchCache[sym]);
      }
    };

    window.addEventListener("symbolChanged", handleSymbolChange);
    return () => window.removeEventListener("symbolChanged", handleSymbolChange);
  }, [pathname]);

  // Dynamic variables for Default header
  const niftyPrice = marketData?.indices?.NIFTY?.price ?? null;
  const niftyChange = marketData?.indices?.NIFTY?.change ?? null;
  const sensexPrice = marketData?.indices?.SENSEX?.price ?? null;
  const sensexChange = marketData?.indices?.SENSEX?.change ?? null;
  const bankniftyPrice = marketData?.indices?.BANKNIFTY?.price ?? null;
  const bankniftyChange = marketData?.indices?.BANKNIFTY?.change ?? null;
  const usdinrPrice = marketData?.indices?.USDINR?.price ?? null;
  const usdinrChange = marketData?.indices?.USDINR?.change ?? null;
  const goldPrice = marketData?.indices?.GOLD?.price ?? null;
  const goldChange = marketData?.indices?.GOLD?.change ?? null;

  // Dynamic variables for Research header
  const symbolName = researchData?.symbol || "";
  const priceVal = researchData?.price ?? null;
  const changeVal = researchData?.change ?? null;
  const mktCapVal = researchData?.mkt_cap || "—";
  const peRatioVal = researchData?.pe_ratio ?? null;
  const betaVal = researchData?.beta ?? null;

  // Marquee Ticker Loop Content
  const tickerContent = (isMounted && marketData) ? (
    <>
      <span className="font-mono flex items-center gap-1.5 shrink-0 animate-fade-in">
        <span className="font-bold text-text-primary">NIFTY 50:</span>
        <span className="text-text-primary/95">
          {niftyPrice !== null ? niftyPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
        </span>
        {niftyChange !== null && (
          <span className={`text-[10px] font-bold ${niftyChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            {niftyChange >= 0 ? "▲" : "▼"}{Math.abs(niftyChange).toFixed(2)}%
          </span>
        )}
      </span>
      <span className="font-mono flex items-center gap-1.5 shrink-0 animate-fade-in">
        <span className="font-bold text-text-primary">SENSEX:</span>
        <span className="text-text-primary/95">
          {sensexPrice !== null ? sensexPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
        </span>
        {sensexChange !== null && (
          <span className={`text-[10px] font-bold ${sensexChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            {sensexChange >= 0 ? "▲" : "▼"}{Math.abs(sensexChange).toFixed(2)}%
          </span>
        )}
      </span>
      <span className="font-mono flex items-center gap-1.5 shrink-0 animate-fade-in">
        <span className="font-bold text-text-primary">BANK NIFTY:</span>
        <span className="text-text-primary/95">
          {bankniftyPrice !== null ? bankniftyPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
        </span>
        {bankniftyChange !== null && (
          <span className={`text-[10px] font-bold ${bankniftyChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            {bankniftyChange >= 0 ? "▲" : "▼"}{Math.abs(bankniftyChange).toFixed(2)}%
          </span>
        )}
      </span>
      <span className="font-mono flex items-center gap-1.5 shrink-0 animate-fade-in">
        <span className="font-bold text-text-primary">USDINR:</span>
        <span className="text-text-primary/95">
          {usdinrPrice !== null ? usdinrPrice.toFixed(2) : "—"}
        </span>
        {usdinrChange !== null && (
          <span className={`text-[10px] font-bold ${usdinrChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            {usdinrChange >= 0 ? "▲" : "▼"}{Math.abs(usdinrChange).toFixed(2)}%
          </span>
        )}
      </span>
      <span className="font-mono flex items-center gap-1.5 shrink-0 animate-fade-in">
        <span className="font-bold text-text-primary">GOLD:</span>
        <span className="text-text-primary/95">
          {goldPrice !== null ? `$${goldPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
        </span>
        {goldChange !== null && (
          <span className={`text-[10px] font-bold ${goldChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            {goldChange >= 0 ? "▲" : "▼"}{Math.abs(goldChange).toFixed(2)}%
          </span>
        )}
      </span>
    </>
  ) : (
    <>
      <span className="font-mono flex items-center gap-2 shrink-0 opacity-50">
        <span className="font-bold text-text-primary">NIFTY 50:</span>
        <span className="w-14 h-3 bg-text-muted/20 rounded animate-pulse"></span>
      </span>
      <span className="font-mono flex items-center gap-2 shrink-0 opacity-50">
        <span className="font-bold text-text-primary">SENSEX:</span>
        <span className="w-16 h-3 bg-text-muted/20 rounded animate-pulse"></span>
      </span>
      <span className="font-mono flex items-center gap-2 shrink-0 opacity-50">
        <span className="font-bold text-text-primary">BANK NIFTY:</span>
        <span className="w-16 h-3 bg-text-muted/20 rounded animate-pulse"></span>
      </span>
    </>
  );

  return (
    <header
      className={`no-print fixed top-0 right-0 h-14 bg-surface-base/80 backdrop-blur-md border-b border-border-subtle flex items-center justify-between px-6 z-20 font-body select-none transition-all duration-300 ease-in-out ${
        collapsed ? "left-[70px]" : "left-[260px]"
      }`}
    >
      <div className="flex items-center gap-6 overflow-hidden">
        {pathname.startsWith("/institutional-research") ? (
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="font-display text-base tracking-tight text-primary font-bold uppercase">{symbolName || "SELECT STOCK"}</span>
              {symbolName && <span className="px-1.5 py-0.5 bg-canvas text-[9px] font-bold rounded border border-border-subtle text-text-muted">NSE</span>}
            </div>
            {priceVal !== null && (
              <div className="hidden md:flex items-center gap-5 text-xs whitespace-nowrap border-l border-border-subtle/50 pl-5">
                <div className="flex flex-col">
                  <span className="text-[9px] text-text-muted uppercase font-bold leading-tight">Price</span>
                  <span className="font-bold text-text-primary font-mono">
                    ₹{priceVal.toLocaleString(undefined, { minimumFractionDigits: 2 })}{" "}
                    {changeVal !== null && (
                      <span className={`text-[10px] font-semibold ${changeVal >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
                        {changeVal >= 0 ? "+" : ""}{changeVal.toFixed(2)}%
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-text-muted uppercase font-bold leading-tight">Mkt Cap</span>
                  <span className="font-semibold text-text-muted font-mono">{mktCapVal}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-text-muted uppercase font-bold leading-tight">P/E (TTM)</span>
                  <span className="font-semibold text-text-muted font-mono">{peRatioVal !== null ? `${peRatioVal.toFixed(1)}x` : "—"}</span>
                </div>
              </div>
            )}
          </div>
        ) : pathname.startsWith("/portfolio-intelligence") ? (
          <div className="flex items-center gap-4">
            <span className="font-display text-base font-bold text-primary">FinIntel Workstation</span>
            <div className="h-4 w-px bg-border-subtle mx-1"></div>
            <span className="text-xs text-text-muted font-bold uppercase tracking-widest opacity-80">Portfolio Suite</span>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <h1 className="font-display text-base tracking-tight text-primary font-bold whitespace-nowrap">
              {pathname.includes("settings") ? "Settings Console" : "Markets Desk"}
            </h1>
          </div>
        )}

        {/* Infinite Market Marquee Loop (GitHub / Apple Style) */}
        {!pathname.includes("settings") && (
          <div className="hidden xl:flex items-center overflow-hidden max-w-[450px] w-full relative pointer-events-auto select-none border-l border-r border-border-subtle/30 px-4">
            <div className="animate-marquee flex gap-8 items-center py-2 text-xs">
              {tickerContent}
              {tickerContent}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Global Stock Search Link to command palette */}
        <div
          onClick={onOpenSearch}
          className="flex items-center border border-border-subtle rounded-lg px-3 py-1.5 bg-canvas hover:bg-surface-elevation transition-all cursor-pointer w-44 justify-between text-text-muted active-press shrink-0"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined !text-sm">search</span>
            <span className="text-[10px] font-bold uppercase tracking-wider">Search CMD</span>
          </div>
          <kbd className="text-[9px] font-mono font-bold bg-surface-base px-1 py-0.2 border border-border-subtle rounded text-text-muted shadow-sm">
            ⌘K
          </kbd>
        </div>

        <div className="flex items-center gap-3">
          {/* Bloomberg Dark Mode Toggle */}
          <button
            onClick={onToggleTheme}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-canvas rounded-full transition-colors active-press cursor-pointer"
            title="Toggle Bloomberg Dark Mode (T)"
          >
            <span className="material-symbols-outlined !text-[1.25rem]">
              {theme === "light" ? "dark_mode" : "light_mode"}
            </span>
          </button>

          {/* Professional Notification Center */}
          <div className="relative">
            <button
              onClick={() => setShowNotifPanel(!showNotifPanel)}
              className="p-1.5 text-text-muted hover:text-text-primary hover:bg-canvas rounded-full transition-colors relative cursor-pointer active-press"
              aria-label="Notifications"
            >
              <span className="material-symbols-outlined !text-[1.25rem]">notifications</span>
              {hasUnread && (
                <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-[#10b981] rounded-full animate-ping"></span>
              )}
            </button>
            
            {showNotifPanel && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNotifPanel(false)} />
                <div className="absolute right-0 top-9 w-76 bg-surface-base border border-border-subtle rounded-xl shadow-xl z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-border-subtle bg-canvas flex items-center justify-between">
                    <span className="text-[10px] font-bold text-text-primary uppercase tracking-wider">System Notifications</span>
                    <div className="flex gap-2">
                      <button onClick={markAllRead} className="text-[9px] text-primary hover:underline font-bold uppercase">Mark Read</button>
                      <button onClick={() => setShowNotifPanel(false)} className="text-text-muted hover:text-text-primary">
                        <span className="material-symbols-outlined !text-sm">close</span>
                      </button>
                    </div>
                  </div>
                  <div className="p-2 space-y-1.5 max-h-[250px] overflow-y-auto custom-scrollbar">
                    {notifications.map(n => (
                      <div key={n.id} className={`flex items-start gap-2.5 p-2 rounded-lg ${n.unread ? "bg-primary/5 border-l-2 border-primary" : "opacity-75"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${n.type === "success" ? "bg-[#10b981]" : "bg-primary"}`}></span>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-baseline mb-0.5">
                            <p className="text-[11px] font-bold text-text-primary truncate">{n.title}</p>
                            <span className="text-[8px] font-mono text-text-muted">{n.time}</span>
                          </div>
                          <p className="text-[10px] text-text-muted leading-tight">{n.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
