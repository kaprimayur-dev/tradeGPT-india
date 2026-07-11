"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import CommandPalette from "@/components/CommandPalette";
import ShortcutsModal from "@/components/ShortcutsModal";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [collapsed, setCollapsed] = useState(false);
  
  // Modals state
  const [cmdOpen, setCmdOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Live ticking status states
  const [latency, setLatency] = useState(14);
  const [countdownStr, setCountdownStr] = useState("");
  const [marketStatus, setMarketStatus] = useState({ open: true, label: "Live" });
  const [usdinrPrice, setUsdinrPrice] = useState(83.52);
  const [usdinrChange, setUsdinrChange] = useState(-0.02);

  // Footer dynamic values loaded from localStorage
  const [openPositionsCount, setOpenPositionsCount] = useState(3);
  const [portfolioHealth, setPortfolioHealth] = useState(84);

  // Sync theme and sidebar from localStorage on mount
  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem("trade_theme");
    if (savedTheme === "dark") {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
    }

    const savedCollapsed = localStorage.getItem("trade_sidebar_collapsed");
    if (savedCollapsed === "true") {
      setCollapsed(true);
    }
  }, []);

  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("trade_theme", next);
    if (next === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    // Notify TradingView charts and components to re-render colors
    window.dispatchEvent(new Event("themeChanged"));
  };

  const toggleSidebar = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("trade_sidebar_collapsed", next ? "true" : "false");
  };

  // Live ticking intervals (latency, countdown, usdinr prices)
  useEffect(() => {
    if (!mounted) return;

    const timer = setInterval(() => {
      // 1. Latency fluctuation
      setLatency((prev) => {
        const delta = Math.floor((Math.random() - 0.5) * 6);
        return Math.max(8, Math.min(85, prev + delta));
      });

      // 2. USDINR price fluctuation
      setUsdinrPrice((prev) => {
        const delta = (Math.random() - 0.5) * 0.02;
        return parseFloat((prev + delta).toFixed(4));
      });

      // 3. IST Market countdown
      const now = new Date();
      const utc = now.getTime() + now.getTimezoneOffset() * 60000;
      const istOffset = 5.5 * 3600000;
      const istTime = new Date(utc + istOffset);
      const day = istTime.getDay();
      const hours = istTime.getHours();
      const minutes = istTime.getMinutes();
      const seconds = istTime.getSeconds();
      const timeValue = hours * 100 + minutes;

      const isWeekend = day === 0 || day === 6;
      const isMarketHours = timeValue >= 915 && timeValue <= 1530;

      if (isWeekend) {
        setMarketStatus({ open: false, label: "Closed" });
        setCountdownStr("Opens Mon 9:15 AM");
      } else if (!isMarketHours) {
        setMarketStatus({ open: false, label: "Closed" });
        if (timeValue < 915) {
          const hoursLeft = 9 - 1 - hours;
          const minsLeft = 60 + 15 - minutes;
          setCountdownStr(`Opens in ${hoursLeft}h ${minsLeft}m`);
        } else {
          setCountdownStr("Closed (Opens 9:15 AM)");
        }
      } else {
        setMarketStatus({ open: true, label: "Live" });
        const totalSecsRemaining = (15 * 3600 + 30 * 60) - (hours * 3600 + minutes * 60 + seconds);
        if (totalSecsRemaining > 0) {
          const h = Math.floor(totalSecsRemaining / 3600);
          const m = Math.floor((totalSecsRemaining % 3600) / 60);
          const s = totalSecsRemaining % 60;
          setCountdownStr(`Closes in ${h}h ${m}m ${s}s`);
        } else {
          setCountdownStr("Closing...");
        }
      }

      // 4. Reload watchlists values dynamically
      const savedWatchlist = localStorage.getItem("trade_watchlist");
      if (savedWatchlist) {
        try {
          setOpenPositionsCount(JSON.parse(savedWatchlist).length);
        } catch {}
      }
      const savedHealth = localStorage.getItem("trade_portfolio_health");
      if (savedHealth) {
        setPortfolioHealth(parseInt(savedHealth, 10));
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [mounted]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    if (!mounted) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }

      if (e.key === "?" && !e.shiftKey) {
        e.preventDefault();
        setShortcutsOpen((v) => !v);
      }

      if (e.key === "1") {
        e.preventDefault();
        router.push("/market-intelligence");
      } else if (e.key === "2") {
        e.preventDefault();
        router.push("/institutional-research");
      } else if (e.key === "3") {
        e.preventDefault();
        router.push("/portfolio-intelligence");
      } else if (e.key === "4") {
        e.preventDefault();
        router.push("/quantitative-strategy");
      }

      if (e.key.toLowerCase() === "t") {
        e.preventDefault();
        toggleTheme();
      }

      if (e.key.toLowerCase() === "r") {
        e.preventDefault();
        window.dispatchEvent(new Event("refreshData"));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mounted, theme, collapsed, router]);

  if (!mounted) {
    return (
      <div className="flex h-full w-full bg-canvas text-text-primary">
        <div className="w-[260px] h-full bg-surface-base border-r border-border-subtle shrink-0 animate-pulse"></div>
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
          <div className="h-14 bg-surface-base border-b border-border-subtle animate-pulse"></div>
          <div className="flex-1 bg-canvas p-6">{children}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full bg-canvas text-text-primary">
      {/* Dynamic Collapsible Left Sidebar */}
      <Sidebar collapsed={collapsed} onToggleCollapse={toggleSidebar} />

      {/* Right Main Container */}
      <div
        className="flex-1 flex flex-col h-screen overflow-hidden transition-all duration-300 ease-in-out"
        style={{ paddingLeft: collapsed ? "70px" : "260px" }}
      >
        {/* Dynamic Header */}
        <Header collapsed={collapsed} theme={theme} onToggleTheme={toggleTheme} onOpenSearch={() => setCmdOpen(true)} />

        {/* Page Workspace Wrapper */}
        <main className="flex-1 pt-14 pb-12 flex flex-col bg-canvas min-h-0 overflow-hidden">
          {children}
        </main>

        {/* Global Live System Status Bar */}
        <footer className="no-print h-12 border-t border-border-subtle bg-surface-base flex items-center px-6 gap-6 shrink-0 z-10 select-none text-xs text-text-muted">
          <div className="flex items-center gap-2 border-r border-border-subtle/50 pr-6">
            <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">USD/INR</span>
            <span className="font-mono text-xs font-bold text-text-primary">₹{usdinrPrice.toFixed(2)}</span>
            <span className={`text-[10px] font-bold ${usdinrChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
              ({usdinrChange >= 0 ? "+" : ""}{usdinrChange.toFixed(2)}%)
            </span>
          </div>

          <div className="flex items-center gap-2 border-r border-border-subtle/50 pr-6">
            <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Health Score</span>
            <div className="flex items-center gap-1">
              <div className={`w-1.5 h-1.5 rounded-full ${portfolioHealth >= 20 ? "bg-[#10b981]" : "bg-alert-red"}`}></div>
              <div className={`w-1.5 h-1.5 rounded-full ${portfolioHealth >= 40 ? "bg-[#10b981]" : "bg-alert-red"}`}></div>
              <div className={`w-1.5 h-1.5 rounded-full ${portfolioHealth >= 60 ? "bg-[#10b981]" : "bg-alert-red"}`}></div>
              <div className={`w-1.5 h-1.5 rounded-full ${portfolioHealth >= 80 ? "bg-[#10b981]" : "bg-alert-red"}`}></div>
              <div className={`w-1.5 h-1.5 rounded-full ${portfolioHealth >= 90 ? "bg-[#10b981]" : "bg-border-subtle"}`}></div>
              <span className="text-[11px] font-bold text-text-primary ml-1">{portfolioHealth}/100</span>
            </div>
          </div>

          <div className="flex items-center gap-6 overflow-hidden text-xs">
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Margin</span>
              <span className="font-bold text-text-primary">₹8.4L Available</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Open Positions</span>
              <span className="font-bold text-text-primary">{openPositionsCount} Active</span>
            </div>
            
            <div className="flex items-center gap-2 border-l border-border-subtle/50 pl-6">
              <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Market Status</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${marketStatus.open ? "bg-[#10b981] animate-pulse" : "bg-[#ba1a1a]"}`}></span>
                <span className="font-mono text-[10px] font-bold text-text-primary">{countdownStr || "Ticking..."}</span>
              </div>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-5 text-[11px] font-mono">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
              <span className="font-semibold text-text-muted">Mum-1</span>
            </div>
            <span className="font-semibold text-text-muted">Latency: {latency}ms</span>
          </div>
        </footer>
      </div>

      {/* Overlays */}
      <CommandPalette isOpen={cmdOpen} onClose={() => setCmdOpen(false)} onToggleTheme={toggleTheme} />
      <ShortcutsModal isOpen={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
    </div>
  );
}
