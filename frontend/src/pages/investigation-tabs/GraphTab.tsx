import React from 'react';
import { useParams } from 'react-router-dom';
import { GitFork, Network } from 'lucide-react';

export const GraphTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <GitFork className="w-3.5 h-3.5" />
            <span>ROUTE: /investigations/{id}/graph</span>
          </div>
          <h1 className="text-xl font-bold text-white">Interactive Evidence Graph</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Visual dependency DAG connecting Claims, Metrics, Facts, Documents, and Conclusions (FR-16).
          </p>
        </div>
      </div>

      <div className="p-12 rounded-xl bg-surface/50 border border-dashed border-surface-border flex flex-col items-center justify-center min-h-[450px] text-center">
        <Network className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-sm font-semibold text-slate-200">React Flow DAG Graph Placeholder</h3>
        <p className="text-xs text-slate-400 max-w-md mt-1">
          Route verified for investigation <code className="font-mono text-blue-400">{id}</code>.
          React Flow dagre rendering of the `/investigations/{id}/graph` node/edge payload will be mounted here.
        </p>
      </div>
    </div>
  );
};
