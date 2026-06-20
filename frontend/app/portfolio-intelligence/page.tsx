"use client";

import { useEffect, useState } from "react";

export default function PortfolioIntelligencePage() {
  const [animateWidth, setAnimateWidth] = useState(false);

  useEffect(() => {
    setAnimateWidth(true);
  }, []);

  const swotItems = [
    { title: "Strengths", text: "Superior earnings-per-share (EPS) momentum in 65% of holdings.", style: "bg-green-50 border-green-200 text-green-800" },
    { title: "Weaknesses", text: "Exposure to high-valuation multiples in non-core speculative assets.", style: "bg-red-50 border-red-200 text-red-800" },
    { title: "Opportunities", text: "Undervalued entry points in emerging markets infrastructure.", style: "bg-blue-50 border-blue-200 text-blue-800" },
    { title: "Threats", text: "Macro volatility stemming from geopolitical shifts in energy supply chains.", style: "bg-orange-50 border-orange-200 text-orange-800" },
  ];

  return (
    <div className="flex-1 bg-[#faf8ff] py-6 px-6 font-body select-none">
      <div className="max-w-7xl mx-auto">
        
        {/* Header Section */}
        <div className="flex justify-between items-end mb-6 border-b border-[#c3c6d7] pb-6">
          <div>
            <h1 className="font-display font-bold text-2xl text-[#191b23] mb-1 tracking-tight">
              Portfolio Intelligence Report
            </h1>
            <div className="flex items-center gap-4 text-[#434655] text-xs">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined !text-sm">calendar_today</span> Oct 24, 2026
              </span>
              <span className="flex items-center gap-1 font-mono">
                <span className="material-symbols-outlined !text-sm">id_card</span> ID: PRT-8829-X
              </span>
              <span className="px-2 py-0.5 bg-[#d0e1fb] text-[#0b1c30] text-[9px] font-bold rounded">
                EQUITY RESEARCH
              </span>
            </div>
          </div>
          <div className="flex gap-3 no-print">
            <button 
              onClick={() => alert("Report link copied to clipboard.")}
              className="px-4 py-2 bg-white border border-[#c3c6d7] rounded-lg flex items-center gap-2 hover:bg-[#f3f3fe] transition-colors text-xs font-semibold text-[#191b23] active:scale-95 duration-100"
            >
              <span className="material-symbols-outlined !text-sm">share</span> Share
            </button>
            <button 
              onClick={() => window.print()}
              className="px-4 py-2 bg-[#004ac6] text-white rounded-lg flex items-center gap-2 hover:bg-[#003ea8] transition-colors text-xs font-semibold active:scale-95 duration-100"
            >
              <span className="material-symbols-outlined !text-sm">print</span> Print Report
            </button>
          </div>
        </div>

        {/* Top Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          
          {/* Health Score */}
          <div className="bg-white p-5 rounded-xl border border-[#c3c6d7] flex flex-col justify-between shadow-sm">
            <span className="text-[10px] font-bold text-[#737686] tracking-wider uppercase">
              Portfolio Health Score
            </span>
            <div className="flex items-baseline gap-1.5 mt-3">
              <span className="text-3xl font-bold text-[#191b23] tracking-tighter">84</span>
              <span className="text-xs text-[#434655]">/100</span>
            </div>
            <div className="w-full bg-[#e7e7f3] h-1.5 rounded-full mt-4">
              <div 
                className="bg-[#004ac6] h-1.5 rounded-full transition-all duration-1000"
                style={{ width: animateWidth ? "84%" : "0%" }}
              ></div>
            </div>
          </div>

          {/* Risk Rating */}
          <div className="bg-white p-5 rounded-xl border border-[#c3c6d7] flex flex-col justify-between shadow-sm">
            <span className="text-[10px] font-bold text-[#737686] tracking-wider uppercase">
              Risk Rating
            </span>
            <div className="mt-3">
              <div className="text-xl font-bold text-[#191b23]">Moderate-Low</div>
              <div className="text-[11px] text-[#505f76] font-semibold mt-1 font-mono">
                β = 0.88 | Sharpe = 1.42
              </div>
            </div>
            <div className="flex gap-1.5 mt-3">
              <div className="h-1.5 flex-1 bg-[#10b981] rounded-full"></div>
              <div className="h-1.5 flex-1 bg-[#10b981] rounded-full"></div>
              <div className="h-1.5 flex-1 bg-[#e7e7f3] rounded-full"></div>
              <div className="h-1.5 flex-1 bg-[#e7e7f3] rounded-full"></div>
            </div>
          </div>

          {/* Sector Exposure Preview */}
          <div className="bg-white p-5 rounded-xl border border-[#c3c6d7] col-span-1 md:col-span-2 shadow-sm">
            <div className="flex justify-between items-center mb-3">
              <span className="text-[10px] font-bold text-[#737686] tracking-wider uppercase">
                Top Sector Exposures
              </span>
              <span className="material-symbols-outlined text-[#004ac6] !text-base">pie_chart</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-[#191b23] w-20">Technology</span>
                <div className="flex-1 bg-[#e7e7f3] h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-[#004ac6] h-full transition-all duration-1000" 
                    style={{ width: animateWidth ? "42%" : "0%" }}
                  ></div>
                </div>
                <span className="text-xs font-mono font-bold text-[#434655] w-8 text-right">42%</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-[#191b23] w-20">Financials</span>
                <div className="flex-1 bg-[#e7e7f3] h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-[#505f76] h-full transition-all duration-1000" 
                    style={{ width: animateWidth ? "18%" : "0%" }}
                  ></div>
                </div>
                <span className="text-xs font-mono font-bold text-[#434655] w-8 text-right">18%</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-[#191b23] w-20">Healthcare</span>
                <div className="flex-1 bg-[#e7e7f3] h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-[#bc4800] h-full transition-all duration-1000" 
                    style={{ width: animateWidth ? "12%" : "0%" }}
                  ></div>
                </div>
                <span className="text-xs font-mono font-bold text-[#434655] w-8 text-right">12%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          
          {/* Left: Summary and SWOT */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-[#c3c6d7] overflow-hidden shadow-sm">
            <div className="bg-[#f3f3fe] px-6 py-5 border-b border-[#c3c6d7]">
              <h2 className="font-display font-bold text-base text-[#191b23]">
                Executive Intelligence Summary
              </h2>
              <p className="text-xs text-[#434655] mt-1">
                High-conviction analysis based on current institutional data models.
              </p>
            </div>
            
            <div className="p-6 space-y-6">
              <section>
                <h3 className="text-sm font-bold text-[#004ac6] border-b border-[#e7e7f3] pb-1.5 mb-3 uppercase tracking-wider">
                  Strategic Strengths
                </h3>
                <p className="text-xs leading-relaxed text-[#191b23] mb-3">
                  The current portfolio structure exhibits robust defensive characteristics against inflationary pressures. Your heavy weighting in large-cap technology firms (AAPL, MSFT, GOOGL) provides a solid growth floor, while the secondary concentration in financials offers a hedge against potential interest rate hikes in Q4.
                </p>
                <ul className="list-disc list-inside text-xs text-[#434655] space-y-1.5 leading-relaxed">
                  <li>High dividend reinvestment yield across healthcare holdings.</li>
                  <li>Optimized alpha generation through disciplined rebalancing in semiconductor stocks.</li>
                  <li>Strong liquidity ratio (L1) across the top 10 positions.</li>
                </ul>
              </section>

              <section>
                <h3 className="text-sm font-bold text-[#004ac6] border-b border-[#e7e7f3] pb-1.5 mb-3 uppercase tracking-wider">
                  Concentration Risk Analysis
                </h3>
                <div className="bg-[#faf8ff] p-4 border-l-4 border-[#ba1a1a] rounded-r">
                  <p className="text-xs font-bold text-[#191b23]">Critical Notice: Tech Concentration</p>
                  <p className="text-xs text-[#434655] mt-1 leading-normal">
                    Your portfolio currently has a 42% exposure to the Technology sector. While historically profitable, this exceeds standard institutional diversification thresholds by 12%. A sector-specific correction could result in a drawdown of ~8.4% beyond benchmark volatility.
                  </p>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-bold text-[#004ac6] border-b border-[#e7e7f3] pb-1.5 mb-4 uppercase tracking-wider">
                  SWOT Matrix
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {swotItems.map((item) => (
                    <div key={item.title} className={`p-4 border rounded ${item.style}`}>
                      <h4 className="text-xs font-bold uppercase mb-1">{item.title}</h4>
                      <p className="text-xs leading-normal opacity-90">{item.text}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <h3 className="text-sm font-bold text-[#004ac6] border-b border-[#e7e7f3] pb-1.5 mb-2 uppercase tracking-wider">
                  Future Growth Catalysts
                </h3>
                <p className="text-xs text-[#191b23] italic leading-relaxed">
                  &ldquo;The portfolio is well-positioned for the anticipated AI integration wave. However, we recommend a tactical rotation of 5% from consumer discretionary to renewable energy over the next 180 days.&rdquo;
                </p>
              </section>
            </div>
          </div>

          {/* Right: Holdings and Stress Exposure */}
          <div className="space-y-6">
            
            {/* Holdings table */}
            <div className="bg-white rounded-xl border border-[#c3c6d7] overflow-hidden shadow-sm">
              <div className="px-5 py-3 border-b border-[#c3c6d7] bg-[#f3f3fe]">
                <span className="text-[10px] font-bold text-[#191b23] uppercase tracking-wider">
                  Alpha Drivers
                </span>
              </div>
              <table className="w-full text-xs text-left">
                <thead className="bg-[#f8fafc] border-b border-[#c3c6d7] text-[#737686] uppercase text-[9px] font-bold">
                  <tr>
                    <th className="px-4 py-2.5">Ticker</th>
                    <th className="px-4 py-2.5 text-right font-mono">Return</th>
                    <th className="px-4 py-2.5 text-right">Sentiment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e7e7f3] font-medium text-[#191b23]">
                  <tr className="hover:bg-[#faf8ff] transition-colors">
                    <td className="px-4 py-3 font-semibold">NVDA</td>
                    <td className="px-4 py-3 text-right font-mono text-[#10b981] font-bold">+24.2%</td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[9px] bg-green-100 text-green-800 px-2 py-0.5 rounded font-bold uppercase">
                        BULLISH
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-[#faf8ff] transition-colors">
                    <td className="px-4 py-3 font-semibold">MSFT</td>
                    <td className="px-4 py-3 text-right font-mono text-[#10b981] font-bold">+12.8%</td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[9px] bg-green-100 text-green-800 px-2 py-0.5 rounded font-bold uppercase">
                        BULLISH
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-[#faf8ff] transition-colors bg-red-50/20">
                    <td className="px-4 py-3 font-semibold">PYPL</td>
                    <td className="px-4 py-3 text-right font-mono text-[#ba1a1a] font-bold">-14.5%</td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[9px] bg-red-100 text-red-800 px-2 py-0.5 rounded font-bold uppercase">
                        BEARISH
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-[#faf8ff] transition-colors bg-red-50/10">
                    <td className="px-4 py-3 font-semibold">TSLA</td>
                    <td className="px-4 py-3 text-right font-mono text-[#ba1a1a] font-bold">-8.2%</td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[9px] bg-orange-100 text-orange-800 px-2 py-0.5 rounded font-bold uppercase">
                        NEUTRAL
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Stress Exposure Card */}
            <div className="bg-white p-5 rounded-xl border border-[#c3c6d7] shadow-sm">
              <h4 className="text-[10px] font-bold text-[#191b23] uppercase tracking-wider mb-4">
                Macro Stress Exposure
              </h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-[#434655] font-medium">Interest Rate Sensitivity</span>
                    <span className="font-bold text-[#ba1a1a]">High</span>
                  </div>
                  <div className="w-full h-2.5 bg-[#e7e7f3] rounded-full flex overflow-hidden">
                    <div 
                      className="bg-[#ba1a1a] h-full transition-all duration-1000" 
                      style={{ width: animateWidth ? "80%" : "0%" }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-[#434655] font-medium">Geopolitical Risk</span>
                    <span className="font-bold text-[#bc4800]">Moderate</span>
                  </div>
                  <div className="w-full h-2.5 bg-[#e7e7f3] rounded-full flex overflow-hidden">
                    <div 
                      className="bg-[#bc4800] h-full transition-all duration-1000" 
                      style={{ width: animateWidth ? "45%" : "0%" }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-[#434655] font-medium">Currency Fluctuation</span>
                    <span className="font-bold text-[#10b981]">Low</span>
                  </div>
                  <div className="w-full h-2.5 bg-[#e7e7f3] rounded-full flex overflow-hidden">
                    <div 
                      className="bg-[#10b981] h-full transition-all duration-1000" 
                      style={{ width: animateWidth ? "20%" : "0%" }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual Accent Card */}
            <div className="relative overflow-hidden rounded-xl h-44 group border border-[#c3c6d7] shadow-sm select-none">
              <div 
                className="bg-cover bg-center w-full h-full transform group-hover:scale-105 transition-transform duration-700" 
                style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuC5BNj0t4GODttf3T33xP5c8Y_Ukzw2rXoymcgPnsar3fDIwuZ__CMkprRMSRQTPMS4B_adyzkQoAejJq4VHD4u21F2VWSil7SYp0HkJtCkckVTAfbmxyhkaxMLC91oHT2us0V0QOZSZbzcD6B37lKNVI2KS2IxN8uRpPxR2vu9e_Q91oncFx9g-i1klmAq6AQAT-M1FUPRjBsYWDBTmbUCL_Yi5JJS5A-lI093NwbBtF2NJ-1SYXKToWJGBNMyztyXm_9InvsY9emi')" }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent flex flex-col justify-end p-5">
                <span className="text-[9px] text-white/70 font-bold uppercase tracking-widest mb-0.5">
                  Global Market Insight
                </span>
                <p className="text-white font-semibold text-xs leading-normal">
                  Monitor correlation shifts in real-time with Terminal Pro.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Disclaimer */}
        <footer className="mt-12 pt-6 border-t border-[#c3c6d7] text-center pb-6">
          <p className="text-[9px] text-[#737686] max-w-2xl mx-auto leading-relaxed uppercase tracking-wider">
            Confidential Report. This analysis is for informational purposes only and does not constitute investment advice. FinIntel Workstation assumes no liability for trading decisions based on this model. Past performance is not indicative of future results. All data subject to 15-minute terminal delay.
          </p>
        </footer>
      </div>
    </div>
  );
}
