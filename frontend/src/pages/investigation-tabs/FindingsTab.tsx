import React from 'react';
import { useParams } from 'react-router-dom';
import { 
  CheckCircle2, 
  XCircle, 
  Calculator, 
  ShieldCheck, 
  FileCheck2, 
  ExternalLink 
} from 'lucide-react';

export const FindingsTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/findings</span>
          </div>
          <h1 className="text-xl font-bold text-white">Verification & Findings (Hero View)</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic verdict, formula trace calculation, comparability gate checklist, and evidence links (FR-5–7).
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-1 rounded text-xs font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
            Engine: v1.0.0 (Deterministic)
          </span>
        </div>
      </div>

      {/* Hero Finding Card Skeleton */}
      <div className="p-6 rounded-xl bg-surface border border-surface-border space-y-6">
        {/* Verdict Badge Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg bg-surface-muted border border-surface-border">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <XCircle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-rose-400">Conflicting</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  Severity: Material
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Claim asserts +25.0% YoY; Deterministic calculation yields +14.2% (Discrepancy: 10.8 pp exceeds tolerance 0.5 pp)
              </p>
            </div>
          </div>

          <div className="text-right sm:border-l sm:border-surface-border sm:pl-4">
            <div className="text-[11px] uppercase font-mono text-slate-400">Conclusion Strength</div>
            <div className="text-sm font-semibold text-rose-400 flex items-center space-x-1 justify-end">
              <ShieldCheck className="w-4 h-4" />
              <span>Disproved</span>
            </div>
          </div>
        </div>

        {/* 3-Column Hero Grid: Trace Stepper, Comparability Gate, Evidence Links */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* 1. Calculation Trace Stepper */}
          <div className="p-4 rounded-lg bg-surface-muted/50 border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <Calculator className="w-4 h-4 text-blue-400" />
              <span>Calculation Trace Stepper</span>
            </div>
            <div className="p-3 rounded bg-surface border border-surface-border font-mono text-xs space-y-2">
              <div className="text-slate-400">Formula: <span className="text-blue-400">growth_yoy</span></div>
              <div className="text-slate-300 text-[11px]">
                (₹3,400 cr - ₹2,977 cr) / ₹2,977 cr * 100
              </div>
              <div className="text-emerald-400 font-bold">= 14.21%</div>
            </div>
            <p className="text-[11px] text-slate-400">Every intermediate step is logged and immutable.</p>
          </div>

          {/* 2. Comparability Gate Checklist */}
          <div className="p-4 rounded-lg bg-surface-muted/50 border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>Comparability Gate (Gate 10.1)</span>
            </div>
            <ul className="text-xs space-y-1.5 font-mono">
              <li className="text-emerald-400 flex items-center space-x-1.5">
                <span>✓</span> <span className="text-slate-300">Metric: revenue == revenue</span>
              </li>
              <li className="text-emerald-400 flex items-center space-x-1.5">
                <span>✓</span> <span className="text-slate-300">Entity: Veridian Foods</span>
              </li>
              <li className="text-emerald-400 flex items-center space-x-1.5">
                <span>✓</span> <span className="text-slate-300">Period: FY2025 vs FY2024</span>
              </li>
              <li className="text-emerald-400 flex items-center space-x-1.5">
                <span>✓</span> <span className="text-slate-300">Currency: INR == INR</span>
              </li>
              <li className="text-emerald-400 flex items-center space-x-1.5">
                <span>✓</span> <span className="text-slate-300">Basis: Reported == Reported</span>
              </li>
            </ul>
          </div>

          {/* 3. Evidence Provenance Links */}
          <div className="p-4 rounded-lg bg-surface-muted/50 border border-surface-border space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <ExternalLink className="w-4 h-4 text-purple-400" />
              <span>Evidence Links (Receipts)</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded bg-surface border border-surface-border flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-200">Annual Report FY25</div>
                  <div className="text-[11px] text-slate-400 font-mono">Page 42, Table 3, Row 1</div>
                </div>
                <span className="text-xs text-blue-400 font-mono">₹3,400 cr</span>
              </div>
              <div className="p-2.5 rounded bg-surface border border-surface-border flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-200">Annual Report FY24</div>
                  <div className="text-[11px] text-slate-400 font-mono">Page 38, Table 2, Row 1</div>
                </div>
                <span className="text-xs text-blue-400 font-mono">₹2,977 cr</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
