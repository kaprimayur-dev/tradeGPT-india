"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api, MarketDataResponse } from "../api";
import { createChart, CandlestickSeries, HistogramSeries, CrosshairMode, IChartApi, ISeriesApi, LineStyle } from "lightweight-charts";
import type { CandlestickData, HistogramData, Time, MouseEventParams } from "lightweight-charts";

const getMarketStatus = () => {
  const now = new Date();
  const utc = now.getTime() + now.getTimezoneOffset() * 60000;
  const istOffset = 5.5 * 3600000;
  const istTime = new Date(utc + istOffset);
  
  const day = istTime.getDay();
  const hours = istTime.getHours();
  const minutes = istTime.getMinutes();
  const timeValue = hours * 100 + minutes;
  
  const isWeekend = day === 0 || day === 6;
  const isMarketHours = timeValue >= 915 && timeValue <= 1530;
  
  if (isWeekend) {
    return { open: false, label: "Market Closed (Weekend)" };
  } else if (!isMarketHours) {
    return { open: false, label: "Market Closed (Opens 9:15 AM IST)" };
  }
  return { open: true, label: "Market Live" };
};

export default function MarketIntelligencePage() {
  const marketStatus = getMarketStatus();
  const [selectedInterval, setSelectedInterval] = useState("15M");
  const [niftyPrice, setNiftyPrice] = useState<number | null>(null);
  const [priceChange, setPriceChange] = useState<number | null>(null);
  
  const [sensexPrice, setSensexPrice] = useState<number | null>(null);
  const [sensexChange, setSensexChange] = useState<number | null>(null);

  const [selectedIndex, setSelectedIndex] = useState<"NIFTY" | "SENSEX">("NIFTY");
  const [isIndexDropdownOpen, setIsIndexDropdownOpen] = useState(false);

  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");
  const [orderSubmitted, setOrderSubmitted] = useState<string | null>(null);
  const [showFullscreenHint, setShowFullscreenHint] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [usdinrPrice, setUsdinrPrice] = useState<number | null>(null);
  const [usdinrChange, setUsdinrChange] = useState<number | null>(null);
  const [hoveredCandle, setHoveredCandle] = useState<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
    change: number;
  } | null>(null);
  const [countdownStr, setCountdownStr] = useState("");
  const [latency, setLatency] = useState<number>(14);

  const [openPositionsCount, setOpenPositionsCount] = useState(3);
  const [portfolioHealth, setPortfolioHealth] = useState(84);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    if (typeof window !== "undefined") {
      const savedWatchlist = localStorage.getItem("trade_watchlist");
      if (savedWatchlist) {
        try {
          setOpenPositionsCount(JSON.parse(savedWatchlist).length);
        } catch (e) {
          console.error("Failed to parse watchlist", e);
        }
      }
      const savedHealth = localStorage.getItem("trade_portfolio_health");
      if (savedHealth) {
        setPortfolioHealth(parseInt(savedHealth, 10));
      }

      // Pre-hydrate market data from localStorage cache if present
      const cache = localStorage.getItem("tradeGPT_market_data_cache");
      if (cache) {
        try {
          const parsed = JSON.parse(cache);
          if (parsed && parsed.success && parsed.status !== "unavailable") {
            setMarketData(parsed);
            if (parsed.indices) {
              if (parsed.indices["NIFTY"]) {
                setNiftyPrice(typeof parsed.indices["NIFTY"].price === "number" ? parsed.indices["NIFTY"].price : null);
                setPriceChange(typeof parsed.indices["NIFTY"].change === "number" ? parsed.indices["NIFTY"].change : null);
              }
              if (parsed.indices["SENSEX"]) {
                setSensexPrice(typeof parsed.indices["SENSEX"].price === "number" ? parsed.indices["SENSEX"].price : null);
                setSensexChange(typeof parsed.indices["SENSEX"].change === "number" ? parsed.indices["SENSEX"].change : null);
              }
              if (parsed.indices["USDINR"]) {
                setUsdinrPrice(typeof parsed.indices["USDINR"].price === "number" ? parsed.indices["USDINR"].price : null);
                setUsdinrChange(typeof parsed.indices["USDINR"].change === "number" ? parsed.indices["USDINR"].change : null);
              }
            }
          }
        } catch (e) {
          console.warn("Failed to parse market cache on mount:", e);
        }
      }
    }
  }, []);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const timeframeMapping: Record<string, { interval: string; period: string }> = {
    "1M": { interval: "1m", period: "1d" },
    "5M": { interval: "5m", period: "5d" },
    "15M": { interval: "15m", period: "5d" },
    "1H": { interval: "1h", period: "30d" },
    "1D": { interval: "1d", period: "30d" },
  };

  const loadData = async (timeframe: string = selectedInterval, silent: boolean = false) => {
    // If we have cached/loaded data, run silently in background
    const isSilent = silent || !!marketData;
    if (!isSilent) setLoading(true);
    setError(null);
    const startTime = Date.now();
    try {
      const mapping = timeframeMapping[timeframe] || { interval: "1d", period: "30d" };
      const data = await api.getMarketData(mapping.interval, mapping.period);
      if (data.success) {
        setMarketData(data);
        if (typeof window !== "undefined" && data.status !== "unavailable") {
          localStorage.setItem("tradeGPT_market_data_cache", JSON.stringify(data));
        }
        if (data.indices) {
          if (data.indices["NIFTY"]) {
            setNiftyPrice(typeof data.indices["NIFTY"].price === "number" ? data.indices["NIFTY"].price : null);
            setPriceChange(typeof data.indices["NIFTY"].change === "number" ? data.indices["NIFTY"].change : null);
          }
          if (data.indices["SENSEX"]) {
            setSensexPrice(typeof data.indices["SENSEX"].price === "number" ? data.indices["SENSEX"].price : null);
            setSensexChange(typeof data.indices["SENSEX"].change === "number" ? data.indices["SENSEX"].change : null);
          }
          if (data.indices["USDINR"]) {
            setUsdinrPrice(typeof data.indices["USDINR"].price === "number" ? data.indices["USDINR"].price : null);
            setUsdinrChange(typeof data.indices["USDINR"].change === "number" ? data.indices["USDINR"].change : null);
          }
        }
      }
      setLatency(Date.now() - startTime);
    } catch (err: unknown) {
      const e = err as Error;
      if (!isSilent) setError(e.message || "Failed to load live market data");
    } finally {
      if (!isSilent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedInterval, false);

    const handleRefresh = () => {
      loadData(selectedInterval, false);
    };
    window.addEventListener("refreshData", handleRefresh);
    return () => window.removeEventListener("refreshData", handleRefresh);
  }, [selectedInterval]);

  // Periodic background refresh every 60s without simulated ticks
  useEffect(() => {
    const pollInterval = setInterval(() => {
      loadData(selectedInterval, true);
    }, 60000);
    return () => clearInterval(pollInterval);
  }, [selectedInterval]);

  // Dynamic ticking countdown for market opens/closes in IST
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const utc = now.getTime() + now.getTimezoneOffset() * 60000;
      const istOffset = 5.5 * 3600000;
      const istTime = new Date(utc + istOffset);
      
      const day = istTime.getDay();
      const hours = istTime.getHours();
      const minutes = istTime.getMinutes();
      
      const isWeekend = day === 0 || day === 6;
      let targetTime = new Date(istTime);
      let isToClose = false;
      
      if (isWeekend) {
        const daysToAdd = day === 0 ? 1 : 2;
        targetTime.setDate(targetTime.getDate() + daysToAdd);
        targetTime.setHours(9, 15, 0, 0);
      } else {
        const timeValue = hours * 100 + minutes;
        if (timeValue < 915) {
          targetTime.setHours(9, 15, 0, 0);
        } else if (timeValue < 1530) {
          targetTime.setHours(15, 30, 0, 0);
          isToClose = true;
        } else {
          const daysToAdd = day === 5 ? 3 : 1;
          targetTime.setDate(targetTime.getDate() + daysToAdd);
          targetTime.setHours(9, 15, 0, 0);
        }
      }
      
      const diffMs = targetTime.getTime() - istTime.getTime();
      if (diffMs <= 0) {
        setCountdownStr("00:00:00");
        return;
      }
      
      const totalSecs = Math.floor(diffMs / 1000);
      const h = Math.floor(totalSecs / 3600);
      const m = Math.floor((totalSecs % 3600) / 60);
      const s = totalSecs % 60;
      
      const hStr = h.toString().padStart(2, "0");
      const mStr = m.toString().padStart(2, "0");
      const sStr = s.toString().padStart(2, "0");
      
      setCountdownStr(`${isToClose ? "Closes" : "Opens"} in ${hStr}:${mStr}:${sStr}`);
    };
    
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleTimeframeChange = async (tf: string) => {
    setSelectedInterval(tf);
    await loadData(tf, false);
  };

  const timeframes = ["1M", "5M", "15M", "1H", "1D"];

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const container = chartContainerRef.current;
    
    // Create chart
    const chart = createChart(container, {
      layout: {
        background: { color: '#ffffff' },
        textColor: '#191b23',
        fontSize: 10,
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      grid: {
        vertLines: { color: '#f3f3fe' },
        horzLines: { color: '#f3f3fe' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#004ac6',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#004ac6',
        },
        horzLine: {
          color: '#004ac6',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#004ac6',
        },
      },
      rightPriceScale: {
        borderColor: '#c3c6d7',
        visible: true,
      },
      timeScale: {
        borderColor: '#c3c6d7',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 3,
        barSpacing: 12,
        minBarSpacing: 4,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ba1a1a',
      borderUpColor: '#10b981',
      borderDownColor: '#ba1a1a',
      wickUpColor: '#10b981',
      wickDownColor: '#ba1a1a',
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#004ac6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // overlay
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Load data
    const rawCandles = marketData?.history?.[selectedIndex] || [];
    const parsedData = rawCandles.map((c) => {
      const dtStr = c.date.includes(" ") ? c.date.replace(" ", "T") : c.date;
      const ts = Math.floor(Date.parse(dtStr) / 1000);
      return {
        time: (isNaN(ts) ? c.date : ts) as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
        volume: c.volume,
        rawDate: c.date,
      };
    });

    // filter out duplicates/decreasing timestamps
    const uniqueCandles: typeof parsedData = [];
    let lastTimeNum = 0;
    for (const item of parsedData) {
      const tNum = typeof item.time === 'number' ? item.time : Date.parse(item.time as string) / 1000;
      if (!isNaN(tNum) && tNum > lastTimeNum) {
        uniqueCandles.push(item);
        lastTimeNum = tNum;
      }
    }

    if (uniqueCandles.length > 0) {
      candleSeries.setData(uniqueCandles.map(c => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })));

      volumeSeries.setData(uniqueCandles.map(c => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.4)' : 'rgba(186, 26, 26, 0.4)',
      })));

      // Auto-fit content and adjust zoom to look professional immediately
      chart.timeScale().fitContent();
    }

    // Subscribe to crosshair move
    chart.subscribeCrosshairMove((param: MouseEventParams) => {
      if (
        !param.point ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > container.clientWidth ||
        param.point.y < 0 ||
        param.point.y > container.clientHeight
      ) {
        setHoveredCandle(null);
      } else {
        const candleData = param.seriesData.get(candleSeries) as CandlestickData;
        const volumeData = param.seriesData.get(volumeSeries) as any;
        if (candleData) {
          // Find matching original date
          const matched = uniqueCandles.find(c => {
            if (typeof c.time === 'number' && typeof param.time === 'number') {
              return c.time === param.time;
            }
            return String(c.time) === String(param.time);
          });
          const rawDate = matched ? matched.rawDate : String(param.time);
          const chg = candleData.open ? ((candleData.close - candleData.open) / candleData.open) * 100 : 0;
          setHoveredCandle({
            time: rawDate,
            open: candleData.open,
            high: candleData.high,
            low: candleData.low,
            close: candleData.close,
            volume: volumeData ? volumeData.value : undefined,
            change: chg,
          });
        }
      }
    });

    // Resize handler
    const handleResize = () => {
      chart.resize(container.clientWidth, container.clientHeight);
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      if (chartRef.current) {
        try {
          chart.remove();
        } catch (e) {
          console.warn("Chart remove warning:", e);
        }
      }
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [marketData, selectedIndex]);

  const rawCandles = marketData?.history?.[selectedIndex] || [];
  const lastCandle = rawCandles[rawCandles.length - 1];

  const lastVolume = lastCandle && lastCandle.volume ? (lastCandle.volume / 1000000).toFixed(2) + "M" : "—";


  const formatRelativeTime = (dateStr: string) => {
    if (!dateStr || dateStr === "N/A") return "—";
    try {
      const date = new Date(dateStr.replace(" ", "T"));
      if (isNaN(date.getTime())) return dateStr;
      
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);
      const diffHours = Math.floor(diffMins / 60);
      
      if (diffSecs < 60) {
        return "Just now";
      } else if (diffMins < 60) {
        return `${diffMins}m ago`;
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else if (diffHours < 48) {
        return "Yesterday";
      } else {
        return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      }
    } catch {
      return dateStr;
    }
  };


  const currentIndexPrice = selectedIndex === "NIFTY" ? niftyPrice : sensexPrice;
  const currentIndexChange = selectedIndex === "NIFTY" ? priceChange : sensexChange;


  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#faf8ff] h-full px-6">
        <div className="bg-white border border-[#ba1a1a] rounded-xl p-6 max-w-md w-full shadow-md text-center">
          <span className="material-symbols-outlined text-[#ba1a1a] !text-4xl mb-3">error_outline</span>
          <h3 className="font-display font-bold text-base text-[#191b23] mb-1">Terminal Connection Error</h3>
          <p className="text-xs text-[#737686] mb-4 leading-normal">{error}</p>
          <button
            onClick={() => loadData(selectedInterval, false)}
            className="px-4 py-2 bg-[#004ac6] hover:bg-[#003ea8] text-white text-xs font-semibold rounded-lg transition-colors active:scale-95 duration-100"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden h-full font-body">
      {/* Truthfulness & Data Integrity Status Banner */}
      {marketData?.status && marketData.status !== "available" && (
        <div className={`px-4 py-2 text-xs font-medium flex items-center justify-between border-b shrink-0 ${
          marketData.status === "unavailable"
            ? "bg-amber-50 text-amber-950 border-amber-200"
            : "bg-blue-50 text-blue-950 border-blue-200"
        }`}>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined !text-base text-amber-600">
              {marketData.status === "unavailable" ? "cloud_off" : "warning"}
            </span>
            <span>
              {marketData.status === "unavailable"
                ? "Live market feed currently unavailable from primary provider. Synthetic fallbacks are disabled to ensure financial integrity."
                : "Degraded market feed: Some index feeds or market breadth components are currently unresolvable."}
            </span>
          </div>
          {marketData.as_of && (
            <span className="text-[10px] font-mono opacity-80">
              Source: {marketData.source || "Yahoo Finance"} • As of: {new Date(marketData.as_of).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      {/* Dynamic Workspace Container */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        
        {/* Center Stage: Charting Area */}
        <section className="flex-1 flex flex-col border-r border-[#c3c6d7] bg-white min-h-0">
          
          {/* Chart Toolbar */}
          <div className="h-10 border-b border-[#c3c6d7] flex items-center px-4 justify-between bg-[#faf8ff]">
            <div className="flex items-center gap-4">
              
              {/* Index Switcher Dropdown */}
              <div className="relative">
                <div 
                  onClick={() => setIsIndexDropdownOpen(!isIndexDropdownOpen)}
                  className="flex items-center gap-1 border-r border-[#c3c6d7] pr-4 cursor-pointer hover:text-[#004ac6] transition-colors"
                >
                  <span className="text-xs font-bold text-[#191b23]">
                    {selectedIndex === "NIFTY" ? "NIFTY 50" : "SENSEX"}
                  </span>
                  <span className="material-symbols-outlined text-[#737686] !text-sm">expand_more</span>
                </div>
                {isIndexDropdownOpen && (
                  <div className="absolute top-8 left-0 bg-white border border-[#c3c6d7] rounded shadow-lg z-30 py-1 w-28 text-xs font-semibold">
                    <div 
                      onClick={() => {
                        setSelectedIndex("NIFTY");
                        setIsIndexDropdownOpen(false);
                      }}
                      className="px-3 py-2 hover:bg-[#f3f3fe] cursor-pointer"
                    >
                      NIFTY 50
                    </div>
                    <div 
                      onClick={() => {
                        setSelectedIndex("SENSEX");
                        setIsIndexDropdownOpen(false);
                      }}
                      className="px-3 py-2 hover:bg-[#f3f3fe] cursor-pointer"
                    >
                      SENSEX
                    </div>
                  </div>
                )}
              </div>

              {/* Live Ticking Index Price */}
              <div className="flex items-baseline gap-2 border-r border-[#c3c6d7] pr-4">
                <span className="font-mono text-sm font-bold text-[#191b23]">
                  {typeof currentIndexPrice === "number" ? currentIndexPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
                </span>
                <span className={`font-mono text-[11px] font-bold ${typeof currentIndexChange === "number" ? (currentIndexChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]") : "text-[#737686]"}`}>
                  {typeof currentIndexChange === "number" ? `${currentIndexChange >= 0 ? "+" : ""}${currentIndexChange.toFixed(2)}%` : "—"}
                </span>
              </div>
              
              <div className="flex items-center gap-3 text-[11px] font-bold text-[#434655]">
                {timeframes.map((tf) => (
                  <span
                    key={tf}
                    onClick={() => handleTimeframeChange(tf)}
                    className={`cursor-pointer pb-0.5 transition-all ${
                      selectedInterval === tf
                        ? "text-[#004ac6] border-b-2 border-[#004ac6]"
                        : "hover:text-[#191b23]"
                    }`}
                  >
                    {tf}
                  </span>
                ))}
              </div>
              
              <div className="h-4 w-px bg-[#c3c6d7]"></div>
              
              <div className="flex items-center gap-3 text-[#434655]">
                <span className="material-symbols-outlined !text-[1.1rem] hover:text-[#191b23] cursor-pointer">
                  candlestick_chart
                </span>
                <span className="material-symbols-outlined !text-[1.1rem] hover:text-[#191b23] cursor-pointer">
                  add_circle
                </span>
                <span className="material-symbols-outlined !text-[1.1rem] hover:text-[#191b23] cursor-pointer">
                  show_chart
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-[#737686]/60 tracking-wider uppercase font-mono">
                VOL: {lastVolume}
              </span>
              <span
                onClick={() => setIsIndexDropdownOpen(!isIndexDropdownOpen)}
                className="material-symbols-outlined text-[#737686] hover:text-[#191b23] cursor-pointer !text-base"
                title="Chart Settings"
              >
                settings
              </span>
              {showFullscreenHint && (
                <div className="absolute right-0 top-8 bg-[#191b23] text-white text-[10px] font-mono px-2.5 py-1.5 rounded shadow-lg z-20 whitespace-nowrap">
                  Press F11 for browser fullscreen
                </div>
              )}
              <span 
                onClick={() => {
                  setShowFullscreenHint(true);
                  setTimeout(() => setShowFullscreenHint(false), 2500);
                }}
                className="material-symbols-outlined text-[#737686] hover:text-[#191b23] cursor-pointer !text-base"
                title="Fullscreen (Press F11)"
              >
                fullscreen
              </span>
            </div>
          </div>

          <div className="flex-1 relative overflow-hidden flex flex-col min-h-0">
            {/* Chart Container for Lightweight Charts */}
            <div ref={chartContainerRef} className="w-full h-full flex-1 relative min-h-0" />
            
            {loading && !marketData && (
              <div className="absolute inset-0 bg-white z-20 p-6 flex flex-col justify-between pointer-events-none select-none">
                <div className="flex-1 border-b border-l border-slate-200/80 relative bg-slate-50/30 rounded p-4 flex flex-col justify-between animate-pulse">
                  <div className="w-full h-[1px] bg-slate-100"></div>
                  <div className="w-full h-[1px] bg-slate-100"></div>
                  <div className="w-full h-[1px] bg-slate-100"></div>
                  <div className="w-full h-[1px] bg-slate-100"></div>
                </div>
              </div>
            )}

            {!loading && (!marketData || marketData.status === "unavailable" || rawCandles.length === 0) && (
              <div className="absolute inset-0 bg-[#faf8ff]/90 z-20 p-6 flex flex-col items-center justify-center text-center select-none">
                <span className="material-symbols-outlined text-[#737686] !text-4xl mb-2">query_stats</span>
                <p className="text-sm font-bold text-[#191b23]">Candlestick Data Unavailable</p>
                <p className="text-xs text-[#737686] max-w-sm mt-1">
                  Historical candles could not be resolved from the market data provider. Synthetic price movements are disabled.
                </p>
              </div>
            )}
            
            {/* Floating Live Data Tooltip */}
            {(() => {
              const activeData = hoveredCandle || (lastCandle ? {
                time: lastCandle.date,
                open: lastCandle.open,
                high: lastCandle.high,
                low: lastCandle.low,
                close: lastCandle.close,
                volume: lastCandle.volume,
                change: lastCandle.open ? ((lastCandle.close - lastCandle.open) / lastCandle.open) * 100 : (typeof currentIndexChange === "number" ? currentIndexChange : 0)
              } : null);

              if (!activeData) return null;

              const hasChange = typeof activeData.change === "number";
              const isPositive = hasChange && (activeData.change as number) > 0;
              const isFlat = !hasChange || activeData.change === 0;

              return (
                <div className="absolute top-4 left-4 bg-white/90 border border-[#c3c6d7] p-2.5 rounded shadow-sm backdrop-blur-sm z-10 max-w-[240px] pointer-events-none select-none">
                  <p className="text-[9px] font-bold text-[#737686] uppercase tracking-wide mb-1 font-mono">
                    DATA: {activeData.time}
                  </p>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-[11px]">
                    <span className="text-[#434655]">O: <span className="font-semibold text-[#191b23]">{typeof activeData.open === "number" ? activeData.open.toFixed(2) : "—"}</span></span>
                    <span className="text-[#434655]">H: <span className="font-semibold text-[#191b23]">{typeof activeData.high === "number" ? activeData.high.toFixed(2) : "—"}</span></span>
                    <span className="text-[#434655]">L: <span className="font-semibold text-[#191b23]">{typeof activeData.low === "number" ? activeData.low.toFixed(2) : "—"}</span></span>
                    <span className="text-[#434655]">C: <span className="font-semibold text-[#004ac6]">{typeof activeData.close === "number" ? activeData.close.toFixed(2) : "—"}</span></span>
                    <span className="col-span-2 text-[#434655] mt-0.5 pt-0.5 border-t border-[#e7e7f3] flex justify-between">
                      <span>CHG:</span> 
                      <span className={`font-semibold ${isFlat ? "text-[#737686]" : (isPositive ? "text-[#10b981]" : "text-[#ba1a1a]")}`}>
                        {hasChange ? (isFlat ? "—" : `${isPositive ? "+" : ""}${(activeData.change as number).toFixed(2)}%`) : "—"}
                      </span>
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>
        </section>

        {/* Right Rail: Breadth & Live Feed */}
        <aside className="w-80 flex flex-col bg-white shrink-0 overflow-hidden border-l border-[#c3c6d7] min-h-0">
          
          {/* Heatmap Breadth */}
          <div className="p-4 border-b border-[#c3c6d7]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider">Market Breadth</h3>
              {marketData ? (
                marketData.breadth.status === "unavailable" || marketData.breadth.advancing === null ? (
                  <span className="text-[10px] text-[#737686] font-mono">
                    Unavailable
                  </span>
                ) : (
                  <span className="text-[10px] text-[#10b981] font-bold font-mono">
                    {marketData.breadth.advancing} ADV / {marketData.breadth.declining || 0} DEC
                  </span>
                )
              ) : (
                <div className="w-20 h-3.5 bg-slate-100 rounded animate-pulse"></div>
              )}
            </div>
            {!marketData ? (
              <div className="grid grid-cols-5 gap-1 animate-pulse">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div key={idx} className="aspect-square rounded-sm bg-slate-200/60"></div>
                ))}
              </div>
            ) : marketData.breadth.status === "unavailable" || marketData.breadth.advancing === null ? (
              <div className="grid grid-cols-5 gap-1">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div key={idx} className="aspect-square rounded-sm bg-slate-200/50" title="Breadth data unavailable"></div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-5 gap-1">
                {Array.from({ length: 10 }).map((_, idx) => {
                  const adv = marketData.breadth.advancing || 0;
                  const dec = marketData.breadth.declining || 0;
                  const total = adv + dec;
                  const ratio = total > 0 ? adv / total : 0.5;
                  const isGreen = idx < Math.round(ratio * 10);
                  return (
                    <div
                      key={idx}
                      className={`aspect-square rounded-sm hover:opacity-90 transition-opacity ${
                        isGreen ? "bg-[#10b981]" : "bg-[#ba1a1a]"
                      }`}
                    ></div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Sector Performance */}
          <div className="p-4 border-b border-[#c3c6d7]">
            <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider mb-3">Sector Performance</h3>
            {!marketData ? (
              <div className="space-y-3.5 animate-pulse">
                {Array.from({ length: 6 }).map((_, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="h-3 bg-slate-200/70 rounded w-24"></div>
                    <div className="flex-1 h-2 bg-slate-100/80 rounded"></div>
                    <div className="h-3 bg-slate-200/70 rounded w-8"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3 max-h-[160px] overflow-y-auto custom-scrollbar pr-1">
                {marketData.sectors.map((sec, idx) => {
                  const hasChange = typeof sec.change === "number";
                  const isPositive = hasChange && (sec.change as number) >= 0;
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <span className="text-xs font-semibold text-[#434655] flex-1 truncate uppercase">{sec.name}</span>
                      <div className="w-20 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden shrink-0">
                        {hasChange ? (
                          <div 
                            className={`h-full ${isPositive ? "bg-[#10b981]" : "bg-[#ba1a1a]"}`} 
                            style={{ width: `${Math.min(100, Math.max(15, Math.abs(sec.change as number) * 20))}%` }}
                          ></div>
                        ) : (
                          <div className="h-full bg-slate-200 w-full"></div>
                        )}
                      </div>
                      <span className={`text-[10px] font-mono font-bold w-10 text-right shrink-0 ${hasChange ? (isPositive ? "text-[#10b981]" : "text-[#ba1a1a]") : "text-[#737686]"}`}>
                        {hasChange ? `${isPositive ? "+" : ""}${(sec.change as number).toFixed(2)}%` : "—"}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Live Institutional Wire Feed */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 bg-[#f3f3fe] border-b border-[#c3c6d7] flex items-center justify-between">
              <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider">Institutional Feed</h3>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${marketStatus.open ? "bg-[#10b981] animate-pulse" : "bg-[#ba1a1a]"}`}></span>
                <span className="text-[9px] uppercase tracking-widest text-[#737686] font-bold font-mono">
                  {marketStatus.label}
                </span>
              </div>
            </div>
            
            {!marketData ? (
              <div className="flex-1 overflow-y-auto divide-y divide-[#e7e7f3] animate-pulse">
                {Array.from({ length: 4 }).map((_, idx) => (
                  <div key={idx} className="p-3.5 space-y-2">
                    <div className="flex justify-between items-center">
                      <div className="h-3 bg-slate-200/70 rounded w-16"></div>
                      <div className="h-3 bg-slate-100/80 rounded w-12"></div>
                    </div>
                    <div className="h-4 bg-slate-300/60 rounded w-full"></div>
                    <div className="h-3 bg-slate-200/70 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-[#e7e7f3]">
                {marketData.news.map((item, idx) => (
                  <a 
                    key={idx}
                    href={item.link && item.link !== "N/A" ? item.link : undefined}
                    target={item.link && item.link !== "N/A" ? "_blank" : undefined}
                    rel="noopener noreferrer"
                    className={`p-3.5 hover:bg-[#faf8ff] transition-all block border-b border-[#e7e7f3] group ${
                      item.link && item.link !== "N/A" ? "cursor-pointer" : "cursor-default opacity-80"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[9px] font-bold text-[#004ac6] tracking-wider font-mono uppercase">{item.publisher}</span>
                      <span className="text-[9px] text-[#737686] font-mono font-medium truncate max-w-[120px]" title={item.date}>
                        {formatRelativeTime(item.date)}
                      </span>
                    </div>
                    <p className="text-[13px] leading-snug text-[#191b23] font-bold group-hover:text-[#004ac6] transition-colors">
                      {item.title}
                    </p>
                    <p className="text-[10px] leading-relaxed text-[#737686] mt-1 line-clamp-2">
                      {item.summary}
                    </p>
                  </a>
                ))}
              </div>
            )}
          </div>
        </aside>
      </div>



      {/* Execution Modal */}
      <div
        id="tradeModal"
        className="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-[1px] transition-all"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            const modal = document.getElementById("tradeModal");
            if (modal) modal.classList.add("hidden");
          }
        }}
      >
        <div className="bg-white w-[380px] border border-[#c3c6d7] shadow-xl rounded-lg p-5 overflow-hidden transition-all duration-300 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between mb-4 border-b border-[#e7e7f3] pb-3">
            <h3 className="font-display font-bold text-base text-[#191b23]">New Order</h3>
            <span
              className="material-symbols-outlined cursor-pointer text-[#737686] hover:text-[#191b23] transition-colors"
              onClick={() => {
                const modal = document.getElementById("tradeModal");
                if (modal) modal.classList.add("hidden");
              }}
            >
              close
            </span>
          </div>

          <div className="space-y-4">
            <div className="flex border border-[#c3c6d7] rounded p-0.5 bg-[#f3f3fe]">
              <button
                onClick={() => setOrderType("BUY")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-sm transition-all ${
                  orderType === "BUY"
                    ? "bg-[#10b981] text-white shadow-sm"
                    : "text-[#434655] hover:text-[#191b23]"
                }`}
              >
                BUY
              </button>
              <button
                onClick={() => setOrderType("SELL")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-sm transition-all ${
                  orderType === "SELL"
                    ? "bg-[#ba1a1a] text-white shadow-sm"
                    : "text-[#434655] hover:text-[#191b23]"
                }`}
              >
                SELL
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] font-bold text-[#737686] uppercase tracking-wider block mb-1">
                  Symbol
                </label>
                <input
                  type="text"
                  id="orderSymbol"
                  className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded px-3 py-1.5 text-xs text-[#191b23] focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none font-semibold uppercase"
                  defaultValue={selectedIndex === "NIFTY" ? "NIFTY 50 JUN FUT" : "SENSEX JUN FUT"}
                  key={selectedIndex}
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-[#737686] uppercase tracking-wider block mb-1">
                  Qty
                </label>
                <input
                  type="number"
                  id="orderQty"
                  className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded px-3 py-1.5 text-xs text-[#191b23] focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none font-mono"
                  defaultValue="50"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#737686] uppercase tracking-wider block mb-1">
                Price
              </label>
              <input
                type="number"
                step="0.05"
                id="orderPrice"
                className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded px-3 py-1.5 text-xs text-[#191b23] focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none font-mono font-semibold"
                value={currentIndexPrice ?? ""}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  if (selectedIndex === "NIFTY") {
                    setNiftyPrice(isNaN(val) ? null : val);
                  } else {
                    setSensexPrice(isNaN(val) ? null : val);
                  }
                }}
              />
            </div>

            <button
              onClick={() => {
                const qtyInput = document.getElementById("orderQty") as HTMLInputElement;
                const symInput = document.getElementById("orderSymbol") as HTMLInputElement;
                const qty = qtyInput ? qtyInput.value : "50";
                const symbol = symInput ? symInput.value : "NIFTY 50";
                const priceFormatted = typeof currentIndexPrice === "number" ? `₹${currentIndexPrice.toFixed(2)}` : "Market Price";
                setOrderSubmitted(`${orderType} ${qty} qty of ${symbol} @ ${priceFormatted} — Order queued.`);
                setTimeout(() => {
                  setOrderSubmitted(null);
                  const modal = document.getElementById("tradeModal");
                  if (modal) modal.classList.add("hidden");
                }, 3000);
              }}
              className={`w-full text-white py-2.5 text-xs font-bold rounded mt-2 hover:opacity-90 active:scale-[0.98] transition-all ${
                orderType === "BUY" ? "bg-[#10b981]" : "bg-[#ba1a1a]"
              }`}
            >
              SUBMIT {orderType} ORDER
            </button>
            {orderSubmitted && (
              <div className="mt-3 p-3 bg-[#f0fdf4] border border-[#10b981] rounded-lg text-center">
                <span className="material-symbols-outlined text-[#10b981] !text-base mr-1 align-middle">check_circle</span>
                <span className="text-xs font-semibold text-[#10b981]">{orderSubmitted}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
