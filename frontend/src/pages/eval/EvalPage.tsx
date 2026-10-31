import React from 'react';
import { BarChart3, Play, Target, Percent, ShieldCheck } from 'lucide-react';

export const EvalPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surface-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluation &amp; Benchmark Harness</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Measure precision, recall, and false-positive rate on labelled ground-truth test cases.
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary hover:brightness-110 text-white text-xs font-medium transition shadow-md shadow-primary/20"
        >
          <Play className="w-3.5 h-3.5" />
          <span>Run 60-Case Eval</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>False-Positive Rate</span>
            <Target className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono">&lt; 2.0%</div>
          <p className="text-[11px] text-slate-400 mt-1">Goal: prevent bogus contradiction alarms</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Accuracy on Traps</span>
            <Percent className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-primary mt-2 font-mono">100%</div>
          <p className="text-[11px] text-slate-400 mt-1">Quarter vs annual &amp; currency trap isolation</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Deterministic vs LLM Baseline</span>
            <ShieldCheck className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-primary mt-2 font-mono">Ready</div>
          <p className="text-[11px] text-slate-400 mt-1">Side-by-side comparison matrix</p>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-surface/50 border border-dashed border-surface-border text-center">
        <BarChart3 className="w-8 h-8 text-primary/40 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-200">Eval Confusion Matrix &amp; Case Viewer</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Confusion matrix, per-category breakdown (rounding, scale, restatements), and live benchmark runs will mount here.
        </p>
      </div>
    </div>
  );
};
