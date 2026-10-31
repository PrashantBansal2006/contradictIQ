import React from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban, Plus, Clock, FileText, ArrowRight } from 'lucide-react';

export const InvestigationsList: React.FC = () => {
  // Sample placeholder investigations to test routing into tabs
  const placeholderInvestigations = [
    {
      id: 'inv-veridian-2025',
      title: 'Veridian Foods Ltd — Annual Report FY25 Verification',
      entity_name: 'Veridian Foods Ltd',
      status: 'open',
      document_count: 2,
      claim_count: 5,
      updated_at: '2026-10-31',
    },
    {
      id: 'inv-apex-tech-2024',
      title: 'Apex Tech Corp — Q3 Revenue Growth & Margin Cross-Check',
      entity_name: 'Apex Tech Corp',
      status: 'in_review',
      document_count: 3,
      claim_count: 8,
      updated_at: '2026-10-30',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <FolderKanban className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Investigations Workspace</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage evidence-first financial cross-checking projects and filings.
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition shadow-lg shadow-blue-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Create Investigation</span>
        </button>
      </div>

      {/* Investigations Grid / List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {placeholderInvestigations.map((inv) => (
          <div
            key={inv.id}
            className="p-5 rounded-xl bg-surface border border-surface-border hover:border-blue-500/40 transition group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {inv.status}
                </span>
                <span className="text-xs text-slate-400 flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{inv.updated_at}</span>
                </span>
              </div>
              <h2 className="font-semibold text-base text-slate-100 group-hover:text-blue-400 transition">
                {inv.title}
              </h2>
              <p className="text-xs text-slate-400 mt-1">Entity: {inv.entity_name}</p>

              <div className="flex items-center space-x-4 mt-4 text-xs text-slate-400">
                <span className="flex items-center space-x-1">
                  <FileText className="w-3.5 h-3.5" />
                  <span>{inv.document_count} Documents</span>
                </span>
                <span>{inv.claim_count} Claims</span>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-surface-border/60 flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400">ID: {inv.id}</span>
              <Link
                to={`/investigations/${inv.id}/dashboard`}
                className="inline-flex items-center space-x-1.5 text-xs font-medium text-blue-400 hover:text-blue-300 transition"
              >
                <span>Open Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
