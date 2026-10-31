import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, UserPlus, Lock, Mail, User } from 'lucide-react';
import api from '../../api/client';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    api.setToken('mock_jwt_token_phase_0');
    navigate('/investigations');
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="max-w-md w-full p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mx-auto mb-3">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-white">Create ContradictIQ Account</h2>
          <p className="text-xs text-slate-400 mt-1">Join the evidence-first intelligence workspace</p>
          <div className="text-[11px] font-mono text-blue-400 mt-2">ROUTE: /register</div>
        </div>

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Rajesh Sharma"
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-muted border border-surface-border text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@firm.com"
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-muted border border-surface-border text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-muted border border-surface-border text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition flex items-center justify-center space-x-2 shadow-lg shadow-blue-600/20"
          >
            <UserPlus className="w-4 h-4" />
            <span>Create Account</span>
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400">
          <span>Already registered? </span>
          <Link to="/login" className="text-blue-400 hover:underline">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  );
};
