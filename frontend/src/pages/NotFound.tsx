import React from 'react';
import { Link } from 'react-router-dom';
import { HelpCircle, ArrowLeft } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
        <HelpCircle className="w-8 h-8" />
      </div>
      <h1 className="text-3xl font-bold text-white mb-2">404 — Route Not Found</h1>
      <p className="text-sm text-slate-400 max-w-md mb-6">
        The requested ContradictIQ workspace URL does not exist or has not been routed.
      </p>
      <Link
        to="/investigations"
        className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Investigations</span>
      </Link>
    </div>
  );
};
