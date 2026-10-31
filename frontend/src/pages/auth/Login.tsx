import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogIn, Lock, Mail } from 'lucide-react';
import { PageBg } from '../../components/layout/PageBg';
import api from '../../api/client';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    api.setToken('mock_jwt_token_phase_0');
    navigate('/investigations');
  };

  return (
    <PageBg bg="home" className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full p-8 rounded-2xl bg-surface/80 backdrop-blur border border-surface-border shadow-2xl">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mx-auto mb-4 shadow-glow-sm">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Contradict<span className="text-primary">IQ</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">Financial Intelligence & Evidence Investigation</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@firm.com"
                className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-background border border-surface-border text-sm text-slate-200 placeholder-slate-600 focus:border-primary/60 focus:shadow-[0_0_0_2px_rgba(232,0,120,0.15)] outline-none transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-background border border-surface-border text-sm text-slate-200 placeholder-slate-600 focus:border-primary/60 focus:shadow-[0_0_0_2px_rgba(232,0,120,0.15)] outline-none transition"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-lg bg-primary hover:brightness-110 text-white font-medium text-sm transition flex items-center justify-center space-x-2 shadow-glow-sm mt-2"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Need an account?{' '}
          <Link to="/register" className="text-primary hover:underline">Register here</Link>
        </div>

        <div className="mt-6 pt-5 border-t border-surface-border text-center">
          <p className="text-[11px] font-mono text-slate-600">"The LLM proposes. The code disposes."</p>
        </div>
      </div>
    </PageBg>
  );
};
