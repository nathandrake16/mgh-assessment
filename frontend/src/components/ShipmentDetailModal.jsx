import React, { useEffect, useState } from 'react';
import { X, Package, Clock, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, Loader2, Anchor } from 'lucide-react';
import { fetchShipmentById } from '../api';

export default function ShipmentDetailModal({ shipmentId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!shipmentId) return;
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchShipmentById(shipmentId)
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to fetch shipment details.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [shipmentId]);

  if (!shipmentId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
              <Package className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white font-mono">
                  {shipmentId}
                </h3>
                {data && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                    data.Status === 'Delivered'
                      ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/40'
                      : 'bg-amber-950/80 text-amber-300 border-amber-800/40'
                  }`}>
                    {data.Status}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                15-Field Operational Deep Dive & SLA Inspector
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-7 h-7 text-blue-500 animate-spin" />
              <p className="text-xs text-slate-400">Fetching verified shipment record...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span>{error}</span>
            </div>
          ) : data ? (
            <div className="space-y-5">
              {/* Route Banner */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Origin</span>
                  <div className="text-sm font-bold text-white">{data['Origin Port']}</div>
                </div>
                <div className="flex flex-col items-center px-4">
                  <span className="text-[10px] text-blue-400 font-mono font-medium">
                    {data.Mode} • {data['Container Mode']}
                  </span>
                  <div className="flex items-center gap-1 text-slate-500 my-0.5">
                    <div className="w-12 h-px bg-slate-700" />
                    <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
                    <div className="w-12 h-px bg-slate-700" />
                  </div>
                  <span className="text-[10px] text-slate-400">{data.Carrier}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Destination</span>
                  <div className="text-sm font-bold text-white">{data['Destination Port']}</div>
                </div>
              </div>

              {/* SLA & Delay Analysis */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">SLA Status</div>
                  <div className="mt-1">
                    {data.is_evaluated ? (
                      data.on_time ? (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" /> On-Time
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-400">
                          <Clock className="w-3.5 h-3.5" /> Delayed
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-slate-500 italic">Excluded from SLA</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Schedule Variance</div>
                  <div className="text-xs font-bold text-white mt-1">
                    {data.delay_days !== null ? (
                      data.delay_days > 0 ? (
                        <span className="text-rose-400">+{data.delay_days} days</span>
                      ) : (
                        <span className="text-emerald-400">{data.delay_days} days (Early/On-Time)</span>
                      )
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Cargo Weight</div>
                  <div className="text-xs font-bold text-white mt-1">
                    {data['Weight (KG)'] !== null ? (
                      `${data['Weight (KG)'].toLocaleString()} kg`
                    ) : (
                      <span className="text-amber-400 italic">Null (Cleaned)</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Volume</div>
                  <div className="text-xs font-bold text-white mt-1">
                    {data['Volume (CBM)'] ? `${data['Volume (CBM)']} CBM` : '—'}
                  </div>
                </div>
              </div>

              {/* Schedule Dates Grid */}
              <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-4">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Schedule Milestones (ETD / ETA / ATD / ATA)
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px]">Estimated Departure (ETD)</span>
                    <p className="font-mono font-medium text-slate-200 mt-0.5">{data.ETD || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Actual Departure (ATD)</span>
                    <p className="font-mono font-medium text-slate-200 mt-0.5">{data.ATD || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Estimated Arrival (ETA)</span>
                    <p className="font-mono font-medium text-slate-200 mt-0.5">{data.ETA || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Actual Arrival (ATA)</span>
                    <p className="font-mono font-medium text-slate-200 mt-0.5">{data.ATA || '—'}</p>
                  </div>
                </div>
              </div>

              {/* Parties */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-800/40 border border-slate-800 rounded-xl p-3">
                  <span className="text-[11px] text-slate-500 uppercase font-semibold">Shipper</span>
                  <p className="font-medium text-white mt-0.5">{data.Shipper}</p>
                </div>
                <div className="bg-slate-800/40 border border-slate-800 rounded-xl p-3">
                  <span className="text-[11px] text-slate-500 uppercase font-semibold">Consignee</span>
                  <p className="font-medium text-white mt-0.5">{data.Consignee}</p>
                </div>
              </div>

              {/* Data Quality Flags */}
              {data.data_quality_flags && data.data_quality_flags.length > 0 && (
                <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-3.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-300 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    Data Quality Interventions Applied ({data.data_quality_flags.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.data_quality_flags.map((flag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-950/80 border border-amber-700/60 text-amber-200"
                      >
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/90 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
