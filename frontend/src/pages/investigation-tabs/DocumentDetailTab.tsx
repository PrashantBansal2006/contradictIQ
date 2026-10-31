import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, ArrowLeft, Layers } from 'lucide-react';

export const DocumentDetailTab: React.FC = () => {
  const { id, docId } = useParams<{ id: string; docId: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <Link to={`/investigations/${id}/documents`} className="hover:underline flex items-center space-x-1">
              <ArrowLeft className="w-3 h-3" />
              <span>Back to Documents</span>
            </Link>
            <span>/</span>
            <span>ROUTE: /investigations/{id}/documents/{docId}</span>
          </div>
          <h1 className="text-xl font-bold text-white">Document Viewer & Extracted Facts</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Synchronized page text/PDF viewer with bounding-box fact highlights (FR-3.2, FR-11).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Document viewer placeholder */}
        <div className="lg:col-span-2 p-8 rounded-xl bg-surface border border-dashed border-surface-border flex flex-col items-center justify-center min-h-[400px] text-center">
          <FileText className="w-10 h-10 text-slate-400 mb-2" />
          <h3 className="text-sm font-semibold text-slate-200">PDF / Page Viewer Skeleton</h3>
          <p className="text-xs text-slate-400 max-w-sm mt-1">
            Document ID: <code className="font-mono text-blue-400">{docId}</code>
          </p>
          <span className="mt-3 px-2 py-0.5 rounded text-[11px] font-mono text-slate-400 bg-surface-muted border border-surface-border">
            Phase 4 viewer & bounding-box highlight overlay mounting point
          </span>
        </div>

        {/* Right: Extracted facts sidebar placeholder */}
        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 pb-2 border-b border-surface-border">
            <Layers className="w-4 h-4 text-blue-400" />
            <span>Extracted Facts (Provenance)</span>
          </div>
          <p className="text-xs text-slate-400">
            Facts extracted via deterministic tables, CSV rows, or LLM grounding will be listed here with clickable page/bbox locators.
          </p>
        </div>
      </div>
    </div>
  );
};
