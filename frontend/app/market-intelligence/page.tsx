"use client";

import { useState, useEffect } from "react";

export default function MarketIntelligencePage() {
  const [selectedInterval, setSelectedInterval] = useState("15M");
  const [niftyPrice, setNiftyPrice] = useState(22450.20);
  const [priceChange, setPriceChange] = useState(0.45);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");

  // Simulate real-time price tick changes
  useEffect(() => {
    const interval = setInterval(() => {
      const change = (Math.random() - 0.48) * 4;
      setNiftyPrice((prev) => parseFloat((prev + change).toFixed(2)));
      setPriceChange((prev) => parseFloat((prev + (change / 22450) * 100).toFixed(4)));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const timeframes = ["1M", "5M", "15M", "1H", "1D"];

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

  return (
    <div className="flex-1 flex flex-col overflow-hidden h-[calc(100vh-3.5rem)] font-body select-none">
      {/* Dynamic Workspace Container */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Center Stage: Charting Area */}
        <section className="flex-1 flex flex-col border-r border-[#c3c6d7] bg-white">
          
          {/* Chart Toolbar */}
          <div className="h-10 border-b border-[#c3c6d7] flex items-center px-4 justify-between bg-[#faf8ff]">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 border-r border-[#c3c6d7] pr-4 cursor-pointer">
                <span className="text-xs font-bold text-[#191b23]">NIFTY 50</span>
                <span className="material-symbols-outlined text-[#737686] !text-sm">expand_more</span>
              </div>
              
              <div className="flex items-center gap-3 text-[11px] font-bold text-[#434655]">
                {timeframes.map((tf) => (
                  <span
                    key={tf}
                    onClick={() => setSelectedInterval(tf)}
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
              <span className="material-symbols-outlined text-[#737686] hover:text-[#191b23] cursor-pointer !text-base">
                settings
              </span>
              <span className="material-symbols-outlined text-[#737686] hover:text-[#191b23] cursor-pointer !text-base">
                fullscreen
              </span>
            </div>
          </div>

          {/* Chart Content Area */}
          <div className="flex-1 relative trading-view-grid overflow-hidden flex items-end">
            
            {/* Candlestick Visualization */}
            <div className="absolute inset-0 px-6 pt-16 pb-28 flex items-end justify-between select-none">
              {mockCandles.map((candle, idx) => (
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
            <div className="absolute top-4 left-4 bg-white/90 border border-[#c3c6d7] p-3 rounded shadow-sm backdrop-blur-sm z-10 max-w-[200px]">
              <p className="text-[9px] font-bold text-[#737686] uppercase tracking-wide mb-1 font-mono">
                DATA: 2026-06-20 14:12
              </p>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-xs">
                <span className="text-[#434655]">O: <span className="font-semibold text-[#191b23]">22,410.50</span></span>
                <span className="text-[#434655]">H: <span className="font-semibold text-[#191b23]">22,465.10</span></span>
                <span className="text-[#434655]">L: <span className="font-semibold text-[#191b23]">22,398.20</span></span>
                <span className="text-[#434655]">C: <span className="font-semibold text-[#004ac6]">{niftyPrice}</span></span>
              </div>
            </div>

            {/* Price Axis (Right) */}
            <div className="absolute right-0 top-0 bottom-0 w-16 border-l border-[#c3c6d7] bg-[#faf8ff] flex flex-col justify-between py-10 text-[10px] font-mono text-[#737686] items-center">
              <span>22,600</span>
              <span>22,550</span>
              <span className="bg-[#004ac6] text-white px-1.5 py-0.5 rounded-sm w-full text-center font-bold">
                {niftyPrice}
              </span>
              <span>22,400</span>
              <span>22,350</span>
              <span>22,300</span>
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
              <span className="text-[10px] text-[#10b981] font-bold">42 ADV / 8 DEC</span>
            </div>
            <div className="grid grid-cols-5 gap-1">
              <div className="aspect-square bg-[#10b981] rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/80 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/70 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/90 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#ba1a1a]/50 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/60 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/40 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981] rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#ba1a1a]/70 rounded-sm hover:opacity-90 transition-opacity"></div>
              <div className="aspect-square bg-[#10b981]/80 rounded-sm hover:opacity-90 transition-opacity"></div>
            </div>
          </div>

          {/* Sector Performance */}
          <div className="p-4 border-b border-[#c3c6d7]">
            <h3 className="text-[11px] font-bold text-[#191b23] uppercase tracking-wider mb-3">Sector Performance</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-[#434655] flex-1">NIFTY BANK</span>
                <div className="w-24 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden">
                  <div className="bg-[#10b981] h-full w-[85%]"></div>
                </div>
                <span className="text-[10px] font-mono text-[#10b981] font-bold w-10 text-right">+1.8%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-[#434655] flex-1">NIFTY IT</span>
                <div className="w-24 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden">
                  <div className="bg-[#ba1a1a] h-full w-[35%]"></div>
                </div>
                <span className="text-[10px] font-mono text-[#ba1a1a] font-bold w-10 text-right">-0.4%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-[#434655] flex-1">NIFTY FMCG</span>
                <div className="w-24 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden">
                  <div className="bg-[#10b981] h-full w-[55%]"></div>
                </div>
                <span className="text-[10px] font-mono text-[#10b981] font-bold w-10 text-right">+0.9%</span>
              </div>
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
              <div className="p-3 hover:bg-[#faf8ff] transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-[#004ac6] tracking-wider font-mono">BLOOMBERG</span>
                  <span className="text-[9px] text-[#737686] font-mono font-medium">10:42 AM</span>
                </div>
                <p className="text-xs leading-normal text-[#191b23] font-medium">
                  RBI maintains repo rate at 6.5%, focus shifts to liquidity management measures.
                </p>
              </div>

              <div className="p-3 hover:bg-[#faf8ff] transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-[#004ac6] tracking-wider font-mono">REUTERS</span>
                  <span className="text-[9px] text-[#737686] font-mono font-medium">10:35 AM</span>
                </div>
                <p className="text-xs leading-normal text-[#191b23] font-medium">
                  FIIs turn net buyers in cash segment; inflows of ₹1,420 Cr recorded in pre-open.
                </p>
              </div>

              <div className="p-3 hover:bg-[#faf8ff] transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-[#505f76] tracking-wider font-mono">SYSTEM ALERT</span>
                  <span className="text-[9px] text-[#737686] font-mono font-medium">10:20 AM</span>
                </div>
                <p className="text-xs leading-normal text-[#434655] italic">
                  Heavy block trade detected in HDFC Bank: 1.2M shares @ 1,451.50.
                </p>
              </div>

              <div className="p-3 hover:bg-[#faf8ff] transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-[#004ac6] tracking-wider font-mono">CNBC-TV18</span>
                  <span className="text-[9px] text-[#737686] font-mono font-medium">10:05 AM</span>
                </div>
                <p className="text-xs leading-normal text-[#191b23] font-medium">
                  Crude Oil dips below $82 as inventory build-up exceeds market projections.
                </p>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Bottom Footer Status Bar */}
      <footer className="no-print h-12 border-t border-[#c3c6d7] bg-white flex items-center px-6 gap-6 shrink-0 z-10 select-none">
        <div className="flex items-center gap-2 border-r border-[#c3c6d7] pr-6">
          <span className="text-[10px] text-[#737686] font-bold uppercase tracking-wider">Portfolio Value</span>
          <span className="font-mono text-sm font-bold text-[#191b23]">₹42,85,120.00</span>
          <span className="text-xs text-[#10b981] font-semibold">(+₹12,450)</span>
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
        <div className="bg-white w-[380px] border border-[#c3c6d7] shadow-xl rounded-lg p-5 overflow-hidden transition-all duration-300">
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
                  className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded px-3 py-1.5 text-xs text-[#191b23] focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none"
                  defaultValue="NIFTY 50 JUN FUT"
                  readOnly
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-[#737686] uppercase tracking-wider block mb-1">
                  Qty
                </label>
                <input
                  type="number"
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
                className="w-full bg-[#f3f3fe] border border-[#c3c6d7] rounded px-3 py-1.5 text-xs text-[#191b23] focus:border-[#004ac6] focus:ring-1 focus:ring-[#004ac6] outline-none font-mono font-semibold"
                value={niftyPrice}
                onChange={(e) => setNiftyPrice(parseFloat(e.target.value))}
              />
            </div>

            <button
              onClick={() => {
                alert(`Mock Order Executed: ${orderType} 50 Qty @ ${niftyPrice}`);
                const modal = document.getElementById("tradeModal");
                if (modal) modal.classList.add("hidden");
              }}
              className={`w-full text-white py-2.5 text-xs font-bold rounded mt-2 hover:opacity-90 active:scale-[0.98] transition-all ${
                orderType === "BUY" ? "bg-[#10b981]" : "bg-[#ba1a1a]"
              }`}
            >
              SUBMIT {orderType} ORDER
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
