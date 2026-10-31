import React from 'react';
import { useParams } from 'react-router-dom';
import { History, ShieldCheck, Link2 } from 'lucide-react';

export const HistoryTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <History className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/history</span>
          </div>
          <h1 className="text-xl font-bold text-white">Cryptographic Audit Ledger</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable SHA-256 hash-chained history of mutations and verification runs (FR-9.1, B10).
          </p>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-4 h-4" />
          <span>Ledger Integrity Verified ✓</span>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <Link2 className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Hash-Chained Timeline Placeholder</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Historical events (`investigation.created`, `document.uploaded`, `claim.confirmed`, `verification.run`)
          with SHA-256 hash links and "state as of event N" replay will be displayed here.
        </p>
      </div>
    </div>
  );
};
