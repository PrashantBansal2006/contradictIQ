import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutGrid, Search, ArrowRight } from 'lucide-react';
import api from '../../api/client';

export const TopNav: React.FC = () => {
  const location = useLocation();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const res = await api.checkHealth();
      if (mounted) setApiOnline(res.ok);
    };
    check();
    const t = setInterval(check, 10000);
    return () => { mounted = false; clearInterval(t); };
  }, []);

  const navLinks = [
    { to: '/', label: 'HOME', exact: true },
    { to: '/investigations', label: 'INVESTIGATIONS' },
    { to: '/investigations/inv-veridian-fy25/documents', label: 'DOCUMENTS' },
    { to: '/eval', label: 'BENCHMARKS' },
    { to: '/shared/demo-token', label: 'AUDIT LEDGER' },
  ];

  const isLinkActive = (to: string, exact?: boolean) => {
    if (exact) {
      return location.pathname === to;
    }
    return location.pathname.startsWith(to);
  };

  return (
    <header className="sticky top-0 z-50 bg-black/30 backdrop-blur-xl border-b border-white/10 px-6 lg:px-10 h-16 flex items-center justify-between transition-colors">
      {/* Brand on Left */}
      <div className="flex items-center space-x-3">
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded-lg bg-primary/15 border border-primary/40 flex items-center justify-center text-primary shadow-[0_0_12px_rgba(232,0,120,0.35)] group-hover:scale-105 transition">
            <LayoutGrid className="w-4 h-4" />
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="font-black text-lg tracking-wider text-white">CONTRADICT</span>
            <span className="font-mono font-black text-lg text-primary tracking-wider">IQ</span>
          </div>
        </Link>
      </div>

      {/* Center Nav Links */}
      <nav className="hidden md:flex items-center space-x-8 text-xs font-mono uppercase tracking-widest">
        {navLinks.map(({ to, label, exact }) => {
          const active = isLinkActive(to, exact);
          return (
            <Link
              key={to}
              to={to}
              className={`transition relative py-1 ${
                active
                  ? 'text-white font-bold after:content-[\'\'] after:absolute after:-bottom-2.5 after:left-1/2 after:-translate-x-1/2 after:w-5 after:h-[2px] after:bg-primary after:shadow-[0_0_8px_#e80078]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* Search */}
        <Link
          to="/investigations"
          className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-400 hover:text-white hover:border-primary/40 transition"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="font-mono text-[11px]">SEARCH</span>
        </Link>

        {/* API Health Dot */}
        <div
          title={`Backend: ${api.getBaseUrl()}`}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono border backdrop-blur-md transition ${
            apiOnline === true
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400'
              : apiOnline === false
              ? 'bg-rose-950/30 border-rose-500/30 text-rose-400'
              : 'bg-white/5 border-white/10 text-slate-400'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              apiOnline === true ? 'bg-emerald-400 animate-pulse' : apiOnline === false ? 'bg-rose-500' : 'bg-slate-500'
            }`}
          />
          <span className="hidden lg:inline">{apiOnline === true ? 'ONLINE' : apiOnline === false ? 'OFFLINE' : 'API'}</span>
        </div>

        {/* Launch Console / Join Us Pill Button */}
        <Link
          to="/investigations"
          className="inline-flex items-center space-x-2 px-5 py-2 rounded-full bg-primary hover:brightness-110 text-white text-xs font-bold uppercase tracking-wider shadow-[0_0_20px_rgba(232,0,120,0.5)] transition hover:scale-105"
        >
          <span>LAUNCH CONSOLE</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </header>
  );
};
