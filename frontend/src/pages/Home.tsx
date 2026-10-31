import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Play,
  Activity,
  Globe,
  ShieldCheck,
  Twitter,
  Disc as Discord,
  Instagram,
  Youtube,
} from 'lucide-react';

export const Home: React.FC = () => {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col justify-between px-4 sm:px-8 lg:px-12 py-6 overflow-hidden select-none">
      {/* 1. Left Vertical Margin Strip (matches screenshot left sidebar) */}
      <div className="hidden lg:flex fixed left-4 top-24 bottom-10 flex-col justify-between items-center z-20 pointer-events-none text-slate-400">
        <div className="flex flex-col items-center space-y-6 pointer-events-auto">
          <div className="text-[10px] font-mono tracking-widest uppercase [writing-mode:vertical-lr] rotate-180 text-slate-400">
            FOLLOW US
          </div>
          <div className="w-[1px] h-8 bg-white/20" />
          <a href="#twitter" className="hover:text-primary transition" aria-label="Twitter">
            <Twitter className="w-3.5 h-3.5" />
          </a>
          <a href="#discord" className="hover:text-primary transition" aria-label="Discord">
            <Discord className="w-3.5 h-3.5" />
          </a>
          <a href="#instagram" className="hover:text-primary transition" aria-label="Instagram">
            <Instagram className="w-3.5 h-3.5" />
          </a>
          <a href="#youtube" className="hover:text-primary transition" aria-label="YouTube">
            <Youtube className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="flex flex-col items-center space-y-2 pointer-events-auto">
          <div className="w-2 h-2 rounded-full bg-primary animate-ping" />
          <div className="text-[9px] font-mono tracking-widest uppercase [writing-mode:vertical-lr] rotate-180 text-primary">
            SCROLL DOWN
          </div>
          <div className="w-[1px] h-8 bg-primary/40" />
        </div>
      </div>

      {/* 2. Giant Futuristic Title across upper background (matching 'METAVERSE' in screenshot) */}
      <div className="absolute top-10 left-0 right-0 flex items-center justify-center pointer-events-none z-0">
        <h1 className="text-7xl sm:text-9xl md:text-[11rem] lg:text-[13rem] font-black uppercase tracking-tight text-white/[0.12] drop-shadow-[0_0_35px_rgba(232,0,120,0.25)] select-none">
          CONTRADICT<span className="text-primary/30">IQ</span>
        </h1>
      </div>

      {/* 3. Main Split Hero Content: Left & Right sides ONLY — Center is completely open for character! */}
      <div className="relative z-10 my-auto grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-16 items-center w-full max-w-7xl mx-auto py-8">
        {/* Left Side Component Block */}
        <div className="max-w-md space-y-4 text-left">
          <div className="text-xs font-mono tracking-widest text-primary uppercase flex items-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            <span>ENTER THE NEXT DIMENSION</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-primary uppercase tracking-tight drop-shadow-[0_0_15px_rgba(232,0,120,0.4)]">
            CYBER OF AUDIT
          </h2>

          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-light">
            Cross-document deterministic fact extraction, unit harmonization, and mathematical
            proof-chains for financial disclosures. Catching accounting traps with zero LLM hallucination.
          </p>

          <div className="pt-2">
            <Link
              to="/investigations"
              className="inline-flex items-center space-x-3 px-6 py-2.5 rounded-lg border border-primary/60 bg-black/20 backdrop-blur-md text-white hover:bg-primary/20 hover:border-primary text-xs font-mono uppercase tracking-wider transition shadow-[0_0_15px_rgba(232,0,120,0.25)] group"
            >
              <span>EXPLORE NOW</span>
              <span className="text-primary group-hover:translate-x-1 transition font-mono tracking-tighter">///</span>
            </Link>
          </div>
        </div>

        {/* Right Side Component Block */}
        <div className="max-w-md md:ml-auto space-y-4 text-left md:text-right">
          <div className="text-xs font-mono tracking-widest text-slate-400 uppercase flex items-center md:justify-end space-x-2">
            <span>WHERE EVIDENCE MEETS REALITY</span>
            <span className="text-primary font-mono font-bold">01 / 05</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-primary uppercase tracking-tight drop-shadow-[0_0_15px_rgba(232,0,120,0.4)]">
            THE FUTURE
          </h2>

          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-light">
            Tolerance-aware variance checks with strict comparability gates to isolate restatements
            from genuine contradictions. Every number tied to verified bounding-box evidence.
          </p>

          <div className="pt-2 flex md:justify-end">
            <Link
              to="/shared/demo-token"
              className="inline-flex items-center space-x-2.5 px-6 py-2.5 rounded-lg border border-primary/60 bg-black/20 backdrop-blur-md text-white hover:bg-primary/20 hover:border-primary text-xs font-mono uppercase tracking-wider transition shadow-[0_0_15px_rgba(232,0,120,0.25)] group"
            >
              <Play className="w-3.5 h-3.5 text-primary fill-primary group-hover:scale-110 transition" />
              <span>WATCH AUDIT TRACE</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 4. Bottom Floating Glass HUD Dock (Exact match to the screenshot bottom widget) */}
      <div className="relative z-10 w-full max-w-6xl mx-auto pt-4 pb-2">
        <div className="p-4 sm:p-5 rounded-2xl bg-black/30 backdrop-blur-xl border border-white/10 shadow-[0_0_35px_rgba(0,0,0,0.6)] flex flex-col md:flex-row items-center justify-between gap-6">
          {/* HUD Section 1: Radar Globe + Active Audits */}
          <div className="flex items-center space-x-4 w-full md:w-auto">
            <div className="w-14 h-14 rounded-full border border-primary/50 bg-primary/10 flex items-center justify-center text-primary relative shrink-0 shadow-[0_0_15px_rgba(232,0,120,0.35)]">
              <Globe className="w-7 h-7 text-primary/80 animate-pulse" />
              <div className="absolute inset-0 rounded-full border border-dashed border-primary/40 animate-spin" />
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                ACTIVE AUDITS
              </div>
              <div className="text-2xl font-bold font-mono text-white flex items-baseline space-x-1">
                <span className="text-primary font-black">+15</span>
                <span className="text-xs font-mono text-slate-400">ENTERPRISE</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                Continuous cross-filing validation running
              </p>
            </div>
          </div>

          {/* Separator */}
          <div className="hidden md:block w-[1px] h-12 bg-white/10" />

          {/* HUD Section 2: Verified Claims */}
          <div className="w-full md:w-auto">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              BENCHMARK TRAP ACCURACY
            </div>
            <div className="text-2xl font-bold font-mono text-white flex items-baseline space-x-1">
              <span className="text-primary font-black">100%</span>
              <span className="text-xs font-mono text-emerald-400">DETERMINISTIC</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
              0% false positives on scale &amp; currency traps
            </p>
          </div>

          {/* Separator */}
          <div className="hidden md:block w-[1px] h-12 bg-white/10" />

          {/* HUD Section 3: Cryptographic Ledger */}
          <div className="w-full md:w-auto">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center space-x-1">
              <ShieldCheck className="w-3 h-3 text-primary" />
              <span>AUDIT TRAIL INTEGRITY</span>
            </div>
            <div className="text-2xl font-bold font-mono text-white flex items-baseline space-x-1">
              <span className="text-primary font-black">SHA-256</span>
              <span className="text-xs font-mono text-slate-400">CHAINED</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
              Immutable tamper-evident proof records
            </p>
          </div>

          {/* Big Circular Action Arrow Button (matching the screenshot) */}
          <Link
            to="/investigations"
            aria-label="Launch Console"
            className="w-14 h-14 rounded-full border border-primary/70 bg-primary/10 hover:bg-primary text-primary hover:text-white transition flex items-center justify-center shrink-0 shadow-[0_0_25px_rgba(232,0,120,0.5)] group hover:scale-105"
          >
            <ArrowRight className="w-6 h-6 group-hover:translate-x-0.5 transition" />
          </Link>
        </div>
      </div>
    </div>
  );
};
