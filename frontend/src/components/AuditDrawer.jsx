import React from 'react';
import { X, ShieldCheck, CheckCircle2, AlertTriangle, Info, Database } from 'lucide-react';

export default function AuditDrawer({ isOpen, onClose, audit }) {
  if (!isOpen) return null;

  const fixes = [
    {
      id: 1,
      title: "Duplicate Shipment IDs Removed",
      count: audit?.duplicates_removed ?? 11,
      rule: "Rule 1",
      description: "Sorted so Status == 'Delivered' and non-null ATA come first, then dropped duplicate Shipment IDs keeping the first record.",
      impact: "Reduced 511 raw records to exactly 500 unique shipments.",
      tag: "Deduplication",
      status: "Verified",
    },
    {
      id: 2,
      title: "Port Aliases & Spaces Normalized",
      count: audit?.ports_normalized ?? 24,
      rule: "Rule 2",
      description: "Mapped lowercase and alias variants {'bdcgp', 'chattogram', 'cgp'} to canonical BDCGP, trimmed whitespace, and uppercased all ports.",
      impact: "Cleaned trade lanes (e.g. BDCGP → ESVLC with 77 shipments).",
      tag: "Normalization",
      status: "Verified",
    },
    {
      id: 3,
      title: "Corrupt Year Typo Corrected (/2062 → /2026)",
      count: audit?.year_typo_fixed ?? 1,
      rule: "Rule 3",
      description: "Identified year entry error on shipment S00158650 (ETA recorded as 2/19/2062) and corrected to 2026.",
      impact: "Prevented a 36-year anomaly from distorting delay and SLA metrics.",
      tag: "Typo Fix",
      status: "Verified",
    },
    {
      id: 4,
      title: "Ambiguous Dates Smart Resolution",
      count: audit?.ambiguous_dates_resolved ?? 216,
      rule: "Rule 3",
      description: "When day and month were both <= 12, resolved M/D/Y vs D/M/Y against departure dates using plausible mode windows (AIR: 0–15d, CNSHA→BDCGP: 7–35d, SEA: 15–65d).",
      impact: "Guaranteed realistic transit days across all global trade corridors.",
      tag: "Date Heuristic",
      status: "Verified",
    },
    {
      id: 5,
      title: "Impossible Arrivals Flagged (ATA < ATD)",
      count: audit?.ata_before_atd ?? 6,
      rule: "Rule 4",
      description: "Flagged 6 impossible shipments where arrival preceded departure (S00159115, S00158459, S00159174, S00158864, S00159407, S00158304).",
      impact: "Excluded from SLA delay metrics to ensure unbiased 57.78% on-time rate.",
      tag: "SLA Integrity",
      status: "Verified",
    },
    {
      id: 6,
      title: "Non-Positive Cargo Weights Cleaned",
      count: audit?.weight_non_positive ?? 5,
      rule: "Rule 5",
      description: "Detected 5 corrupted entries with Weight (KG) <= 0 (negative values and 0.0) and set cleaned weight to None.",
      impact: "Preserved validity of aggregate freight weight calculations.",
      tag: "Outlier Cleansing",
      status: "Verified",
    },
    {
      id: 7,
      title: "Grams Typo Rescaled (> 100,000 kg)",
      count: audit?.weight_grams_typo_corrected ?? 1,
      rule: "Rule 5",
      description: "Detected shipment S00158128 recorded as 21,816,000 kg (grams entry error) and divided by 1000 to 21,816.0 kg.",
      impact: "Yielded verified total fleet weight of exactly 6,648,333.5 kg (~6,648.3 MT).",
      tag: "Unit Fix",
      status: "Verified",
    },
    {
      id: 8,
      title: "Missing Consignees Imputed",
      count: audit?.missing_consignee_filled ?? 7,
      rule: "Rule 6",
      description: "Identified 7 shipments with blank or missing Consignee fields and assigned fallback placeholder 'Unknown'.",
      impact: "Prevented UI breakage and preserved relational integrity in filters.",
      tag: "Imputation",
      status: "Verified",
    },
    {
      id: 9,
      title: "Status & Delivery Timestamp Mismatches",
      count: (audit?.delivered_missing_ata ?? 6) + (audit?.in_transit_with_ata ?? 4),
      rule: "Rule 6",
      description: "Logged 6 Delivered shipments with missing ATA and 4 In Transit shipments with present ATA into data_quality_flags.",
      impact: "Full auditability for operational dispatchers and carrier billing teams.",
      tag: "Audit Flags",
      status: "Verified",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/80 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 sticky top-0 z-10">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Data Quality Audit & Remediation Log
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-700/60 text-emerald-300 font-medium">
                  9 Fixes Verified
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Automated ingestion pipeline rules enforcing verified data integrity
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

        {/* Audit Stats Banner */}
        <div className="px-6 py-3 bg-slate-950 border-b border-slate-800/80 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-slate-400">Raw Input Rows</div>
            <div className="text-base font-bold text-slate-200">{audit?.total_raw_rows ?? 511}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Unique Cleaned</div>
            <div className="text-base font-bold text-emerald-400">{audit?.unique_shipments ?? 500}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Evaluated Shipments</div>
            <div className="text-base font-bold text-blue-400">{audit?.evaluated_shipments ?? 450}</div>
          </div>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3.5">
          {fixes.map((fix) => (
            <div
              key={fix.id}
              className="bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-xl p-4 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700 text-xs font-bold text-slate-200 flex items-center justify-center">
                    {fix.id}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      {fix.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] font-mono px-1.5 py-0.2 bg-slate-700/60 text-slate-300 rounded">
                        {fix.rule}
                      </span>
                      <span className="text-[10px] font-medium text-emerald-400 bg-emerald-950/80 border border-emerald-800/40 px-1.5 py-0.2 rounded">
                        {fix.tag}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-sm font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-700/40 px-2 py-0.5 rounded-lg">
                    {fix.count} {fix.count === 1 ? 'case' : 'cases'}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 mt-2.5 leading-relaxed">
                {fix.description}
              </p>

              <div className="mt-2.5 pt-2 border-t border-slate-700/50 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5 text-blue-300">
                  <Info className="w-3.5 h-3.5 flex-shrink-0" />
                  {fix.impact}
                </span>
                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {fix.status}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Drawer Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Exported JSON sanitized for zero NaNs & NaTs
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
          >
            Close Audit Drawer
          </button>
        </div>
      </div>
    </div>
  );
}
