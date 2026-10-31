import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  ShieldCheck, 
  BarChart3, 
  FolderKanban, 
  PlusCircle 
} from 'lucide-react';
import api from '../../api/client';

export const TopNav: React.FC = () => {
  const location = useLocation();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const testHealth = async () => {
      const res = await api.checkHealth();
      if (mounted) {
        setApiOnline(res.ok);
      }
    };
    testHealth();
    const interval = setInterval(testHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const isCurrent = (path: string) => {
    if (path === '/investigations' && (location.pathname === '/' || location.pathname.startsWith('/investigations'))) {
      return true;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-50 bg-[#0c101a]/95 backdrop-blur border-b border-surface-border px-4 lg:px-6 h-16 flex items-center justify-between">
      {/* Brand & Tagline */}
      <div className="flex items-center space-x-6">
        <Link to="/investigations" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white group-hover:text-blue-400 transition">
                Contradict<span className="text-blue-500">IQ</span>
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-mono tracking-wide rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                P0-SKELETON
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Evidence-First Financial Intelligence
            </p>
          </div>
        </Link>

        {/* Global Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          <Link
            to="/investigations"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              isCurrent('/investigations')
                ? 'bg-surface-hover text-white border border-surface-border'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface/50'
            }`}
          >
            <FolderKanban className="w-3.5 h-3.5" />
            <span>Investigations</span>
          </Link>

          <Link
            to="/eval"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              isCurrent('/eval')
                ? 'bg-surface-hover text-white border border-surface-border'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface/50'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Eval Harness</span>
          </Link>
        </nav>
      </div>

      {/* Right controls: Health status + Actions */}
      <div className="flex items-center space-x-3">
        {/* API Health Pill */}
        <div
          title={`Backend URL: ${api.getBaseUrl()}`}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border transition ${
            apiOnline === true
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
              : apiOnline === false
              ? 'bg-rose-950/40 border-rose-500/30 text-rose-400'
              : 'bg-slate-800/60 border-slate-700 text-slate-400'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              apiOnline === true
                ? 'bg-emerald-400 animate-pulse'
                : apiOnline === false
                ? 'bg-rose-500'
                : 'bg-slate-500'
            }`}
          />
          <span className="hidden sm:inline">API</span>
          <span>{apiOnline === true ? 'ONLINE' : apiOnline === false ? 'OFFLINE' : 'CHECKING'}</span>
        </div>

        {/* Quick New Investigation button */}
        <Link
          to="/investigations?create=true"
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition shadow-md shadow-blue-600/20"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Investigation</span>
        </Link>
      </div>
    </header>
  );
};
