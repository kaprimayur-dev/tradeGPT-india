"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { api, IndexTicker } from "../app/api";

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function Sidebar({ collapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [showAddTicker, setShowAddTicker] = useState(false);
  const [newTicker, setNewTicker] = useState("");
  const [mounted, setMounted] = useState(false);
  const [deskDropdownOpen, setDeskDropdownOpen] = useState(false);

  const [watchlistTickers, setWatchlistTickers] = useState<string[]>(["RELIANCE", "HDFCBANK", "TCS"]);
  const [watchlistData, setWatchlistData] = useState<Record<string, IndexTicker>>({});

  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("trade_watchlist");
      if (saved) {
        try {
          setWatchlistTickers(JSON.parse(saved));
        } catch (e) {
          console.error("Failed to parse watchlist from localStorage", e);
        }
      }
    }
  }, []);

  useEffect(() => {
    if (mounted && typeof window !== "undefined") {
      localStorage.setItem("trade_watchlist", JSON.stringify(watchlistTickers));
    }
  }, [watchlistTickers, mounted]);

  const fetchWatchlistPrices = async () => {
    try {
      if (watchlistTickers.length === 0) return;
      const res = await api.getMarketData(undefined, undefined, watchlistTickers);
      if (res.watchlist) {
        setWatchlistData(res.watchlist);
      }
    } catch (err) {
      console.error("Failed to load watchlist prices", err);
    }
  };

  useEffect(() => {
    if (!mounted) return;
    fetchWatchlistPrices();
    const interval = setInterval(fetchWatchlistPrices, 30000);
    return () => clearInterval(interval);
  }, [watchlistTickers, mounted]);

  const menuItems = [
    {
      name: "Terminal",
      icon: "terminal",
      href: "/market-intelligence",
      activePattern: /^\/market-intelligence/,
    },
    {
      name: "Watchlist",
      icon: "visibility",
      href: "#",
      activePattern: null,
    },
    {
      name: "Analytics",
      icon: "analytics",
      href: "/quantitative-strategy",
      activePattern: /^\/quantitative-strategy/,
    },
    {
      name: "Research",
      icon: "menu_book",
      href: "/institutional-research",
      activePattern: /^\/institutional-research/,
    },
    {
      name: "Portfolio",
      icon: "account_balance_wallet",
      href: "/portfolio-intelligence",
      activePattern: /^\/portfolio-intelligence/,
    },
  ];

  // Desks/Workspaces configuration
  const desks = [
    { id: "market", label: "Markets Desk", path: "/market-intelligence", icon: "monitoring" },
    { id: "research", label: "RAG Research Desk", path: "/institutional-research", icon: "search_insights" },
    { id: "portfolio", label: "Portfolio Suite", path: "/portfolio-intelligence", icon: "donut_large" },
    { id: "quant", label: "Quant Strategy Lab", path: "/quantitative-strategy", icon: "analytics" },
  ];

  const getActiveDesk = () => {
    if (pathname.includes("/market-intelligence")) return desks[0];
    if (pathname.includes("/institutional-research")) return desks[1];
    if (pathname.includes("/portfolio-intelligence")) return desks[2];
    if (pathname.includes("/quantitative-strategy")) return desks[3];
    return desks[0];
  };

  const activeDesk = getActiveDesk();

  return (
    <aside
      className={`no-print fixed left-0 top-0 h-full bg-surface-base border-r border-border-subtle flex flex-col py-6 px-4 z-30 font-body select-none transition-all duration-300 ease-in-out ${
        collapsed ? "w-[70px]" : "w-[260px]"
      }`}
    >
      {/* Brand Header */}
      <div className="mb-6 px-1 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-white shrink-0 shadow-md">
            <span className="material-symbols-outlined !text-[1.25rem]">terminal</span>
          </div>
          {!collapsed && (
            <div>
              <h1 className="font-display font-bold text-base text-text-primary leading-tight">Alpha Terminal</h1>
              <p className="text-[9px] text-text-muted font-bold tracking-widest uppercase opacity-80">Institutional</p>
            </div>
          )}
        </div>
      </div>

      {/* Desk/Workspace Selector */}
      {!collapsed && (
        <div className="relative mb-5 px-1">
          <div
            onClick={() => setDeskDropdownOpen(!deskDropdownOpen)}
            className="flex items-center justify-between border border-border-subtle rounded-lg px-2.5 py-1.5 bg-canvas hover:bg-surface-elevation transition-all cursor-pointer active-press"
          >
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary !text-[1.1rem]">
                {activeDesk.icon}
              </span>
              <span className="text-xs font-bold text-text-primary">{activeDesk.label}</span>
            </div>
            <span className="material-symbols-outlined text-text-muted !text-xs">swap_vert</span>
          </div>

          {deskDropdownOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setDeskDropdownOpen(false)} />
              <div className="absolute top-9 left-0 right-0 bg-surface-base border border-border-subtle rounded-lg shadow-xl z-50 py-1 text-xs font-semibold overflow-hidden">
                {desks.map((d) => (
                  <div
                    key={d.id}
                    onClick={() => {
                      router.push(d.path);
                      setDeskDropdownOpen(false);
                    }}
                    className={`flex items-center gap-2 px-3 py-2 hover:bg-canvas cursor-pointer ${
                      activeDesk.id === d.id ? "text-primary bg-secondary-container/20" : "text-text-primary"
                    }`}
                  >
                    <span className="material-symbols-outlined !text-sm text-text-muted">{d.icon}</span>
                    <span>{d.label}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Navigation Router */}
      <nav className="flex-1 space-y-1.5">
        {menuItems.map((item) => {
          const isActive = item.activePattern ? item.activePattern.test(pathname) : false;

          return (
            <Link
              key={item.name}
              href={item.href}
              title={collapsed ? item.name : undefined}
              onClick={(e) => {
                if (item.name === "Watchlist") {
                  e.preventDefault();
                  setShowAddTicker((v) => !v);
                }
              }}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all active-press ${
                isActive
                  ? "bg-secondary-container text-on-secondary-container font-bold shadow-sm"
                  : "text-text-muted hover:bg-canvas"
              }`}
            >
              <span className="material-symbols-outlined !text-[1.25rem] shrink-0">
                {item.icon}
              </span>
              {!collapsed && <span className="text-xs font-bold tracking-wide">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapsible Watchlist Section (only visible when expanded) */}
      {!collapsed && (
        <div className="mt-auto border-t border-border-subtle pt-4 max-h-[180px] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-2 px-1">
            <h3 className="text-[9px] font-bold text-text-muted tracking-wider uppercase">My Watchlist</h3>
            <span
              onClick={() => setShowAddTicker((v) => !v)}
              className="material-symbols-outlined text-text-muted hover:text-primary cursor-pointer !text-xs"
              title="Add ticker"
            >
              add
            </span>
          </div>

          {/* Add Ticker Mini-Modal */}
          {showAddTicker && (
            <div className="mx-1 mb-2 bg-canvas border border-border-subtle rounded-lg p-2 shrink-0">
              <p className="text-[9px] text-text-muted uppercase font-bold mb-1">Add Symbol</p>
              <div className="flex gap-1">
                <input
                  type="text"
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newTicker.trim()) {
                      setWatchlistTickers((prev) => [...prev, newTicker.trim()]);
                      setNewTicker("");
                      setShowAddTicker(false);
                    }
                  }}
                  placeholder="E.g. INFY"
                  className="flex-1 bg-surface-base border border-border-subtle rounded px-2 py-0.5 text-xs font-mono text-text-primary outline-none focus:border-primary uppercase"
                  autoFocus
                />
                <button
                  onClick={() => {
                    if (newTicker.trim()) {
                      setWatchlistTickers((prev) => [...prev, newTicker.trim()]);
                      setNewTicker("");
                      setShowAddTicker(false);
                    }
                  }}
                  className="px-2 py-0.5 bg-primary text-white text-[10px] font-bold rounded hover:bg-primary-fixed-dim transition-colors"
                >
                  Add
                </button>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2.5">
            {!mounted ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-3 w-16 bg-border-subtle rounded"></div>
                <div className="h-3 w-12 bg-border-subtle rounded"></div>
              </div>
            ) : (
              watchlistTickers.map((ticker) => {
                const data = watchlistData[ticker.toUpperCase()];
                const price = data && typeof data.price === "number" ? data.price : null;
                const change = data && typeof data.change === "number" ? data.change : null;
                const sparkline = data?.sparkline || [];
                const isPositive = change !== null && change > 0;
                const isFlat = change === null || change === 0;

                let sparklineSvg = null;
                if (sparkline && sparkline.length > 1) {
                  const minVal = Math.min(...sparkline);
                  const maxVal = Math.max(...sparkline);
                  const range = maxVal - minVal || 1;
                  const points = sparkline
                    .map((val, idx) => {
                      const x = (idx / (sparkline.length - 1)) * 40;
                      const y = 14 - ((val - minVal) / range) * 12;
                      return `${x},${y}`;
                    })
                    .join(" ");

                  sparklineSvg = (
                    <svg className="w-8 h-4 mx-1.5 text-current overflow-visible shrink-0 pointer-events-none" viewBox="0 0 40 15">
                      <polyline
                        fill="none"
                        stroke={isFlat ? "#737686" : isPositive ? "#10b981" : "#ba1a1a"}
                        strokeWidth="1.2"
                        points={points}
                      />
                    </svg>
                  );
                }

                return (
                  <div
                    key={ticker}
                    className="flex items-center justify-between border-b border-border-subtle/40 pb-1.5 hover:bg-canvas px-1 rounded transition-colors group cursor-pointer"
                  >
                    <Link
                      href={`/institutional-research?symbol=${ticker}`}
                      className="flex-1 min-w-0"
                    >
                      <p className="font-mono text-xs font-bold text-text-primary truncate">{ticker.toUpperCase()}</p>
                      <div className="flex items-center mt-0.5">
                        <p className="text-[9px] text-text-muted font-mono shrink-0">
                          {price !== null ? `₹${price.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "..."}
                        </p>
                        {sparklineSvg}
                      </div>
                    </Link>
                    <div className="flex items-center gap-1 shrink-0">
                      {change !== null && (
                        <span className={`text-[9px] font-bold font-mono ${isFlat ? "text-text-muted" : isPositive ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
                          {isFlat ? "—" : `${isPositive ? "+" : ""}${change.toFixed(2)}%`}
                        </span>
                      )}
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          setWatchlistTickers((prev) => prev.filter((t) => t !== ticker));
                        }}
                        className="material-symbols-outlined text-text-muted hover:text-alert-red cursor-pointer !text-xs opacity-0 group-hover:opacity-100 transition-opacity p-0.5"
                        title="Remove"
                      >
                        delete
                      </span>
                    </div>
                  </div>
                );
              })
            )}
            {watchlistTickers.length === 0 && (
              <p className="text-[10px] text-text-muted text-center italic py-2">Watchlist empty</p>
            )}
          </div>
        </div>
      )}

      {/* Collapse Toggle & Profile Row */}
      <div className="mt-auto border-t border-border-subtle pt-4 shrink-0">
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="w-full flex items-center justify-center gap-2 py-1.5 mb-2 hover:bg-canvas rounded-lg text-text-muted hover:text-text-primary transition-all text-xs font-bold active-press"
          >
            <span className="material-symbols-outlined !text-lg">
              {collapsed ? "arrow_forward_ios" : "arrow_back_ios"}
            </span>
            {!collapsed && <span>Collapse Sidebar</span>}
          </button>
        )}

        <div className="flex items-center gap-3 px-1 mt-1">
          <div className="w-9 h-9 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-bold text-xs shrink-0 select-none shadow-inner">
            AS
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-text-primary truncate">Alex Sterling</p>
              <p className="text-[10px] text-text-muted font-semibold uppercase tracking-wider">Senior Quant</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
