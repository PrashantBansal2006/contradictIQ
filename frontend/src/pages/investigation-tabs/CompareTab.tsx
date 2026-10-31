import React from 'react';
import { useParams } from 'react-router-dom';
import { Columns3 } from 'lucide-react';

export const CompareTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <Columns3 className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/compare</span>
          </div>
          <h1 className="text-xl font-bold text-white">Side-by-Side Comparison</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-document metric alignment, restatement detection, and period variance analysis (FR-12).
          </p>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <Columns3 className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Side-by-Side Matrix Placeholder</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Select Document A and Document B to compare aligned metric × period data points with restatement flags.
        </p>
      </div>
    </div>
  );
};
