import React from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban, Plus, Clock, FileText, ArrowRight, Tag } from 'lucide-react';

const STATUS_STYLES: Record<string, string> = {
  open: 'bg-primary/10 border-primary/30 text-primary',
  in_review: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  concluded: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
};

const placeholderInvestigations = [
  { id: 'inv-veridian-2025', title: 'Veridian Foods Ltd — Annual Report FY25 Verification', entity_name: 'Veridian Foods Ltd', status: 'open', document_count: 2, claim_count: 5, updated_at: '2026-10-31' },
  { id: 'inv-apex-tech-2024', title: 'Apex Tech Corp — Q3 Revenue Growth & Margin Cross-Check', entity_name: 'Apex Tech Corp', status: 'in_review', document_count: 3, claim_count: 8, updated_at: '2026-10-30' },
  { id: 'inv-meridian-2025', title: 'Meridian Pharma — EBITDA Margin Claims vs Regulatory Filings', entity_name: 'Meridian Pharma Ltd', status: 'concluded', document_count: 5, claim_count: 12, updated_at: '2026-10-28' },
];

export const InvestigationsList: React.FC = () => (
  <div className="space-y-6">
    {/* Header */}
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-5">
      <div>
        <div className="flex items-center space-x-2 text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">
          <FolderKanban className="w-3 h-3" />
          <span>Investigations Workspace</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Active Investigations</h1>
        <p className="text-sm text-slate-400 mt-1">Manage evidence-first financial verification projects.</p>
      </div>
      <button type="button" className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary hover:brightness-110 text-white text-sm font-medium transition shadow-glow-sm whitespace-nowrap">
        <Plus className="w-4 h-4" />
        <span>New Investigation</span>
      </button>
    </div>

    {/* Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {placeholderInvestigations.map((inv) => (
        <div
          key={inv.id}
          className="p-5 rounded-xl bg-surface border border-surface-border hover:border-primary/30 hover:shadow-[0_0_16px_rgba(232,0,120,0.08)] transition flex flex-col justify-between group"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider border ${STATUS_STYLES[inv.status] ?? STATUS_STYLES.open}`}>
                {inv.status.replace('_', ' ')}
              </span>
              <span className="text-xs text-slate-500 flex items-center space-x-1 font-mono">
                <Clock className="w-3 h-3" />
                <span>{inv.updated_at}</span>
              </span>
            </div>

            <h2 className="font-semibold text-sm text-slate-100 group-hover:text-primary transition leading-snug">
              {inv.title}
            </h2>
            <p className="text-xs text-slate-500 mt-1 flex items-center space-x-1">
              <Tag className="w-3 h-3" />
              <span>{inv.entity_name}</span>
            </p>

            <div className="flex items-center space-x-4 mt-4 text-xs text-slate-400">
              <span className="flex items-center space-x-1">
                <FileText className="w-3.5 h-3.5" />
                <span>{inv.document_count} docs</span>
              </span>
              <span>{inv.claim_count} claims</span>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-surface-border/60 flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-600 truncate max-w-[100px]">{inv.id}</span>
            <Link
              to={`/investigations/${inv.id}/dashboard`}
              className="inline-flex items-center space-x-1.5 text-xs font-medium text-primary hover:text-white transition"
            >
              <span>Open</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      ))}
    </div>
  </div>
);
