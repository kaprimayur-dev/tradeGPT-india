"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to console or error reporter
    console.warn("Caught frontend error:", error);
  }, [error]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-[#faf8ff] h-[calc(100vh-3.5rem)] font-body px-6">
      <div className="bg-white border border-[#ba1a1a] rounded-xl p-6 max-w-md w-full shadow-md text-center">
        <span className="material-symbols-outlined text-[#ba1a1a] !text-4xl mb-3">error_outline</span>
        <h3 className="font-display font-bold text-base text-[#191b23] mb-1">Application Error</h3>
        <p className="text-xs text-[#737686] mb-4 leading-normal">
          An unexpected error occurred in Alpha Terminal. Our engineering team has been notified.
        </p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-[#004ac6] hover:bg-[#003ea8] text-white text-xs font-semibold rounded-lg transition-colors active:scale-95 duration-100"
          >
            Retry Section
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-white border border-[#c3c6d7] hover:bg-[#f3f3fe] text-[#191b23] text-xs font-semibold rounded-lg transition-colors active:scale-95 duration-100"
          >
            Reload Window
          </button>
        </div>
      </div>
    </div>
  );
}
