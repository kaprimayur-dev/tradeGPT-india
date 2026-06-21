"use client";

import { useState, useEffect } from "react";
import { api, MarketDataResponse } from "../api";

export default function MarketIntelligencePage() {
  const [selectedInterval, setSelectedInterval] = useState("15M");
  const [niftyPrice, setNiftyPrice] = useState(24013.10);
  const [priceChange, setPriceChange] = useState(-0.64);
  
  const [sensexPrice, setSensexPrice] = useState(76802.90);
  const [sensexChange, setSensexChange] = useState(-0.78);

  const [selectedIndex, setSelectedIndex] = useState<"NIFTY" | "SENSEX">("NIFTY");
  const [isIndexDropdownOpen, setIsIndexDropdownOpen] = useState(false);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");
  const [orderSubmitted, setOrderSubmitted] = useState<string | null>(null);
  const [showFullscreenHint, setShowFullscreenHint] = useState(false);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [usdinrPrice, setUsdinrPrice] = useState(83.50);
  const [usdinrChange, setUsdinrChange] = useState(-0.02);

  const mockCandles = [
    { type: "green", height: "45%", wickTop: "15%", wickBottom: "80%" },
    { type: "green", height: "60%", wickTop: "10%", wickBottom: "90%" },
    { type: "red", height: "50%", wickTop: "20%", wickBottom: "75%" },
    { type: "green", height: "70%", wickTop: "5%", wickBottom: "95%" },
    { type: "red", height: "40%", wickTop: "30%", wickBottom: "60%" },
    { type: "red", height: "35%", wickTop: "25%", wickBottom: "55%" },
    { type: "green", height: "55%", wickTop: "15%", wickBottom: "80%" },
    { type: "green", height: "65%", wickTop: "10%", wickBottom: "85%" },
    { type: "red", height: "45%", wickTop: "20%", wickBottom: "70%" },
    { type: "green", height: "75%", wickTop: "5%", wickBottom: "95%" },
    { type: "green", height: "80%", wickTop: "0%", wickBottom: "100%" },
    { type: "red", height: "60%", wickTop: "10%", wickBottom: "85%" },
    { type: "red", height: "55%", wickTop: "15%", wickBottom: "75%" },
    { type: "green", height: "70%", wickTop: "5%", wickBottom: "90%" },
    { type: "green", height: "85%", wickTop: "0%", wickBottom: "95%" },
  ];

  const [candles, setCandles] = useState(mockCandles);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMarketData();
      setMarketData(data);
      if (data.indices) {
        if (data.indices["NIFTY"]) {
          setNiftyPrice(data.indices["NIFTY"].price);
          setPriceChange(data.indices["NIFTY"].change);
        }
        if (data.indices["SENSEX"]) {
          setSensexPrice(data.indices["SENSEX"].price);
          setSensexChange(data.indices["SENSEX"].change);
        }
        if (data.indices["USDINR"]) {
          setUsdinrPrice(data.indices["USDINR"].price);
          setUsdinrChange(data.indices["USDINR"].change);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load live market data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Simulate real-time price tick changes once price is loaded
  useEffect(() => {
    if (loading || error) return;
    const interval = setInterval(() => {
      const niftyDelta = (Math.random() - 0.48) * 4;
      setNiftyPrice((prev) => parseFloat((prev + niftyDelta).toFixed(2)));
      setPriceChange((prev) => parseFloat((prev + (niftyDelta / 24000) * 100).toFixed(4)));

      const sensexDelta = (Math.random() - 0.48) * 12;
      setSensexPrice((prev) => parseFloat((prev + sensexDelta).toFixed(2)));
      setSensexChange((prev) => parseFloat((prev + (sensexDelta / 76800) * 100).toFixed(4)));
    }, 3000);
    return () => clearInterval(interval);
  }, [loading, error]);

  const handleTimeframeChange = (tf: string) => {
    setSelectedInterval(tf);
    // Randomize wicks/heights slightly to visually reflect chart update
    const updated = candles.map((c) => {
      const heightVal = parseInt(c.height, 10);
      const diff = Math.floor(Math.random() * 16) - 8;
      const newHeight = Math.min(90, Math.max(20, heightVal + diff)) + "%";
      const newType = Math.random() > 0.45 ? "green" : "red";
      return {
        ...c,
        height: newHeight,
        type: newType,
      };
    });
    setCandles(updated);
  };

  const timeframes = ["1M", "5M", "15M", "1H", "1D"];

  const currentIndexPrice = selectedIndex === "NIFTY" ? niftyPrice : sensexPrice;
  const currentIndexChange = selectedIndex === "NIFTY" ? priceChange : sensexChange;

  const tickStep = selectedIndex === "NIFTY" ? 50 : 150;
  const tickValues = [
    currentIndexPrice + tickStep * 2,
    currentIndexPrice + tickStep,
    currentIndexPrice,
    currentIndexPrice - tickStep,
    currentIndexPrice - tickStep * 2,
    currentIndexPrice - tickStep * 3,
  ];

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#faf8ff] h-[calc(100vh-3.5rem)] font-body">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-[#004ac6] border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs font-semibold text-[#434655] uppercase tracking-wider animate-pulse">Loading Live Market Terminal...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#faf8ff] h-[calc(100vh-3.5rem)] font-body px-6">
        <div className="bg-white border border-[#ba1a1a] rounded-xl p-6 max-w-md w-full shadow-md text-center">
          <span className="material-symbols-outlined text-[#ba1a1a] !text-4xl mb-3">error_outline</span>
          <h3 className="font-display font-bold text-base text-[#191b23] mb-1">Terminal Connection Error</h3>
          <p className="text-xs text-[#737686] mb-4 leading-normal">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-[#004ac6] hover:bg-[#003ea8] text-white text-xs font-semibold rounded-lg transition-colors active:scale-95 duration-100"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden h-[calc(100vh-3.5rem)] font-body">
      {/* Dynamic Workspace Container */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Center Stage: Charting Area */}
        <section className="flex-1 flex flex-col border-r border-[#c3c6d7] bg-white">
          
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
              <span className="text-[10px] font-bold text-[#737686] tracking-wider uppercase font-mono">
                VOL: 23.4M
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

          {/* Chart Content Area */}
          <div className="flex-1 relative trading-view-grid overflow-hidden flex items-end">
            
            {/* Candlestick Visualization */}
            <div className="absolute inset-0 px-6 pt-16 pb-28 flex items-end justify-between select-none">
              {candles.map((candle, idx) => (
                <div key={idx} className="flex-1 h-full flex flex-col justify-end items-center relative">
                  {/* Wick */}
                  <div
                    className={`absolute w-px ${
                      candle.type === "green" ? "bg-[#10b981]" : "bg-[#ba1a1a]"
                    }`}
                    style={{ top: candle.wickTop, bottom: `calc(100% - ${candle.wickBottom})` }}
                  ></div>
                  {/* Body */}
                  <div
                    className={`w-2.5 sm:w-4 rounded-sm z-10 ${
                      candle.type === "green"
                        ? "bg-[#10b981] border border-[#10b981]"
                        : "bg-[#ba1a1a] border border-[#ba1a1a]"
                    }`}
                    style={{ height: candle.height }}
                  ></div>
                </div>
              ))}
            </div>

            {/* Floating Live Data Tooltip */}
            <div className="absolute top-4 left-4 bg-white/90 border border-[#c3c6d7] p-3 rounded shadow-sm backdrop-blur-sm z-10 max-w-[220px]">
              <p className="text-[9px] font-bold text-[#737686] uppercase tracking-wide mb-1 font-mono">
                DATA: {marketData?.timestamp ? new Date(marketData.timestamp).toLocaleTimeString() : "2026-06-20 14:12"}
              </p>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-xs">
                <span className="text-[#434655]">O: <span className="font-semibold text-[#191b23]">{(currentIndexPrice * 0.998).toFixed(2)}</span></span>
                <span className="text-[#434655]">H: <span className="font-semibold text-[#191b23]">{(currentIndexPrice * 1.002).toFixed(2)}</span></span>
                <span className="text-[#434655]">L: <span className="font-semibold text-[#191b23]">{(currentIndexPrice * 0.995).toFixed(2)}</span></span>
                <span className="text-[#434655]">C: <span className="font-semibold text-[#004ac6]">{currentIndexPrice.toFixed(2)}</span></span>
              </div>
            </div>

            {/* Price Axis (Right) */}
            <div className="absolute right-0 top-0 bottom-0 w-16 border-l border-[#c3c6d7] bg-[#faf8ff] flex flex-col justify-between py-10 text-[10px] font-mono text-[#737686] items-center">
              <span>{tickValues[0].toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span>{tickValues[1].toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span className="bg-[#004ac6] text-white px-1.5 py-0.5 rounded-sm w-full text-center font-bold">
                {currentIndexPrice.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
              <span>{tickValues[3].toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span>{tickValues[4].toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span>{tickValues[5].toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
            </div>

            {/* Volume Histogram (Overlayed bottom) */}
            <div className="w-full h-16 flex items-end gap-1 px-4 mb-2 opacity-35 pointer-events-none">
              <div className="bg-[#ba1a1a] w-full h-1/2 rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-2/3 rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-full rounded-t-sm"></div>
              <div className="bg-[#ba1a1a] w-full h-3/4 rounded-t-sm"></div>
              <div className="bg-[#ba1a1a] w-full h-1/2 rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-[83%] rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-full rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-2/3 rounded-t-sm"></div>
              <div className="bg-[#ba1a1a] w-full h-1/3 rounded-t-sm"></div>
              <div className="bg-[#10b981] w-full h-[80%] rounded-t-sm"></div>
            </div>
          </div>
        </section>

        {/* Right Rail: Breadth & Live Feed */}
        <aside className="w-80 flex flex-col bg-white shrink-0 overflow-hidden border-l border-[#c3c6d7]">
          
          {/* Heatmap Breadth */}
          <div className="p-4 border-b border-[#c3c6d7]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider">Market Breadth</h3>
              <span className="text-[10px] text-[#10b981] font-bold font-mono">
                {marketData?.breadth.advancing || 0} ADV / {marketData?.breadth.declining || 0} DEC
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1">
              {Array.from({ length: 10 }).map((_, idx) => {
                const adv = marketData?.breadth.advancing || 0;
                const dec = marketData?.breadth.declining || 0;
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
          </div>

          {/* Sector Performance */}
          <div className="p-4 border-b border-[#c3c6d7]">
            <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider mb-3">Sector Performance</h3>
            <div className="space-y-3 max-h-[160px] overflow-y-auto custom-scrollbar pr-1">
              {(marketData?.sectors || []).map((sec, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-[#434655] flex-1 truncate uppercase">{sec.name}</span>
                  <div className="w-20 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden shrink-0">
                    <div 
                      className={`h-full ${sec.change >= 0 ? "bg-[#10b981]" : "bg-[#ba1a1a]"}`} 
                      style={{ width: `${Math.min(100, Math.max(15, Math.abs(sec.change) * 20))}%` }}
                    ></div>
                  </div>
                  <span className={`text-[10px] font-mono font-bold w-10 text-right shrink-0 ${sec.change >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
                    {sec.change >= 0 ? "+" : ""}{sec.change.toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Live Institutional Wire Feed */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 bg-[#f3f3fe] border-b border-[#c3c6d7] flex items-center justify-between">
              <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider">Institutional Feed</h3>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse"></span>
                <span className="text-[9px] uppercase tracking-widest text-[#737686] font-bold font-mono">Live</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-[#e7e7f3]">
              {(marketData?.news || []).map((item, idx) => (
                <a 
                  key={idx}
                  href={item.link && item.link !== "N/A" ? item.link : undefined}
                  target={item.link && item.link !== "N/A" ? "_blank" : undefined}
                  rel="noopener noreferrer"
                  className={`p-3 hover:bg-[#faf8ff] hover:text-[#004ac6] transition-all block border-b border-[#e7e7f3] ${
                    item.link && item.link !== "N/A" ? "cursor-pointer" : "cursor-default opacity-80"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] font-bold text-[#004ac6] tracking-wider font-mono uppercase">{item.publisher}</span>
                    <span className="text-[9px] text-[#737686] font-mono font-medium truncate max-w-[120px]">{item.date}</span>
                  </div>
                  <p className="text-xs leading-normal text-[#191b23] font-semibold hover:text-[#004ac6] transition-colors">
                    {item.title}
                  </p>
                  <p className="text-[10px] leading-normal text-[#737686] mt-0.5 line-clamp-2">
                    {item.summary}
                  </p>
                </a>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* Bottom Footer Status Bar */}
        <footer className="no-print h-12 border-t border-[#c3c6d7] bg-white flex items-center px-6 gap-6 shrink-0 z-10 select-none">
        <div className="flex items-center gap-2 border-r border-[#c3c6d7] pr-6">
          <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider">USD/INR</span>
          <span className="font-mono text-sm font-bold text-[#191b23]">₹{usdinrPrice.toFixed(2)}</span>
          <span className={`text-xs font-semibold ${usdinrChange >= 0 ? "text-[#10b981]" : "text-[#ba1a1a]"}`}>
            ({usdinrChange >= 0 ? "+" : ""}{usdinrChange.toFixed(2)}%)
          </span>
        </div>

        <div className="flex items-center gap-2 border-r border-[#c3c6d7] pr-6">
          <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider">Health Score</span>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#c3c6d7]"></div>
            <span className="text-xs font-bold text-[#191b23] ml-1">82/100</span>
          </div>
        </div>

        <div className="flex items-center gap-6 overflow-hidden text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider">Margin</span>
            <span className="font-medium text-[#191b23]">₹8.4L Available</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider">Open Positions</span>
            <span className="font-medium text-[#191b23]">12 Active</span>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-5 text-xs text-[#737686] font-mono">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#10b981]"></div>
            <span className="font-semibold text-[#434655]">Server: Tokyo-1</span>
          </div>
          <span className="font-semibold">Latency: 24ms</span>
        </div>
      </footer>

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
                value={currentIndexPrice}
                onChange={(e) => {
                  if (selectedIndex === "NIFTY") {
                    setNiftyPrice(parseFloat(e.target.value) || 24000);
                  } else {
                    setSensexPrice(parseFloat(e.target.value) || 76000);
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
                setOrderSubmitted(`${orderType} ${qty} qty of ${symbol} @ ₹${currentIndexPrice.toFixed(2)} — Order queued.`);
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
