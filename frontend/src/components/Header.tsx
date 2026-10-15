import React from 'react';
import type { NetworkResponse } from '../types/network';

interface HeaderProps {
  network: NetworkResponse | null;
  backendStatus?: 'connected' | 'disconnected' | 'connecting';
  theme?: 'light' | 'dark';
}

export const Header: React.FC<HeaderProps> = ({
  theme = 'dark',
}) => {
  const isLight = theme === 'light';

  return (
    <header
      className={`mx-4 mt-3 px-6 py-2.5 rounded-2xl flex items-center justify-between z-[1200] shrink-0 select-none transition-all duration-300 ${
        isLight
          ? 'bg-white/80 backdrop-blur-2xl border border-slate-300/60 shadow-xl text-slate-900'
          : 'bg-slate-950/65 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.45)] text-slate-100'
      }`}
    >
      {/* Left: Brand Identity */}
      <div className="flex items-center">
        <span className="bg-gradient-to-r from-sky-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent text-lg font-bold tracking-tight font-sans">
          ProbRoute
        </span>
        <span className={`mx-2 font-light ${isLight ? 'text-slate-400' : 'text-slate-600'}`}>|</span>
        <span className={`text-sm font-medium font-sans ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
          Resilient Logistics Decision Support
        </span>
      </div>
    </header>
  );
};

export default Header;
