import React from 'react';
import { useParams } from 'react-router-dom';
import { LayoutDashboard, AlertTriangle, CheckCircle, XCircle, HelpCircle } from 'lucide-react';

export const DashboardTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/dashboard</span>
          </div>
          <h1 className="text-xl font-bold text-white">Investigation Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Aggregated findings, verification breakdown, and unresolved issues queue (FR-8.x).
          </p>
        </div>
      </div>

      {/* Metrics Summary Strip */}
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
            <AlertTriangle className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-2 font-mono">--</div>
          <p className="text-[11px] text-slate-400 mt-1">Extraction & parsing flags</p>
        </div>
      </div>

      {/* Placeholder Panel */}
      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <LayoutDashboard className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Dashboard Visualizations & Unresolved Queue</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Frontend skeleton router verified. Findings donut chart and priority action queue will be mounted here in Phase 4.
        </p>
      </div>
    </div>
  );
};
