import React from 'react';
import { Outlet, useLocation, useParams } from 'react-router-dom';
import { TopNav } from './TopNav';
import { InvestigationNav } from './InvestigationNav';

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const { id } = useParams<{ id: string }>();

  // Show investigation subnav if we are on an investigation detail route (e.g. /investigations/123/...)
  const isInvestigationDetail = Boolean(id) && location.pathname.startsWith('/investigations/');

  return (
    <div className="min-h-screen flex flex-col bg-background text-slate-100">
      <TopNav />
      {isInvestigationDetail && <InvestigationNav />}

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      <footer className="border-t border-surface-border bg-[#090c13] py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
          <span>ContradictIQ — Phase 0 Frozen Shared Contracts v1.0.0</span>
        </div>
        <div className="text-[11px] font-mono text-slate-600">
          "The LLM proposes. The code disposes."
        </div>
      </footer>
    </div>
  );
};
