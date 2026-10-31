import React from 'react';
import { Outlet, useLocation, useParams } from 'react-router-dom';
import { TopNav } from './TopNav';
import { InvestigationNav } from './InvestigationNav';
import { PageBg } from './PageBg';

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const { id } = useParams<{ id: string }>();
  const isInvDetail = Boolean(id) && location.pathname.startsWith('/investigations/');
  const isHome = location.pathname === '/';

  return (
    <PageBg bg={isHome ? 'home' : 'app'} className="flex flex-col min-h-screen">
      {/* TopNav is uniformly rendered across all pages */}
      <TopNav />
      {isInvDetail && <InvestigationNav />}

      <main className={`flex-1 w-full ${isHome ? 'flex flex-col' : 'max-w-7xl mx-auto p-4 sm:p-6 lg:p-8'}`}>
        <Outlet />
      </main>

      {!isHome && (
        <footer className="border-t border-white/10 bg-black/30 backdrop-blur-md py-3.5 px-6 lg:px-10 text-center text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <span className="font-mono text-slate-300">CONTRADICTIQ // DETERMINISTIC REASONING ENGINE</span>
          </div>
          <div className="font-mono text-[11px] text-slate-500">
            "The LLM proposes. The code disposes."
          </div>
        </footer>
      )}
    </PageBg>
  );
};
