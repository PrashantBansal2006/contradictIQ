import React from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Calculator, ShieldCheck, FileCheck2, ExternalLink } from 'lucide-react';

const VerdictRow: React.FC<{ label: string; ok: boolean }> = ({ label, ok }) => (
  <li className={`flex items-center space-x-1.5 text-xs ${ok ? 'text-emerald-400' : 'text-rose-400'}`}>
    <span>{ok ? '✓' : '✗'}</span>
    <span className="text-slate-300">{label}</span>
  </li>
);

export const FindingsTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Findings — {id}</span>
          </div>
          <h1 className="text-xl font-bold text-white">Verification & Findings</h1>
          <p className="text-xs text-slate-400 mt-0.5">Deterministic verdict, formula trace, comparability gate, evidence links.</p>
        </div>
        <span className="px-2.5 py-1 rounded text-xs font-mono bg-surface border border-surface-border text-slate-400">
          Engine v0.1.0
        </span>
      </div>

      {/* Finding Card */}
      <div className="p-6 rounded-xl bg-surface border border-surface-border space-y-5">
        {/* Verdict strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg bg-surface-muted border border-rose-500/20">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <XCircle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-rose-400">Conflicting</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase border bg-rose-500/10 border-rose-500/20 text-rose-300">Material</span>
              </div>
              <p className="text-xs text-slate-400">Claim: +25.0% YoY · Calculated: +14.2% · Discrepancy 10.8 pp exceeds tolerance 0.5 pp</p>
            </div>
          </div>
          <div className="text-right sm:border-l sm:border-surface-border sm:pl-4">
            <div className="text-[10px] uppercase font-mono text-slate-500">Conclusion Strength</div>
            <div className="text-sm font-semibold text-rose-400 flex items-center space-x-1 justify-end mt-0.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Disproved</span>
            </div>
          </div>
        </div>

        {/* 3-column grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Calculation Trace */}
          <div className="p-4 rounded-lg bg-surface-muted border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <Calculator className="w-4 h-4 text-primary" />
              <span>Calculation Trace</span>
            </div>
            <div className="p-3 rounded bg-background border border-surface-border font-mono text-xs space-y-1.5">
              <div className="text-slate-400">Formula: <span className="text-primary">growth_yoy</span></div>
              <div className="text-slate-300 text-[11px]">(₹3,400 cr − ₹2,977 cr) / ₹2,977 cr × 100</div>
              <div className="text-emerald-400 font-bold">= 14.21%</div>
              <div className="text-rose-400 text-[11px]">Claim stated: 25.0%</div>
            </div>
          </div>

          {/* Comparability Gate */}
          <div className="p-4 rounded-lg bg-surface-muted border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>Comparability Gate</span>
            </div>
            <ul className="space-y-1.5 font-mono">
              {[
                { label: 'Metric: revenue == revenue', ok: true },
                { label: 'Entity: Veridian Foods', ok: true },
                { label: 'Period: FY2025 vs FY2024', ok: true },
                { label: 'Currency: INR == INR', ok: true },
                { label: 'Basis: Reported == Reported', ok: true },
              ].map((r) => <VerdictRow key={r.label} {...r} />)}
            </ul>
          </div>

          {/* Evidence Links */}
          <div className="p-4 rounded-lg bg-surface-muted border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <ExternalLink className="w-4 h-4 text-purple-400" />
              <span>Evidence Links</span>
            </div>
            <div className="space-y-2 text-xs">
              {[
                { doc: 'Annual Report FY25', loc: 'Page 42, Table 3, Row 1', val: '₹3,400 cr' },
                { doc: 'Annual Report FY24', loc: 'Page 38, Table 2, Row 1', val: '₹2,977 cr' },
              ].map(({ doc, loc, val }) => (
                <div key={doc} className="p-2.5 rounded bg-background border border-surface-border flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-200">{doc}</div>
                    <div className="text-[11px] text-slate-500 font-mono">{loc}</div>
                  </div>
                  <span className="text-xs text-primary font-mono">{val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
