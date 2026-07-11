"use client";

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ShortcutsModal({ isOpen, onClose }: ShortcutsModalProps) {
  if (!isOpen) return null;

  const list = [
    { key: "Ctrl + K", desc: "Toggle Command Palette / Global Search" },
    { key: "?", desc: "Toggle Keyboard Shortcuts Map" },
    { key: "1", desc: "Navigate to Market Intelligence Desk" },
    { key: "2", desc: "Navigate to RAG Institutional Research" },
    { key: "3", desc: "Navigate to Portfolio Intelligence Suite" },
    { key: "4", desc: "Navigate to Quantitative Strategy Lab" },
    { key: "T", desc: "Toggle Bloomberg Dark Mode" },
    { key: "R", desc: "Manual Cache Purge & Data Reload" },
    { key: "ESC", desc: "Close Dialogs / Settings Overlay" },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#090a0f]/40 dark:bg-black/60 backdrop-blur-[2px]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-surface-base border border-border-subtle shadow-2xl rounded-xl overflow-hidden flex flex-col mx-4 animate-in fade-in zoom-in-95 duration-100"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-4 py-3 border-b border-border-subtle bg-canvas flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary !text-lg">keyboard</span>
            <span className="text-xs font-bold text-text-primary uppercase tracking-wider">Terminal Keyboard Shortcuts</span>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <span className="material-symbols-outlined !text-sm">close</span>
          </button>
        </div>
        <div className="p-4 divide-y divide-canvas">
          {list.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center py-2 text-xs">
              <span className="font-semibold text-text-muted">{item.desc}</span>
              <kbd className="font-mono bg-canvas border border-border-subtle text-text-primary px-2 py-0.5 rounded shadow-sm text-[10px]">
                {item.key}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
