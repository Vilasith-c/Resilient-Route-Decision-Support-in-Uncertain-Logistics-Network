import React from 'react';
import type { NetworkResponse } from '../types/network';

interface HeaderProps {
  network: NetworkResponse | null;
  backendStatus?: 'connected' | 'disconnected' | 'connecting';
  theme?: 'light' | 'dark';
}

export const Header: React.FC<HeaderProps> = ({
  network,
  backendStatus = 'connected',
  theme = 'dark',
}) => {
  const isLight = theme === 'light';
  const nodeCount = network?.nodes_summary.total_nodes ?? 43;
  const edgeCount = network?.edges_summary.total_directed_edges ?? 128;

  return (
    <header
      className={`mx-4 mt-3 px-6 py-2.5 rounded-2xl flex items-center justify-between z-[1200] shrink-0 select-none transition-all duration-300 ${
        isLight
          ? 'bg-white/80 backdrop-blur-2xl border border-slate-300/60 shadow-xl text-slate-900'
          : 'bg-slate-950/65 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.45)] text-slate-100'
      }`}
    >
      {/* Left: Brand & Institutional Academic Identity */}
      <div className="flex flex-col justify-center">
        <div className="flex items-center">
          <span className="bg-gradient-to-r from-sky-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent text-lg font-bold tracking-tight font-sans">
            ProbRoute
          </span>
          <span className={`mx-2 font-light ${isLight ? 'text-slate-400' : 'text-slate-600'}`}>|</span>
          <span className={`text-sm font-medium font-sans ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
            Resilient Logistics Decision Support
          </span>
        </div>
        <p className={`text-[11px] tracking-normal mt-0.5 font-sans ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
          Amrita School of Computing &middot; Department of CSE (AIE) &middot; Course: 22AIE301 Probabilistic Reasoning
        </p>
      </div>

      {/* Right: System Telemetry Badges */}
      <div className="flex items-center gap-2 text-xs">
        <div
          className={`px-2.5 py-1 rounded-full font-mono text-xs ${
            isLight
              ? 'bg-slate-100 border border-slate-300/80 text-slate-700'
              : 'bg-slate-900/80 border border-slate-800 text-slate-300'
          }`}
        >
          {nodeCount} Nodes &middot; {edgeCount} Edges
        </div>

        <div
          className={`px-2.5 py-1 rounded-full font-mono text-xs ${
            isLight
              ? 'bg-sky-100 text-sky-800 border border-sky-300 font-medium'
              : 'bg-sky-950/60 border border-sky-800/60 text-sky-300'
          }`}
        >
          Engine: 2-TBN Active
        </div>

        <div
          className={`px-2.5 py-1 rounded-full font-mono text-xs ${
            isLight
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-medium'
              : 'bg-emerald-950/60 border border-emerald-800/60 text-emerald-300'
          }`}
        >
          FSD Pruning: 65.7%
        </div>

        <div
          className={`px-2.5 py-1 rounded-full font-mono text-xs flex items-center gap-1.5 ${
            isLight
              ? 'bg-emerald-100/90 border border-emerald-300 text-emerald-800 font-medium'
              : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${isLight ? 'bg-emerald-600' : 'bg-emerald-400'}`} />
          <span>{backendStatus === 'connected' ? 'Online' : backendStatus === 'connecting' ? 'Syncing' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
