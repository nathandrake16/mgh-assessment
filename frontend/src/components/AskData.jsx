import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  Bot,
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Code2,
  Table as TableIcon,
  Copy,
  Check
} from 'lucide-react';
import { askData } from '../api';

const SAMPLE_QUESTIONS = [
  "Which carrier is delayed the least?",
  "Which carrier is delayed the most?",
  "What are the top 5 trade lanes?",
  "Show delayed ocean shipments",
  "Tell me about shipment S00158545",
];

export default function AskData() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (qText) => {
    const query = qText || question;
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await askData(query.trim());
      setResponse(res);
    } catch (err) {
      setError(err.message || 'Failed to get answer from server.');
    } finally {
      setLoading(false);
    }
  };

  const handleChipClick = (q) => {
    setQuestion(q);
    handleSubmit(q);
  };

  const copySql = () => {
    if (response?.generated_sql) {
      navigator.clipboard.writeText(response.generated_sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/70 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
      {/* Title & Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-700/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl text-white shadow-md">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Milestone 3 — Ask the Data
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-950/80 border border-indigo-700/50 text-indigo-300">
                Text-to-SQL + Grounded AI
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Translates natural language questions into database SQL queries via Gemini 3.5 Flash Lite & executes against PostgreSQL
            </p>
          </div>
        </div>

        {response && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Engine:</span>
            {response.engine && response.engine.includes('gemini') ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-purple-950/80 text-purple-300 border border-purple-700/50">
                <Bot className="w-3.5 h-3.5 text-purple-400" />
                Gemini 3.5 Flash Lite (Text-to-SQL)
              </span>
            ) : response.engine && response.engine.includes('postgres') ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-700/50">
                <Database className="w-3.5 h-3.5 text-emerald-400" />
                PostgreSQL Text-to-SQL
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-950/80 text-blue-300 border border-blue-700/50">
                <Database className="w-3.5 h-3.5 text-blue-400" />
                Text-to-SQL Engine
              </span>
            )}
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="mt-5"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about carriers, routes, delays, or shipment IDs (e.g. 'least delayed carrier')..."
            className="w-full pl-4 pr-24 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="absolute right-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium text-xs rounded-lg transition-all flex items-center gap-1.5 shadow-sm"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Querying...</span>
              </>
            ) : (
              <>
                <span>Ask</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Sample Question Chips */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400 flex items-center gap-1">
          Suggestions:
        </span>
        {SAMPLE_QUESTIONS.map((chip, i) => (
          <button
            key={i}
            type="button"
            onClick={() => handleChipClick(chip)}
            disabled={loading}
            className="text-xs px-3 py-1 rounded-lg bg-slate-900/70 hover:bg-slate-700/70 border border-slate-700/60 text-slate-300 hover:text-white transition-all text-left disabled:opacity-50"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mt-4 p-3 bg-red-950/60 border border-red-800/50 rounded-xl flex items-center gap-2.5 text-xs text-red-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Response Box */}
      {response && (
        <div className="mt-5 p-5 bg-slate-900/90 border border-slate-700/60 rounded-xl animate-in fade-in duration-200 space-y-4">
          {/* Natural Language Answer */}
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-600/20 rounded-lg text-blue-400 mt-0.5">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Grounded Answer
              </h4>
              <p className="text-sm text-slate-200 leading-relaxed font-normal">
                {response.answer}
              </p>
            </div>
          </div>

          {/* Generated SQL Query */}
          {response.generated_sql && (
            <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Code2 className="w-4 h-4 text-indigo-400" />
                  Generated PostgreSQL Query
                </span>
                <button
                  type="button"
                  onClick={copySql}
                  className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700/80 transition-colors"
                  title="Copy SQL query"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy SQL</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-2.5 bg-slate-900/90 rounded-lg text-xs font-mono text-indigo-300 overflow-x-auto whitespace-pre-wrap border border-slate-800/80">
                <code>{response.generated_sql}</code>
              </pre>
            </div>
          )}

          {/* Database Query Results Table Preview */}
          {response.sql_rows && response.sql_rows.length > 0 && (
            <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <TableIcon className="w-4 h-4 text-emerald-400" />
                  Database Query Execution Results ({response.sql_rows.length} {response.sql_rows.length === 1 ? 'row' : 'rows'})
                </span>
                <span className="text-[10px] text-emerald-400/80 font-mono">live db fetch</span>
              </div>
              <div className="overflow-x-auto border border-slate-800 rounded-lg max-h-56">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      {Object.keys(response.sql_rows[0]).map((col) => (
                        <th key={col} className="px-3 py-1.5 font-medium whitespace-nowrap text-[11px]">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300 font-mono text-[11px]">
                    {response.sql_rows.slice(0, 10).map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        {Object.keys(response.sql_rows[0]).map((col) => (
                          <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                            {row[col] !== null && row[col] !== undefined ? (
                              String(row[col])
                            ) : (
                              <span className="text-slate-600 italic">null</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {response.sql_rows.length > 10 && (
                <div className="text-[10px] text-slate-500 mt-1.5 text-right">
                  Showing first 10 of {response.sql_rows.length} rows
                </div>
              )}
            </div>
          )}

          {/* Supporting Data Metrics */}
          {response.supporting_data && response.supporting_data.length > 0 && (
            <div className="pt-2 border-t border-slate-800">
              <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Verified Supporting Metrics
              </h5>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
                {response.supporting_data.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5"
                  >
                    <div className="text-[11px] text-slate-400 truncate">
                      {item.label}
                    </div>
                    <div className="text-xs font-bold text-slate-100 mt-0.5 truncate">
                      {String(item.value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
