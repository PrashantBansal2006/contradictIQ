import React from 'react';
import { LayoutDashboard, AlertTriangle, CheckCircle, XCircle, HelpCircle } from 'lucide-react';

export const DashboardTab: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-xl font-bold text-white">Investigation Dashboard</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Aggregated findings, verification breakdown, and unresolved issues queue.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Consistent Claims</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono">--</div>
          <p className="text-[11px] text-slate-400 mt-1">Direct math match within tolerance</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Conflicting Claims</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2 font-mono">--</div>
          <p className="text-[11px] text-slate-400 mt-1">Disproved with calculation trace</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Inconclusive / Unresolved</span>
            <HelpCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2 font-mono">--</div>
          <p className="text-[11px] text-slate-400 mt-1">Comparability or evidence gap</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Data Warnings</span>
            <AlertTriangle className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-primary mt-2 font-mono">--</div>
          <p className="text-[11px] text-slate-400 mt-1">Extraction &amp; parsing flags</p>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <LayoutDashboard className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Dashboard Visualizations &amp; Unresolved Queue</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Findings donut chart and priority action queue will be mounted here.
        </p>
      </div>
    </div>
  );
};
