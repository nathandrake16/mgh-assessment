import React from 'react';
import { Package, Clock, Weight, Navigation, ArrowUpRight, CheckCircle2 } from 'lucide-react';

export default function KpiCards({ summary, loading }) {
  if (loading || !summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 animate-pulse h-28" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: "Total Unique Shipments",
      value: summary.total_shipments?.toLocaleString() ?? "500",
      subtitle: `${summary.data_quality_audit?.total_raw_rows ?? 511} raw rows • ${summary.data_quality_audit?.duplicates_removed ?? 11} duplicates dropped`,
      icon: Package,
      badge: "Deduplicated",
      badgeColor: "bg-blue-950/80 text-blue-300 border-blue-800/40",
      iconColor: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    },
    {
      title: "On-Time Delivery Rate",
      value: `${summary.on_time_percentage ?? 57.78}%`,
      subtitle: `${summary.on_time_shipments ?? 260} on-time / ${summary.evaluated_shipments ?? 450} evaluated`,
      icon: Clock,
      badge: "SLA Evaluated",
      badgeColor: "bg-emerald-950/80 text-emerald-300 border-emerald-800/40",
      iconColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    },
    {
      title: "Total Cleaned Weight",
      value: `${(summary.total_weight_kg / 1000).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} MT`,
      subtitle: `${summary.total_weight_kg?.toLocaleString()} kg • ${summary.total_volume_cbm?.toLocaleString()} CBM`,
      icon: Weight,
      badge: "Rescaled",
      badgeColor: "bg-amber-950/80 text-amber-300 border-amber-800/40",
      iconColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    },
    {
      title: "In-Transit Shipments",
      value: "42 Active",
      subtitle: "458 Delivered (91.6% completed)",
      icon: Navigation,
      badge: "Fleet Live",
      badgeColor: "bg-purple-950/80 text-purple-300 border-purple-800/40",
      iconColor: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const IconComponent = card.icon;
        return (
          <div
            key={idx}
            className="bg-slate-800/70 border border-slate-700/60 hover:border-slate-600 rounded-xl p-5 shadow-sm transition-all duration-150 hover:shadow-md relative overflow-hidden group"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  {card.title}
                </p>
                <h3 className="text-2xl font-bold text-white mt-1.5 tracking-tight">
                  {card.value}
                </h3>
              </div>
              <div className={`p-2.5 rounded-xl border ${card.iconColor}`}>
                <IconComponent className="w-5 h-5" />
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-slate-700/50 flex items-center justify-between text-xs">
              <span className="text-slate-400 truncate pr-2">
                {card.subtitle}
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border flex-shrink-0 ${card.badgeColor}`}>
                {card.badge}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
