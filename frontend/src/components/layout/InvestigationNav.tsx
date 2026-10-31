import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import { LayoutDashboard, FileText, Quote, CheckCircle2, GitFork, History, Columns3, Share2 } from 'lucide-react';

export const InvestigationNav: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const base = `/investigations/${id || 'inv-veridian-fy25'}`;

  const tabs = [
    { label: 'Dashboard', to: `${base}/dashboard`, Icon: LayoutDashboard },
    { label: 'Documents', to: `${base}/documents`, Icon: FileText },
    { label: 'Claims', to: `${base}/claims`, Icon: Quote },
    { label: 'Findings', to: `${base}/findings`, Icon: CheckCircle2 },
    { label: 'Evidence Graph', to: `${base}/graph`, Icon: GitFork },
    { label: 'Audit History', to: `${base}/history`, Icon: History },
    { label: 'Compare', to: `${base}/compare`, Icon: Columns3 },
  ];

  return (
    <div className="bg-black/25 backdrop-blur-md border-b border-white/10 px-6 lg:px-10">
      <div className="flex items-center justify-between overflow-x-auto">
        <nav className="flex space-x-1">
          {tabs.map(({ label, to, Icon }) => (
            <NavLink
              key={label}
              to={to}
              className={({ isActive }) =>
                `flex items-center space-x-1.5 px-3.5 py-3 text-xs font-mono uppercase tracking-wider whitespace-nowrap transition border-b-2 ${
                  isActive
                    ? 'border-primary text-primary font-bold'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`
              }
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <NavLink
          to="/shared/sample-token"
          className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 ml-4 rounded-full text-[11px] font-mono text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition whitespace-nowrap"
          title="Read-only Judge Mode"
        >
          <Share2 className="w-3 h-3" />
          <span>Judge Mode</span>
        </NavLink>
      </div>
    </div>
  );
};
