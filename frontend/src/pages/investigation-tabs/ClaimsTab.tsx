import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Quote, Plus, Play, Sparkles } from 'lucide-react';

export const ClaimsTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const placeholderClaims = [
    {
      id: 'claim-rev-grow-25',
      text: 'Veridian Foods revenue grew by 25% year-over-year in FY2025.',
      metric: 'revenue',
      type: 'GROWTH_YOY',
      period: 'FY2025',
      state: 'confirmed',
      origin: 'parsed',
    },
    {
      id: 'claim-margin-8-4',
      text: 'Operating margin expanded to 8.4% in FY25.',
      metric: 'operating_margin',
      type: 'MARGIN',
      period: 'FY2025',
      state: 'needs_confirmation',
      origin: 'ai',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <h1 className="text-xl font-bold text-white">Claims Management</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Assertions, management commentary, and press statements to be verified.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-surface border border-surface-border hover:border-primary/40 text-primary text-xs font-medium transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Extract Claims</span>
          </button>
          <button
            type="button"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-primary hover:brightness-110 text-white text-xs font-medium transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add Manual Claim</span>
          </button>
        </div>
      </div>

      <div className="rounded-xl bg-surface border border-surface-border overflow-hidden">
        <div className="px-4 py-3 border-b border-surface-border flex items-center justify-between text-xs font-semibold text-slate-300">
          <span>Stated Claims ({placeholderClaims.length})</span>
          <span className="text-slate-400 font-normal">Deterministic Verification Pending</span>
        </div>
        <div className="divide-y divide-surface-border">
          {placeholderClaims.map((claim) => (
            <div key={claim.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-primary/5 transition">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-primary/10 text-primary border border-primary/20">
                    {claim.type}
                  </span>
                  <span className="text-xs font-mono text-slate-400">Metric: {claim.metric}</span>
                  <span className="text-xs text-slate-500">·</span>
                  <span className="text-xs font-mono text-slate-400">{claim.period}</span>
                </div>
                <p className="text-sm font-medium text-slate-200">"{claim.text}"</p>
                <div className="text-[11px] text-slate-400 flex items-center space-x-2">
                  <span>Origin: <span className="font-mono">{claim.origin}</span></span>
                  <span>·</span>
                  <span>State: <span className="font-mono text-amber-400">{claim.state}</span></span>
                </div>
              </div>

              <div className="flex items-center space-x-2 self-start sm:self-center">
                <Link
                  to={`/investigations/${id}/findings`}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 text-xs font-medium transition"
                >
                  <Play className="w-3 h-3" />
                  <span>Verify Claim</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
