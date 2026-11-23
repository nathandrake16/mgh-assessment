import React, { useState, useEffect } from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, ArrowUpDown, Clock, CheckCircle2, ShieldAlert } from 'lucide-react';
import { fetchShipments } from '../api';

export default function ShipmentSearch({ onSelectShipment }) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('');
  const [carrier, setCarrier] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 15;

  const [shipments, setShipments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadShipments = async () => {
    setLoading(true);
    try {
      const data = await fetchShipments({
        q: query,
        mode,
        carrier,
        status,
        limit: pageSize,
        offset: page * pageSize,
      });
      setShipments(data.items || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error("Failed to load shipments", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShipments();
  }, [query, mode, carrier, status, page]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-sm">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-700/60 gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            Shipment Search & Detail Inspector
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 font-medium">
              {totalCount} Total
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time filter and full inspection across all 500 cleaned shipments
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(0);
              }}
              placeholder="Search ID, party, port..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Mode Dropdown */}
          <select
            value={mode}
            onChange={(e) => {
              setMode(e.target.value);
              setPage(0);
            }}
            className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Modes</option>
            <option value="SEA">SEA (Ocean)</option>
            <option value="AIR">AIR (Air Cargo)</option>
          </select>

          {/* Status Dropdown */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(0);
            }}
            className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Delivered">Delivered</option>
            <option value="In Transit">In Transit</option>
          </select>

          {/* Clear Filters */}
          {(query || mode || status) && (
            <button
              onClick={() => {
                setQuery('');
                setMode('');
                setStatus('');
                setPage(0);
              }}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium px-2 py-1"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Shipments Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
            <tr>
              <th className="py-2.5 px-3">Shipment ID</th>
              <th className="py-2.5 px-3">Mode</th>
              <th className="py-2.5 px-3">Carrier</th>
              <th className="py-2.5 px-3">Trade Lane</th>
              <th className="py-2.5 px-3">Shipper</th>
              <th className="py-2.5 px-3">Consignee</th>
              <th className="py-2.5 px-3 text-center">Status</th>
              <th className="py-2.5 px-3 text-center">SLA Performance</th>
              <th className="py-2.5 px-3 text-center">Data Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              [...Array(6)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={9} className="py-3 px-3">
                    <div className="h-4 bg-slate-800 rounded w-full" />
                  </td>
                </tr>
              ))
            ) : shipments.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-500">
                  No shipments matching your filter criteria.
                </td>
              </tr>
            ) : (
              shipments.map((s) => {
                const isDelivered = s.Status === 'Delivered';
                const hasFlags = s.data_quality_flags && s.data_quality_flags.length > 0;

                return (
                  <tr
                    key={s['Shipment ID']}
                    onClick={() => onSelectShipment(s['Shipment ID'])}
                    className="hover:bg-slate-700/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 font-mono font-bold text-blue-400">
                      {s['Shipment ID']}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        s.Mode === 'AIR'
                          ? 'bg-purple-950 text-purple-300 border border-purple-800'
                          : 'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}>
                        {s.Mode} • {s['Container Mode']}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-medium text-slate-200">
                      {s.Carrier}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {s.trade_lane}
                    </td>
                    <td className="py-2.5 px-3 max-w-[130px] truncate" title={s.Shipper}>
                      {s.Shipper}
                    </td>
                    <td className="py-2.5 px-3 max-w-[130px] truncate" title={s.Consignee}>
                      {s.Consignee}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        isDelivered
                          ? 'bg-emerald-950/70 text-emerald-300 border-emerald-800/40'
                          : 'bg-amber-950/70 text-amber-300 border-amber-800/40'
                      }`}>
                        {s.Status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {s.is_evaluated ? (
                        s.on_time ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                            <CheckCircle2 className="w-3 h-3" />
                            On-Time
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                            <Clock className="w-3 h-3" />
                            +{s.delay_days}d
                          </span>
                        )
                      ) : (
                        <span className="text-[10px] text-slate-500 italic">
                          {s.ata_before_atd ? 'Impossible (Excluded)' : 'Pending ATA'}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {hasFlags ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium bg-amber-950/60 border border-amber-800/40 text-amber-300 rounded" title={s.data_quality_flags.join(', ')}>
                          <ShieldAlert className="w-3 h-3 text-amber-400" />
                          {s.data_quality_flags.length}
                        </span>
                      ) : (
                        <span className="text-slate-600 text-[10px]">Clean</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{page * pageSize + 1}</strong> to{' '}
            <strong className="text-white">{Math.min((page + 1) * pageSize, totalCount)}</strong> of{' '}
            <strong className="text-white">{totalCount}</strong> shipments
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 text-slate-300 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 text-slate-300 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
