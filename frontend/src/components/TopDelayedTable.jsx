import React from 'react';
import { AlertTriangle, Clock, ArrowUpRight } from 'lucide-react';

export default function TopDelayedTable({ delayedShipments = [], loading, onSelectShipment }) {
  if (loading) {
    return (
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 h-80 animate-pulse" />
    );
  }

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-700/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Top 10 Most Delayed Shipments
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-950 border border-rose-800/50 text-rose-300 font-medium">
                Action Required
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Critical schedule variances impacting delivery SLAs (Click row for full inspector)
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
            <tr>
              <th className="py-2.5 px-3">Shipment ID</th>
              <th className="py-2.5 px-3">Carrier</th>
              <th className="py-2.5 px-3">Trade Lane</th>
              <th className="py-2.5 px-3 text-center">ETA</th>
              <th className="py-2.5 px-3 text-center">ATA</th>
              <th className="py-2.5 px-3 text-center">Delay</th>
              <th className="py-2.5 px-3 text-right">Consignee</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {delayedShipments.map((row, idx) => (
              <tr
                key={idx}
                onClick={() => onSelectShipment(row['Shipment ID'])}
                className="hover:bg-slate-700/50 cursor-pointer transition-colors group"
              >
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400 group-hover:text-blue-300 flex items-center gap-1.5">
                  <span>{row['Shipment ID']}</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </td>
                <td className="py-2.5 px-3 font-medium text-slate-200">
                  {row['Carrier']}
                </td>
                <td className="py-2.5 px-3 text-slate-300">
                  {row['trade_lane']}
                </td>
                <td className="py-2.5 px-3 text-center font-mono text-slate-400">
                  {row['ETA'] || '—'}
                </td>
                <td className="py-2.5 px-3 text-center font-mono text-slate-400">
                  {row['ATA'] || '—'}
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-sm">
                    <Clock className="w-3 h-3 text-rose-400" />
                    +{row['delay_days']} days
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right text-slate-300 max-w-[140px] truncate" title={row['Consignee']}>
                  {row['Consignee']}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
