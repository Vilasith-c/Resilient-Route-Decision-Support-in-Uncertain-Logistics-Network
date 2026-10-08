import React from 'react';
import { Truck, Activity, GitBranch } from 'lucide-react';
import type { NetworkResponse } from '../types/network';

interface HeaderProps {
  network: NetworkResponse | null;
  backendStatus?: 'connected' | 'disconnected' | 'connecting';
}

export const Header: React.FC<HeaderProps> = ({ network }) => {
  return (
    <header className="h-14 bg-slate-900/95 border-b border-slate-800 px-4 flex items-center justify-between z-10 select-none">
      {/* Brand & Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
          <Truck className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 text-sm tracking-wide">ProbRoute</h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800/60 font-semibold">
              v2.1 Tamil Nadu
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Probabilistic Route Resilience & Dynamic Decision Support
          </p>
        </div>
      </div>

      {/* Network Metrics Badges */}
      {network && (
        <div className="hidden lg:flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950/60 border border-slate-800/80 text-slate-300">
            <GitBranch className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-semibold text-slate-100">{network.nodes_summary.total_nodes}</span> Nodes
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">3 HQ &bull; 10 Hubs &bull; 30 WH</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950/60 border border-slate-800/80 text-slate-300">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-semibold text-slate-100">{network.edges_summary.total_directed_edges}</span> Edges
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">8 Macro Corridors</span>
          </div>
        </div>
      )}
    </header>
  );
};
