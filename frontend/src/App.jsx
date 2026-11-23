import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import AuditDrawer from './components/AuditDrawer';
import KpiCards from './components/KpiCards';
import AskData from './components/AskData';
import TradeLanesSection from './components/TradeLanesSection';
import TopDelayedTable from './components/TopDelayedTable';
import ShipmentSearch from './components/ShipmentSearch';
import ShipmentDetailModal from './components/ShipmentDetailModal';
import { fetchSummary, fetchTradeLanes, fetchTopDelayed } from './api';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function App() {
  const [summary, setSummary] = useState(null);
  const [tradeLanes, setTradeLanes] = useState([]);
  const [topDelayed, setTopDelayed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals & Drawers
  const [isAuditOpen, setIsAuditOpen] = useState(false);
  const [selectedShipmentId, setSelectedShipmentId] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, lanesRes, delayedRes] = await Promise.all([
        fetchSummary(),
        fetchTradeLanes(),
        fetchTopDelayed(10),
      ]);
      setSummary(sumRes);
      setTradeLanes(lanesRes);
      setTopDelayed(delayedRes);
    } catch (err) {
      console.error('Dashboard load failure:', err);
      setError(err.message || 'Failed to connect to backend server at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Header */}
      <Header
        audit={summary?.data_quality_audit}
        onOpenAudit={() => setIsAuditOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="p-4 bg-rose-950/80 border border-rose-800 rounded-xl text-rose-200 text-xs flex items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <span>
                <strong>Connection Error:</strong> {error}. Ensure FastAPI backend is running on{' '}
                <code className="font-mono bg-rose-900/60 px-1.5 py-0.5 rounded">http://localhost:8000</code>.
              </span>
            </div>
            <button
              onClick={loadDashboardData}
              className="flex items-center gap-1.5 px-3 py-1 bg-rose-900 hover:bg-rose-800 text-white rounded-lg text-xs font-semibold transition-colors flex-shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
          </div>
        )}

        {/* Milestone 2: KPI Summary Cards */}
        <KpiCards summary={summary} loading={loading} />

        {/* Milestone 3: "Ask the Data" Natural Language Grounded Engine */}
        <AskData />

        {/* Analytics Grid: Trade Lanes (Milestone 4) & Top Delayed Shipments (Milestone 5) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TradeLanesSection tradeLanes={tradeLanes} loading={loading} />
          <TopDelayedTable
            delayedShipments={topDelayed}
            loading={loading}
            onSelectShipment={(id) => setSelectedShipmentId(id)}
          />
        </div>

        {/* Milestone 6: Shipment Search & Filter Inspector */}
        <ShipmentSearch onSelectShipment={(id) => setSelectedShipmentId(id)} />
      </main>

      {/* Data Quality Audit Drawer */}
      <AuditDrawer
        isOpen={isAuditOpen}
        onClose={() => setIsAuditOpen(false)}
        audit={summary?.data_quality_audit}
      />

      {/* Shipment Detail Modal */}
      {selectedShipmentId && (
        <ShipmentDetailModal
          shipmentId={selectedShipmentId}
          onClose={() => setSelectedShipmentId(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-5 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MGH Logistics Assessment MVP • 2026 H1 Operational Visibility</span>
          <span>FastAPI + Pandas Engine • React + Vite + Tailwind UI</span>
        </div>
      </footer>
    </div>
  );
}
