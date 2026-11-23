import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { Route, Table, BarChart3, TrendingUp } from 'lucide-react';

const COLORS = [
  '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#4f46e5',
  '#6366f1', '#7c3aed', '#8b5cf6', '#a855f7', '#d946ef'
];

export default function TradeLanesSection({ tradeLanes = [], loading }) {
  const [viewMode, setViewMode] = useState('chart'); // 'chart' or 'table'

  if (loading) {
    return (
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 h-96 animate-pulse" />
    );
  }

  const top10 = tradeLanes.slice(0, 10);

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-700/60 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400">
            <Route className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Shipments per Trade Lane
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950 border border-blue-800/50 text-blue-300 font-medium">
                {tradeLanes.length} Lanes Tracked
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Volume and on-time performance distribution across major corridors
            </p>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex items-center bg-slate-900 border border-slate-700/70 rounded-lg p-0.5 self-start sm:self-auto">
          <button
            onClick={() => setViewMode('chart')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              viewMode === 'chart'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Top 10 Chart
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              viewMode === 'table'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            All Lanes Table
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="mt-5">
        {viewMode === 'chart' ? (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={top10}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 95, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                />
                <YAxis
                  type="category"
                  dataKey="trade_lane"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                  width={90}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(51, 65, 85, 0.4)' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl text-xs">
                          <p className="font-bold text-white border-b border-slate-800 pb-1 mb-1.5">
                            {data.trade_lane}
                          </p>
                          <div className="space-y-1 text-slate-300">
                            <p className="flex justify-between gap-4">
                              <span>Volume:</span>
                              <strong className="text-white">{data.total_shipments} shipments</strong>
                            </p>
                            <p className="flex justify-between gap-4">
                              <span>On-Time Rate:</span>
                              <strong className="text-emerald-400">{data.on_time_percentage ?? 'N/A'}%</strong>
                            </p>
                            <p className="flex justify-between gap-4">
                              <span>Avg Delay:</span>
                              <strong className="text-amber-400">{data.average_delay_days ?? 'N/A'} days</strong>
                            </p>
                            <p className="flex justify-between gap-4">
                              <span>Cargo Weight:</span>
                              <strong className="text-blue-300">{Math.round(data.total_weight_kg).toLocaleString()} kg</strong>
                            </p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="total_shipments" radius={[0, 4, 4, 0]}>
                  {top10.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-slate-700">
                <tr>
                  <th className="py-2.5 px-3">Trade Lane</th>
                  <th className="py-2.5 px-3 text-center">Shipments</th>
                  <th className="py-2.5 px-3 text-center">On-Time %</th>
                  <th className="py-2.5 px-3 text-center">Avg Delay</th>
                  <th className="py-2.5 px-3 text-right">Weight (KG)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {tradeLanes.map((lane, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                    <td className="py-2 px-3 font-semibold text-white">
                      {lane.trade_lane}
                    </td>
                    <td className="py-2 px-3 text-center font-bold text-blue-400">
                      {lane.total_shipments}
                    </td>
                    <td className="py-2 px-3 text-center">
                      {lane.on_time_percentage !== null ? (
                        <span
                          className={`font-semibold ${
                            lane.on_time_percentage >= 60
                              ? 'text-emerald-400'
                              : lane.on_time_percentage >= 45
                              ? 'text-amber-400'
                              : 'text-rose-400'
                          }`}
                        >
                          {lane.on_time_percentage}%
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-center">
                      {lane.average_delay_days !== null ? (
                        <span>{lane.average_delay_days}d</span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-400 font-mono">
                      {Math.round(lane.total_weight_kg).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
