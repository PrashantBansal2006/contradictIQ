import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, UploadCloud, Eye } from 'lucide-react';

export const DocumentsTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const placeholderDocs = [
    {
      id: 'doc-annual-report-fy25',
      filename: 'Veridian_Annual_Report_FY25.pdf',
      mime: 'application/pdf',
      size: '4.2 MB',
      source_tier: 'T2',
      status: 'ready',
      fact_count: 42,
    },
    {
      id: 'doc-quarterly-csv',
      filename: 'Q1_Q4_Financial_Summary.csv',
      mime: 'text/csv',
      size: '184 KB',
      source_tier: 'T1',
      status: 'ready',
      fact_count: 18,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <FileText className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/documents</span>
          </div>
          <h1 className="text-xl font-bold text-white">Document Repository</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Uploaded regulatory filings, annual reports (PDF), and tables (CSV).
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* Documents List */}
      <div className="rounded-xl bg-surface border border-surface-border overflow-hidden">
        <div className="px-4 py-3 border-b border-surface-border text-xs font-semibold text-slate-300">
          Attached Documents ({placeholderDocs.length})
        </div>
        <div className="divide-y divide-surface-border">
          {placeholderDocs.map((doc) => (
            <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-surface-hover/50 transition">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-mono text-xs">
                  {doc.mime.includes('pdf') ? 'PDF' : 'CSV'}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-200">{doc.filename}</h4>
                  <div className="flex items-center space-x-3 text-xs text-slate-400 mt-0.5">
                    <span>{doc.size}</span>
                    <span>•</span>
                    <span className="font-mono text-[11px] text-blue-400">Tier: {doc.source_tier}</span>
                    <span>•</span>
                    <span>{doc.fact_count} Extracted Facts</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {doc.status}
                </span>
                <Link
                  to={`/investigations/${id}/documents/${doc.id}`}
                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-surface border border-surface-border hover:border-blue-500/40 text-xs text-slate-300 hover:text-white transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Viewer</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
