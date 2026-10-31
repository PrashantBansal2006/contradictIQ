import React from 'react';
import { useParams } from 'react-router-dom';
import { Network } from 'lucide-react';

export const GraphTab: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-xl font-bold text-white">Interactive Evidence Graph</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Visual dependency DAG connecting Claims, Metrics, Facts, Documents, and Conclusions.
        </p>
      </div>

      <div className="p-12 rounded-xl bg-surface/50 border border-dashed border-surface-border flex flex-col items-center justify-center min-h-[450px] text-center">
        <Network className="w-12 h-12 text-primary/40 mb-3" />
        <h3 className="text-sm font-semibold text-slate-200">Evidence DAG — Investigation <span className="font-mono text-primary">{id}</span></h3>
        <p className="text-xs text-slate-400 max-w-md mt-1">
          React Flow dagre graph of the node/edge evidence payload will be mounted here.
        </p>
      </div>
    </div>
  );
};
