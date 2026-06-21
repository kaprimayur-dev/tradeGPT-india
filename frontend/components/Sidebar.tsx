"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const [showAddTicker, setShowAddTicker] = useState(false);
  const [newTicker, setNewTicker] = useState("");
  const [watchlistTickers, setWatchlistTickers] = useState<string[]>([]);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);

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
    {
      name: "Settings",
      icon: "settings",
      href: "#",
      activePattern: null,
    },
  ];

  return (
    <aside className="no-print fixed left-0 top-0 h-full w-[260px] bg-white border-r border-[#c3c6d7] flex flex-col py-6 px-4 z-30 font-body select-none">
      {/* Brand Header */}
      <div className="mb-8 px-2 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-[#004ac6] flex items-center justify-center text-white shrink-0">
          <span className="material-symbols-outlined !text-[1.25rem]">terminal</span>
        </div>
        <div>
          <h1 className="font-display font-bold text-lg text-[#191b23] leading-tight">Alpha Terminal</h1>
          <p className="text-[10px] text-[#737686] font-bold tracking-widest uppercase">Institutional Access</p>
        </div>
      </div>

      {/* Navigation Router */}
      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => {
          const isActive = item.activePattern ? item.activePattern.test(pathname) : false;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={(e) => {
                if (item.name === "Settings") {
                  e.preventDefault();
                  setShowSettingsPanel((v) => !v);
                } else if (item.name === "Watchlist") {
                  e.preventDefault();
                  setShowAddTicker((v) => !v);
                }
              }}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                isActive
                  ? "bg-[#d0e1fb] text-[#0b1c30] font-semibold"
                  : "text-[#434655] hover:bg-[#f3f3fe] transition-colors"
              }`}
            >
              <span className="material-symbols-outlined !text-[1.25rem] shrink-0">
                {item.icon}
              </span>
              <span className="text-sm font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Collapsible Watchlist Section */}
      <div className="mt-auto border-t border-[#c3c6d7] pt-4">
        <div className="flex items-center justify-between mb-3 px-2">
          <h3 className="text-[11px] font-bold text-[#737686] tracking-wider uppercase">Watchlist</h3>
          <span 
            onClick={() => setShowAddTicker((v) => !v)}
            className="material-symbols-outlined text-[#737686] hover:text-[#004ac6] cursor-pointer !text-sm"
            title="Add ticker"
          >
            add
          </span>
        </div>

        {/* Add Ticker Mini-Modal */}
        {showAddTicker && (
          <div className="mx-1 mb-3 bg-[#f3f3fe] border border-[#c3c6d7] rounded-lg p-2">
            <p className="text-[9px] text-[#737686] uppercase font-bold mb-1.5">Add Symbol to Watchlist</p>
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
                className="flex-1 bg-white border border-[#c3c6d7] rounded px-2 py-1 text-xs font-mono text-[#191b23] outline-none focus:border-[#004ac6] uppercase"
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
                className="px-2 py-1 bg-[#004ac6] text-white text-[10px] font-bold rounded hover:bg-[#003ea8] transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        )}
        <div className="space-y-3 px-1">
          {/* Watchlist Tickers */}
          <Link
            href="/institutional-research?symbol=RELIANCE"
            onClick={() => {
              setTimeout(() => {
                window.dispatchEvent(new Event("symbolChanged"));
              }, 100);
            }}
            className="flex items-center justify-between border-b border-[#e7e7f3] pb-2 hover:bg-[#faf8ff] px-1 rounded transition-colors block cursor-pointer"
          >
            <div>
              <p className="font-mono text-xs font-bold text-[#191b23]">RELIANCE</p>
              <p className="text-[10px] text-[#737686]">2,945.50</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold text-[#bc4800]">+1.24%</p>
              <div className="w-12 h-4 overflow-hidden mt-1 opacity-70">
                <svg className="stroke-[#bc4800] fill-none stroke-2" viewBox="0 0 100 20">
                  <polyline points="0,15 20,10 40,18 60,5 80,8 100,2" />
                </svg>
              </div>
            </div>
          </Link>

          <Link
            href="/institutional-research?symbol=HDFCBANK"
            onClick={() => {
              setTimeout(() => {
                window.dispatchEvent(new Event("symbolChanged"));
              }, 100);
            }}
            className="flex items-center justify-between border-b border-[#e7e7f3] pb-2 hover:bg-[#faf8ff] px-1 rounded transition-colors block cursor-pointer"
          >
            <div>
              <p className="font-mono text-xs font-bold text-[#191b23]">HDFCBANK</p>
              <p className="text-[10px] text-[#737686]">1,452.10</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold text-[#ba1a1a]">-0.85%</p>
              <div className="w-12 h-4 overflow-hidden mt-1 opacity-70">
                <svg className="stroke-[#ba1a1a] fill-none stroke-2" viewBox="0 0 100 20">
                  <polyline points="0,5 20,8 40,2 60,15 80,12 100,18" />
                </svg>
              </div>
            </div>
          </Link>

          <Link
            href="/institutional-research?symbol=TCS"
            onClick={() => {
              setTimeout(() => {
                window.dispatchEvent(new Event("symbolChanged"));
              }, 100);
            }}
            className="flex items-center justify-between border-b border-[#e7e7f3] pb-2 hover:bg-[#faf8ff] px-1 rounded transition-colors block cursor-pointer"
          >
            <div>
              <p className="font-mono text-xs font-bold text-[#191b23]">TCS</p>
              <p className="text-[10px] text-[#737686]">3,890.00</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold text-[#bc4800]">+0.32%</p>
              <div className="w-12 h-4 overflow-hidden mt-1 opacity-70">
                <svg className="stroke-[#bc4800] fill-none stroke-2" viewBox="0 0 100 20">
                  <polyline points="0,10 25,12 50,5 75,8 100,5" />
                </svg>
              </div>
            </div>
          </Link>
        </div>

        {/* Dynamic Tickers added by user */}
        {watchlistTickers.map((ticker) => (
          <Link
            key={ticker}
            href={`/institutional-research?symbol=${ticker}`}
            onClick={() => {
              setTimeout(() => window.dispatchEvent(new Event("symbolChanged")), 100);
            }}
            className="flex items-center justify-between border-b border-[#e7e7f3] pb-2 hover:bg-[#faf8ff] px-1 rounded transition-colors block cursor-pointer"
          >
            <div>
              <p className="font-mono text-xs font-bold text-[#191b23]">{ticker}</p>
              <p className="text-[10px] text-[#737686]">Click to research</p>
            </div>
            <span className="material-symbols-outlined text-[#c3c6d7] !text-sm">arrow_forward</span>
          </Link>
        ))}

        {/* Settings Panel */}
        {showSettingsPanel && (
          <div className="mx-1 mb-3 bg-[#f3f3fe] border border-[#c3c6d7] rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[9px] text-[#191b23] uppercase font-bold tracking-wider">Terminal Settings</p>
              <button onClick={() => setShowSettingsPanel(false)} className="text-[#737686] hover:text-[#191b23]">
                <span className="material-symbols-outlined !text-sm">close</span>
              </button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#434655]">Theme</span>
                <span className="text-[10px] font-bold text-[#004ac6] font-mono">Light (Default)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#434655]">API Endpoint</span>
                <span className="text-[10px] font-bold text-[#191b23] font-mono">localhost:8000</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#434655]">Cache TTL</span>
                <span className="text-[10px] font-bold text-[#191b23] font-mono">120s</span>
              </div>
            </div>
          </div>
        )}

        {/* Profile Card */}
        <div className="mt-4 pt-4 border-t border-[#e7e7f3] flex items-center gap-3 px-1">
          <div className="w-9 h-9 rounded-full bg-[#d0e1fb] flex items-center justify-center text-[#004ac6] font-bold text-xs shrink-0 select-none">
            AS
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-[#191b23] truncate">Alex Sterling</p>
            <p className="text-[10px] text-[#434655] font-medium tracking-wide uppercase">Senior Quant</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
