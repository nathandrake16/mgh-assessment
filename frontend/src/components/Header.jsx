import React from 'react';
import { ShieldCheck, Sparkles, Ship } from 'lucide-react';

export default function Header({ audit, onOpenAudit }) {
  const fixesCount = 9;

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400 flex items-center justify-center">
            <Ship className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                MGH Freight Visibility Dashboard
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/50 rounded-full">
                2026 H1
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live Operations & Logistics Intelligence • Forward Deployed Engineering
            </p>
          </div>
        </div>

        {/* Audit Drawer Trigger Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAudit}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-700/50 rounded-lg shadow-sm transition-all duration-150 group"
            title="Click to view full Data Quality Audit report"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
            <span>Data Quality Audit ({fixesCount} Fixes)</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </button>
        </div>
      </div>
    </header>
  );
}
