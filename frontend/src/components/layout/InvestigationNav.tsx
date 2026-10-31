import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Quote, 
  CheckCircle2, 
  GitFork, 
  History, 
  Columns3,
  Share2
} from 'lucide-react';

export const InvestigationNav: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const investigationId = id || 'demo-inv';

  const navItems = [
    { label: 'Dashboard', path: `/investigations/${investigationId}/dashboard`, icon: LayoutDashboard },
    { label: 'Documents', path: `/investigations/${investigationId}/documents`, icon: FileText },
    { label: 'Claims', path: `/investigations/${investigationId}/claims`, icon: Quote },
    { label: 'Findings', path: `/investigations/${investigationId}/findings`, icon: CheckCircle2 },
    { label: 'Evidence Graph', path: `/investigations/${investigationId}/graph`, icon: GitFork },
    { label: 'Audit History', path: `/investigations/${investigationId}/history`, icon: History },
    { label: 'Compare', path: `/investigations/${investigationId}/compare`, icon: Columns3 },
  ];

  return (
    <div className="bg-[#0e1320] border-b border-surface-border px-4 lg:px-6">
      <div className="flex items-center justify-between overflow-x-auto">
        <nav className="flex space-x-1 py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.label}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium whitespace-nowrap transition ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface/60'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Share / Judge Mode shortcut */}
        <div className="hidden sm:flex items-center pl-4 py-2">
          <NavLink
            to={`/shared/sample-token`}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded text-[11px] font-medium text-slate-400 hover:text-slate-200 bg-surface/40 hover:bg-surface border border-surface-border transition"
            title="Read-only Judge / Auditor View"
          >
            <Share2 className="w-3 h-3 text-slate-400" />
            <span>Judge Mode</span>
          </NavLink>
        </div>
      </div>
    </div>
  );
};
