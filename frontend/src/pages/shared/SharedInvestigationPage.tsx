import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, Lock } from 'lucide-react';

export const SharedInvestigationPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-primary mb-1">
            <Lock className="w-3.5 h-3.5" />
            <span>READ-ONLY AUDIT MODE</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Judge &amp; Auditor Inspection View</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Cryptographically sealed read-only view of investigation findings, traces, and evidence.
          </p>
        </div>

        <Link
          to="/investigations"
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-surface border border-surface-border text-xs text-slate-300 hover:text-white hover:border-primary/40 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Workspace</span>
        </Link>
      </div>

      {/* Read-only banner */}
      <div className="flex items-center space-x-2 px-4 py-3 rounded-xl border border-primary/30 bg-primary/5 text-sm text-slate-300">
        <ShieldCheck className="w-4 h-4 text-primary shrink-0" />
        <span>This view is sealed. No mutations are permitted. All findings are cryptographically verifiable.</span>
      </div>

      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Judge Mode View</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Share Token: <code className="font-mono text-primary">{token}</code>.
          Complete provenance and hash-chained audit trail available without login or mutation permissions.
        </p>
      </div>
    </div>
  );
};
