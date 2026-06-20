"use client";

export default function InstitutionalResearchPage() {
  const growthDrivers = [
    {
      title: "New Energy Ecosystem",
      icon: "bolt",
      desc: "Implementation of the Dhirubhai Ambani Green Energy Giga Complex. Expected reduction in hydrogen production costs to $1/kg by 2030."
    },
    {
      title: "Jio 5G Monetization",
      icon: "signal_cellular_alt",
      desc: "ARPU (Average Revenue Per User) expansion through 5G standalone adoption and fixed wireless access (JioAirFiber)."
    }
  ];

  const riskFactors = [
    { factor: "Crude Volatility", impact: "High", prob: "Medium", score: "0.82" },
    { factor: "Regulatory Headwinds", impact: "Moderate", prob: "Low", score: "0.65" },
    { factor: "Capex Overrun", impact: "Medium", prob: "Medium", score: "0.74" },
  ];

  const citations = [
    { title: "Annual Report FY2025-26", meta: "SEC | 128 Pages | PDF" },
    { title: "Q4 Earnings Presentation", meta: "IR Portal | 45 Pages | PDF" },
    { title: "Strategic New Energy Roadmap", meta: "Exchange Filing | 12 Pages | PDF" },
    { title: "Sustainability Report 2026", meta: "ESG Filing | 88 Pages | PDF" },
  ];

  return (
    <div className="flex-1 bg-[#faf8ff] p-6 font-body select-none">
      <div className="grid grid-cols-12 gap-6">
        
        {/* Left Column (Wide): Research Note */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6 pr-0 lg:pr-6">
          
          {/* Document Header */}
          <div className="border-b border-[#c3c6d7] pb-6">
            <div className="flex items-center justify-between mb-2 text-xs">
              <span className="text-[#004ac6] font-bold tracking-widest uppercase">
                Research Report #2026-REL-04
              </span>
              <span className="text-[#737686] font-mono uppercase font-semibold">
                Updated: 20 JUN 2026, 09:30 AM IST
              </span>
            </div>
            <h2 className="font-display font-bold text-2xl text-[#191b23] tracking-tight">
              Integrated Energy &amp; Digital Transformation Synergy
            </h2>
            <p className="text-sm text-[#434655] mt-2 max-w-3xl leading-relaxed">
              A comprehensive analysis on Reliance Industries Limited (RIL) focusing on New Energy integration and O2C margin stabilization amidst global volatility.
            </p>
          </div>

          {/* Executive Summary */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1 h-5 bg-[#004ac6]"></div>
              <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Executive Summary</h3>
            </div>
            <div className="text-xs text-[#434655] leading-relaxed space-y-4">
              <p>
                Reliance Industries Limited (RIL) continues to demonstrate robust resilience across its diversified business segments. The core O2C (Oil-to-Chemicals) business provides a stable cash flow foundation, while the consumer-facing Jio and Retail businesses drive the next leg of growth. Our analysis suggests that the market has yet to fully price in the valuation of the New Energy segment, which we estimate will contribute significantly to EBITDA by FY28.
              </p>
              
              <div className="grid grid-cols-3 gap-4 py-4 border-y border-[#c3c6d7] font-mono">
                <div className="flex flex-col">
                  <span className="text-[9px] text-[#737686] uppercase font-bold">Recommendation</span>
                  <span className="text-[#004ac6] font-bold text-sm">OVERWEIGHT</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-[#737686] uppercase font-bold">Price Target (12M)</span>
                  <span className="text-[#191b23] font-bold text-sm">₹3,450.00</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-[#737686] uppercase font-bold">Upside</span>
                  <span className="text-[#bc4800] font-bold text-sm">+15.6%</span>
                </div>
              </div>
            </div>
          </section>

          {/* Growth Drivers (Bento style) */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-1 h-5 bg-[#004ac6]"></div>
              <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Primary Growth Drivers</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {growthDrivers.map((driver) => (
                <div key={driver.title} className="p-4 border border-[#c3c6d7] rounded-lg bg-white shadow-sm flex flex-col justify-between">
                  <div>
                    <span className="material-symbols-outlined text-[#004ac6] mb-2 !text-base">{driver.icon}</span>
                    <h4 className="text-xs font-bold text-[#191b23] mb-1.5">{driver.title}</h4>
                    <p className="text-[11px] text-[#434655] leading-normal">{driver.desc}</p>
                  </div>
                </div>
              ))}
              
              <div className="p-4 border border-[#c3c6d7] rounded-lg bg-white shadow-sm col-span-1 sm:col-span-2 flex gap-4 items-center">
                <div className="w-16 h-16 flex-shrink-0 bg-[#f3f3fe] rounded flex items-center justify-center border border-[#c3c6d7]">
                  <span className="material-symbols-outlined text-xl text-[#737686]">shopping_bag</span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#191b23] mb-1">Retail Omnichannel Scaling</h4>
                  <p className="text-[11px] text-[#434655] leading-normal">
                    Expansion of Tier 3-4 footprint and integration of METRO Cash &amp; Carry assets into the existing supply chain network.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Risk Matrix Table */}
          <section className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1 h-5 bg-[#004ac6]"></div>
              <h3 className="text-xs font-bold text-[#191b23] uppercase tracking-wider">Risk Matrix</h3>
            </div>
            <div className="overflow-x-auto border border-[#c3c6d7] rounded-lg shadow-sm">
              <table className="w-full text-xs text-left border-collapse bg-white">
                <thead>
                  <tr className="bg-[#f3f3fe] text-[#737686] font-mono uppercase text-[9px] border-b border-[#c3c6d7] font-bold">
                    <th className="px-4 py-2.5">Risk Factor</th>
                    <th className="px-4 py-2.5">Impact</th>
                    <th className="px-4 py-2.5">Probability</th>
                    <th className="px-4 py-2.5 text-right">Mitigant Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e7e7f3] text-[#434655]">
                  {riskFactors.map((risk) => (
                    <tr key={risk.factor} className="hover:bg-[#faf8ff] transition-colors">
                      <td className="px-4 py-3 font-semibold text-[#191b23]">{risk.factor}</td>
                      <td className="px-4 py-3">{risk.impact}</td>
                      <td className="px-4 py-3">{risk.prob}</td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-[#004ac6]">{risk.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Right Column (Narrow): Metrics & Citations */}
        <div className="col-span-12 lg:col-span-4 border-l-0 lg:border-l border-[#c3c6d7] pl-0 lg:pl-6 space-y-8">
          
          {/* Technical Metrics */}
          <div>
            <h3 className="text-[10px] font-bold text-[#737686] tracking-wider uppercase mb-4">
              Technical Metrics
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                <span className="text-xs text-[#434655] font-medium">RSI (14-Day)</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-[#191b23]">58.42</span>
                  <span className="w-12 h-1.5 bg-[#e7e7f3] rounded-full overflow-hidden">
                    <span className="block h-full bg-[#004ac6]" style={{ width: "58%" }}></span>
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                <span className="text-xs text-[#434655] font-medium">50-Day Moving Avg</span>
                <span className="font-mono font-bold text-[#191b23]">₹2,845.10</span>
              </div>
              <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                <span className="text-xs text-[#434655] font-medium">200-Day Moving Avg</span>
                <span className="font-mono font-bold text-[#191b23]">₹2,612.45</span>
              </div>
              <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                <span className="text-xs text-[#434655] font-medium">Volume (Avg 10D)</span>
                <span className="font-mono font-bold text-[#191b23]">6.8M</span>
              </div>
              <div className="flex items-center justify-between border-b border-[#e7e7f3] pb-2">
                <span className="text-xs text-[#434655] font-medium">VWAP</span>
                <span className="font-mono font-bold text-[#191b23]">₹2,991.05</span>
              </div>
            </div>
          </div>

          {/* Citations badges */}
          <div>
            <h3 className="text-[10px] font-bold text-[#737686] tracking-wider uppercase mb-4">
              Institutional Citations
            </h3>
            <div className="space-y-3">
              {citations.map((cit, idx) => (
                <div key={idx} className="group p-2.5 border border-[#c3c6d7] rounded bg-white hover:border-[#004ac6] cursor-pointer transition-all flex items-center justify-between">
                  <div className="overflow-hidden">
                    <p className="text-xs font-bold text-[#191b23] group-hover:text-[#004ac6] transition-colors truncate">
                      {cit.title}
                    </p>
                    <p className="text-[9px] text-[#737686] font-mono mt-0.5">{cit.meta}</p>
                  </div>
                  <span className="material-symbols-outlined text-[#737686] group-hover:text-[#004ac6] !text-sm flex-shrink-0">
                    open_in_new
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Ownership Breakdown */}
          <div className="p-4 bg-white border border-[#c3c6d7] rounded-xl shadow-sm">
            <h4 className="text-[10px] font-bold text-[#191b23] uppercase tracking-wider mb-3">
              Ownership Structure
            </h4>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 bg-[#004ac6] rounded-sm"></div>
                <span className="text-xs text-[#434655] flex-1">Promoter Group</span>
                <span className="text-xs font-mono font-bold text-[#191b23]">50.39%</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 bg-[#505f76] rounded-sm"></div>
                <span className="text-xs text-[#434655] flex-1">FII / FPI</span>
                <span className="text-xs font-mono font-bold text-[#191b23]">22.12%</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 bg-[#c3c6d7] rounded-sm"></div>
                <span className="text-xs text-[#434655] flex-1">DII / Mutual Funds</span>
                <span className="text-xs font-mono font-bold text-[#191b23]">16.55%</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 bg-[#e7e7f3] rounded-sm"></div>
                <span className="text-xs text-[#434655] flex-1">Public &amp; Others</span>
                <span className="text-xs font-mono font-bold text-[#191b23]">10.94%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
