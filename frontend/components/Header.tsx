"use client";

import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

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
          <div className="relative cursor-pointer group">
            <span className="material-symbols-outlined text-[#434655] group-hover:text-[#004ac6] transition-colors !text-[1.25rem]">
              notifications
            </span>
            <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-[#ba1a1a] rounded-full"></span>
          </div>
          <span className="material-symbols-outlined text-[#434655] hover:text-[#004ac6] cursor-pointer transition-colors !text-[1.25rem]">
            settings
          </span>
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
            <span className="font-display text-lg tracking-tight text-[#004ac6] font-bold">RELIANCE</span>
            <span className="px-1.5 py-0.5 bg-[#e7e7f3] text-[9px] font-bold rounded border border-[#c3c6d7]">NSE</span>
          </div>
          <div className="flex items-center gap-5 text-xs whitespace-nowrap">
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Price</span>
              <span className="font-bold text-[#191b23] font-mono">
                ₹2,984.45 <span className="text-[#ba1a1a] text-[10px] font-semibold">-0.42%</span>
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Mkt Cap</span>
              <span className="font-semibold text-[#434655] font-mono">20.21T</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">P/E (TTM)</span>
              <span className="font-semibold text-[#434655] font-mono">28.4x</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-[#737686] uppercase font-bold leading-tight">Beta</span>
              <span className="font-semibold text-[#434655] font-mono">0.92</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center border border-[#c3c6d7] rounded-lg px-3 py-1 bg-[#f3f3fe]">
            <span className="material-symbols-outlined text-[#737686] !text-sm mr-2">search</span>
            <input
              type="text"
              placeholder="Search instruments..."
              className="bg-transparent border-none p-0 text-xs text-[#191b23] w-36 focus:outline-none focus:ring-0"
              readOnly
              value="RELIANCE"
            />
          </div>
          <div className="flex items-center gap-1">
            <button className="p-1.5 text-[#434655] hover:bg-[#f3f3fe] rounded-full transition-colors">
              <span className="material-symbols-outlined !text-[1.25rem]">notifications</span>
            </button>
            <button className="p-1.5 text-[#434655] hover:bg-[#f3f3fe] rounded-full transition-colors">
              <span className="material-symbols-outlined !text-[1.25rem]">history</span>
            </button>
          </div>
          <button className="px-4 py-1.5 bg-[#004ac6] text-white rounded-lg text-xs font-semibold active:opacity-90 transition-opacity">
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
            NIFTY: 22,450.20 (+0.45%)
          </span>
          <span className="font-mono hover:text-[#191b23] transition-colors cursor-pointer">
            SENSEX: 73,810.15 (+0.38%)
          </span>
          <span className="font-mono hover:text-[#191b23] transition-colors cursor-pointer">
            USDINR: 83.12 (-0.02%)
          </span>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1 border-r border-[#c3c6d7] pr-4">
          <span className="material-symbols-outlined text-[#434655] cursor-pointer hover:text-[#191b23] transition-colors !text-[1.25rem] p-1">
            notifications
          </span>
          <span className="material-symbols-outlined text-[#434655] cursor-pointer hover:text-[#191b23] transition-colors !text-[1.25rem] p-1">
            history
          </span>
          <span className="material-symbols-outlined text-[#434655] cursor-pointer hover:text-[#191b23] transition-colors !text-[1.25rem] p-1">
            help_outline
          </span>
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
