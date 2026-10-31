import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, ArrowLeft, Layers } from 'lucide-react';

export const DocumentDetailTab: React.FC = () => {
  const { id, docId } = useParams<{ id: string; docId: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <Link
            to={`/investigations/${id}/documents`}
            className="inline-flex items-center space-x-1 text-xs font-mono text-primary hover:underline mb-2"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>Back to Documents</span>
          </Link>
          <h1 className="text-xl font-bold text-white">Document Viewer &amp; Extracted Facts</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Synchronized page text/PDF viewer with bounding-box fact highlights.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-8 rounded-xl bg-surface border border-dashed border-surface-border flex flex-col items-center justify-center min-h-[400px] text-center">
          <FileText className="w-10 h-10 text-slate-400 mb-2" />
          <h3 className="text-sm font-semibold text-slate-200">PDF / Page Viewer Skeleton</h3>
          <p className="text-xs text-slate-400 max-w-sm mt-1">
            Document ID: <code className="font-mono text-primary">{docId}</code>
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 pb-2 border-b border-surface-border">
            <Layers className="w-4 h-4 text-primary" />
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
