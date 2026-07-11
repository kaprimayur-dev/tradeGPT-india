"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onToggleTheme: () => void;
}

export default function CommandPalette({ isOpen, onClose, onToggleTheme }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = [
    { id: "nav-market", title: "Go to Market Intelligence", category: "Navigation", icon: "monitoring", action: () => router.push("/market-intelligence") },
    { id: "nav-research", title: "Go to RAG Stock Research", category: "Navigation", icon: "search_insights", action: () => router.push("/institutional-research") },
    { id: "nav-portfolio", title: "Go to Portfolio Intelligence", category: "Navigation", icon: "account_balance_wallet", action: () => router.push("/portfolio-intelligence") },
    { id: "nav-quant", title: "Go to Quantitative Strategy Lab", category: "Navigation", icon: "analytics", action: () => router.push("/quantitative-strategy") },
    { id: "nav-settings", title: "Go to System Settings", category: "Navigation", icon: "settings", action: () => router.push("/settings") },
    { id: "action-theme", title: "Toggle Bloomberg Dark Mode", category: "Actions", icon: "dark_mode", action: onToggleTheme },
    { id: "action-clear", title: "Clear Watchlist Tickers", category: "Actions", icon: "delete_sweep", action: () => { localStorage.removeItem("trade_watchlist"); window.location.reload(); } },
    { id: "sym-reliance", title: "Analyze RELIANCE (Reliance Industries)", category: "Stocks", icon: "trending_up", action: () => router.push("/institutional-research?symbol=RELIANCE") },
    { id: "sym-tcs", title: "Analyze TCS (Tata Consultancy Services)", category: "Stocks", icon: "trending_up", action: () => router.push("/institutional-research?symbol=TCS") },
    { id: "sym-hdfc", title: "Analyze HDFCBANK (HDFC Bank)", category: "Stocks", icon: "trending_up", action: () => router.push("/institutional-research?symbol=HDFCBANK") },
    { id: "sym-infy", title: "Analyze INFY (Infosys Limited)", category: "Stocks", icon: "trending_up", action: () => router.push("/institutional-research?symbol=INFY") },
  ];

  const filtered = commands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Handle keyboard navigation inside command palette
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].action();
          onClose();
        }
      } else if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-[#090a0f]/40 dark:bg-black/60 backdrop-blur-[2px]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-surface-base border border-border-subtle shadow-2xl rounded-xl overflow-hidden flex flex-col max-h-[400px] mx-4 animate-in fade-in zoom-in-95 duration-100"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border-subtle bg-canvas">
          <span className="material-symbols-outlined text-text-muted">search</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search symbol (e.g. RELIANCE)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted/60 outline-none"
          />
          <span className="text-[10px] font-bold font-mono px-2 py-1 bg-surface-elevation text-text-muted border border-border-subtle rounded">
            ESC
          </span>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar py-2">
          {filtered.length > 0 ? (
            Object.entries(
              filtered.reduce<Record<string, typeof commands>>((acc, item) => {
                acc[item.category] = acc[item.category] || [];
                acc[item.category].push(item);
                return acc;
              }, {})
            ).map(([category, items]) => (
              <div key={category} className="mb-2">
                <p className="px-4 py-1 text-[9px] font-bold text-text-muted/50 uppercase tracking-widest bg-canvas/30">
                  {category}
                </p>
                <div className="mt-1">
                  {items.map((item) => {
                    const globalIdx = filtered.indexOf(item);
                    const isSelected = globalIdx === selectedIndex;
                    return (
                      <div
                        key={item.id}
                        onClick={() => {
                          item.action();
                          onClose();
                        }}
                        className={`flex items-center gap-3 px-4 py-2 text-xs font-semibold cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-primary text-white"
                            : "text-text-primary hover:bg-canvas"
                        }`}
                      >
                        <span className={`material-symbols-outlined !text-base ${isSelected ? "text-white" : "text-text-muted"}`}>
                          {item.icon}
                        </span>
                        <span className="flex-1 truncate">{item.title}</span>
                        {isSelected && (
                          <span className="text-[10px] font-bold text-white/80 font-mono">ENTER</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-xs text-text-muted italic py-6">No matching commands or symbols found</p>
          )}
        </div>
      </div>
    </div>
  );
}
