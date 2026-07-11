"use client";

import { useState, useEffect } from "react";

export default function SettingsPage() {
  const [theme, setTheme] = useState("light");
  const [refresh, setRefresh] = useState("30s");
  const [density, setDensity] = useState("compact");
  const [sound, setSound] = useState(true);
  const [currency, setCurrency] = useState("INR");
  const [alerts, setAlerts] = useState(true);
  
  const [saveStatus, setSaveStatus] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      setTheme(localStorage.getItem("trade_theme") || "light");
      setRefresh(localStorage.getItem("trade_settings_refresh") || "30s");
      setDensity(localStorage.getItem("trade_settings_density") || "compact");
      setSound(localStorage.getItem("trade_settings_sound") !== "false");
      setCurrency(localStorage.getItem("trade_settings_currency") || "INR");
      setAlerts(localStorage.getItem("trade_settings_alerts") !== "false");
    }
  }, []);

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("trade_theme", theme);
      localStorage.setItem("trade_settings_refresh", refresh);
      localStorage.setItem("trade_settings_density", density);
      localStorage.setItem("trade_settings_sound", sound ? "true" : "false");
      localStorage.setItem("trade_settings_currency", currency);
      localStorage.setItem("trade_settings_alerts", alerts ? "true" : "false");

      // Apply theme immediately
      if (theme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      window.dispatchEvent(new Event("themeChanged"));

      setSaveStatus("Preferences persisted successfully.");
      setTimeout(() => setSaveStatus(""), 3000);
    }
  };

  if (!mounted) {
    return (
      <div className="flex-1 p-8 bg-canvas flex items-center justify-center">
        <div className="text-xs text-text-muted font-mono animate-pulse">Loading console preferences...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-canvas select-none font-body">
      <div className="max-w-2xl mx-auto space-y-6">
        
        {/* Title */}
        <div>
          <h2 className="text-lg font-bold text-text-primary font-display">Terminal Configuration Console</h2>
          <p className="text-xs text-text-muted">Customize workspace defaults, streaming layers, and notifications.</p>
        </div>

        {/* Form Sections */}
        <div className="bg-surface-base border border-border-subtle rounded-xl p-5 space-y-5 shadow-sm">
          
          {/* Theme Setup */}
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">Terminal Appearance</label>
            <div className="grid grid-cols-2 gap-3">
              <div
                onClick={() => setTheme("light")}
                className={`p-3 border rounded-lg cursor-pointer transition-all flex flex-col items-center gap-1.5 active-press ${
                  theme === "light"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border-subtle hover:bg-canvas text-text-muted"
                }`}
              >
                <span className="material-symbols-outlined">light_mode</span>
                <span className="text-xs font-bold">Standard Light</span>
              </div>
              <div
                onClick={() => setTheme("dark")}
                className={`p-3 border rounded-lg cursor-pointer transition-all flex flex-col items-center gap-1.5 active-press ${
                  theme === "dark"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border-subtle hover:bg-canvas text-text-muted"
                }`}
              >
                <span className="material-symbols-outlined">dark_mode</span>
                <span className="text-xs font-bold">Bloomberg Dark</span>
              </div>
            </div>
          </div>

          <hr className="border-border-subtle/30" />

          {/* Polling & Refresh Setup */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-text-primary block">Market Stream Refresh</span>
              <span className="text-[10px] text-text-muted">Set polling frequency for yfinance watchlist rates.</span>
            </div>
            <select
              value={refresh}
              onChange={(e) => setRefresh(e.target.value)}
              className="text-xs font-mono font-bold bg-canvas border border-border-subtle rounded px-2 py-1 outline-none text-text-primary"
            >
              <option value="15s">15 seconds</option>
              <option value="30s">30 seconds (Default)</option>
              <option value="1m">1 minute</option>
              <option value="5m">5 minutes</option>
            </select>
          </div>

          <hr className="border-border-subtle/30" />

          {/* Layout density */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-text-primary block">Layout Density</span>
              <span className="text-[10px] text-text-muted">Adjust padding and text sizing for financial metrics.</span>
            </div>
            <div className="flex bg-canvas border border-border-subtle rounded-lg p-0.5">
              <button
                onClick={() => setDensity("compact")}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                  density === "compact" ? "bg-primary text-white" : "text-text-muted hover:text-text-primary"
                }`}
              >
                Compact
              </button>
              <button
                onClick={() => setDensity("cozy")}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                  density === "cozy" ? "bg-primary text-white" : "text-text-muted hover:text-text-primary"
                }`}
              >
                Cozy
              </button>
            </div>
          </div>

          <hr className="border-border-subtle/30" />

          {/* Switches */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-text-primary block">Alarms & Order Sounds</span>
                <span className="text-[10px] text-text-muted">Play system sound effects upon order fill.</span>
              </div>
              <input
                type="checkbox"
                checked={sound}
                onChange={(e) => setSound(e.target.checked)}
                className="w-4 h-4 rounded accent-primary bg-canvas border-border-subtle"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-text-primary block">Currency Layout Default</span>
                <span className="text-[10px] text-text-muted">Display portfolio valuations in INR (₹) or USD ($).</span>
              </div>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="text-xs font-mono font-bold bg-canvas border border-border-subtle rounded px-2 py-1 outline-none text-text-primary"
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-text-primary block">RAG Execution Alerts</span>
                <span className="text-[10px] text-text-muted">Push notification center warnings on long queries.</span>
              </div>
              <input
                type="checkbox"
                checked={alerts}
                onChange={(e) => setAlerts(e.target.checked)}
                className="w-4 h-4 rounded accent-primary bg-canvas border-border-subtle"
              />
            </div>
          </div>

          {/* Save Area */}
          <div className="pt-2 border-t border-border-subtle/40 flex items-center justify-between gap-4">
            <span className="text-xs font-semibold text-[#10b981] font-mono">{saveStatus}</span>
            <button
              onClick={handleSave}
              className="px-5 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:bg-primary-fixed-dim transition-all shadow-md active-press"
            >
              Apply Settings
            </button>
          </div>
        </div>

        {/* Shortcuts card */}
        <div className="p-4 border border-border-subtle bg-canvas rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-text-primary block">Keyboard Hotkey Map</span>
            <span className="text-[10px] text-text-muted">Access rapid controls using power-user bindings.</span>
          </div>
          <kbd className="text-xs font-mono font-bold bg-surface-base px-2 py-1 border border-border-subtle rounded text-text-primary shadow-sm">
            ?
          </kbd>
        </div>

      </div>
    </div>
  );
}
