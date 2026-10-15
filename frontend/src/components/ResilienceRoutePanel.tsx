import React, { useState, useMemo } from 'react';
import type { TimelineFrame, CandidateRoute, EngineTimelineResult, NetworkResponse } from '../types/network';

interface ResilienceRoutePanelProps {
  timelineResult: EngineTimelineResult | null;
  currentFrame: TimelineFrame | null;
  selectedRoute?: CandidateRoute | null;
  onSelectRoute?: (route: CandidateRoute) => void;
  selectedRouteNodes?: string[];
  network?: NetworkResponse | null;
  theme?: 'light' | 'dark';
  sourceNode?: string;
  targetNode?: string;
  onCorridorChange?: (source: string, target: string) => void;
}

const CORRIDOR_OPTIONS = [
  {
    group: 'Strategic HQs',
    items: [
      { id: 'HQ_Chennai', label: 'HQ Chennai (Northern Core)' },
      { id: 'HQ_Coimbatore', label: 'HQ Coimbatore (Western Hub)' },
      { id: 'HQ_Madurai', label: 'HQ Madurai (Southern Hub)' },
    ],
  },
  {
    group: 'Regional Transit Hubs',
    items: [
      { id: 'Hub_Tiruvallur', label: 'Hub Tiruvallur (North Gateway)' },
      { id: 'Hub_Vellore', label: 'Hub Vellore (NH48 Transit)' },
      { id: 'Hub_Salem', label: 'Hub Salem (Central Crossroads)' },
      { id: 'Hub_Erode', label: 'Hub Erode (Textile Corridor)' },
      { id: 'Hub_Tiruchirappalli', label: 'Hub Tiruchirappalli (Trichy Central)' },
      { id: 'Hub_Thanjavur', label: 'Hub Thanjavur (Delta Terminal)' },
      { id: 'Hub_Cuddalore', label: 'Hub Cuddalore (East Coast Port)' },
      { id: 'Hub_Dindigul', label: 'Hub Dindigul (Southern Junction)' },
      { id: 'Hub_Tirunelveli', label: 'Hub Tirunelveli (Deep South Hub)' },
      { id: 'Hub_Thoothukudi', label: 'Hub Thoothukudi (Major Port Terminal)' },
    ],
  },
  {
    group: 'Industrial & Trade Warehouses',
    items: [
      { id: 'WH_01_Gummidipoondi', label: 'WH 01 Gummidipoondi (Border Depot)' },
      { id: 'WH_02_Sriperumbudur', label: 'WH 02 Sriperumbudur (Auto Hub Depot)' },
      { id: 'WH_03_Arakkonam', label: 'WH 03 Arakkonam (Railhead Depot)' },
      { id: 'WH_04_Ranipet', label: 'WH 04 Ranipet (Leather Cluster)' },
      { id: 'WH_05_Ambur', label: 'WH 05 Ambur (Trade Warehouse)' },
      { id: 'WH_06_Tirupattur', label: 'WH 06 Tirupattur (Transit Depot)' },
      { id: 'WH_07_Attur', label: 'WH 07 Attur (Eastern Salem Depot)' },
      { id: 'WH_08_Mettur', label: 'WH 08 Mettur (Thermal Power Terminal)' },
      { id: 'WH_09_Namakkal', label: 'WH 09 Namakkal (Logistics Depot)' },
      { id: 'WH_10_Bhavani', label: 'WH 10 Bhavani (River Basin Depot)' },
      { id: 'WH_11_Perundurai', label: 'WH 11 Perundurai (SIPCOT Depot)' },
      { id: 'WH_12_Tiruppur', label: 'WH 12 Tiruppur (Knitwear Freight Depot)' },
      { id: 'WH_13_Pollachi', label: 'WH 13 Pollachi (Agro Depot)' },
      { id: 'WH_14_Udumalaipettai', label: 'WH 14 Udumalaipettai (Wind Corridor Depot)' },
      { id: 'WH_15_Mettupalayam', label: 'WH 15 Mettupalayam (Nilgiris Gateway)' },
      { id: 'WH_16_Manapparai', label: 'WH 16 Manapparai (Southern Trichy Depot)' },
      { id: 'WH_17_Thuraiyur', label: 'WH 17 Thuraiyur (Northern Trichy Depot)' },
      { id: 'WH_18_Pudukkottai', label: 'WH 18 Pudukkottai (Transit Depot)' },
      { id: 'WH_19_Kumbakonam', label: 'WH 19 Kumbakonam (Delta Core Depot)' },
      { id: 'WH_20_Mayiladuthurai', label: 'WH 20 Mayiladuthurai (Coastal Delta Depot)' },
      { id: 'WH_21_Nagapattinam', label: 'WH 21 Nagapattinam (Port Terminal Depot)' },
      { id: 'WH_22_Panruti', label: 'WH 22 Panruti (Commercial Depot)' },
      { id: 'WH_23_Chidambaram', label: 'WH 23 Chidambaram (Delta Depot)' },
      { id: 'WH_24_Villupuram', label: 'WH 24 Villupuram (Crossroad Depot)' },
      { id: 'WH_25_Palani', label: 'WH 25 Palani (Hill Depot)' },
      { id: 'WH_26_Batlagundu', label: 'WH 26 Batlagundu (Spices Warehouse)' },
      { id: 'WH_27_Virudhunagar', label: 'WH 27 Virudhunagar (Trade Depot)' },
      { id: 'WH_28_Kovilpatti', label: 'WH 28 Kovilpatti (Industrial Depot)' },
      { id: 'WH_29_Tenkasi', label: 'WH 29 Tenkasi (Western Ghats Depot)' },
      { id: 'WH_30_Nagercoil', label: 'WH 30 Nagercoil (Southernmost Gateway)' },
    ],
  },
];

const PRESET_CORRIDORS = [
  {
    source: 'HQ_Chennai',
    target: 'HQ_Madurai',
    label: 'Chennai ⇄ Madurai',
    desc: 'North-South Core',
  },
  {
    source: 'HQ_Chennai',
    target: 'HQ_Coimbatore',
    label: 'Chennai ⇄ Coimbatore',
    desc: 'East-West Industrial',
  },
  {
    source: 'HQ_Coimbatore',
    target: 'HQ_Madurai',
    label: 'Coimbatore ⇄ Madurai',
    desc: 'Western-Southern Artery',
  },
  {
    source: 'HQ_Chennai',
    target: 'WH_30_Nagercoil',
    label: 'Chennai ⇄ Nagercoil',
    desc: 'Full State Spine',
  },
];

type ActiveTab = 'route' | 'beliefs' | 'scorecard';

export const ResilienceRoutePanel: React.FC<ResilienceRoutePanelProps> = ({
  timelineResult,
  currentFrame,
  selectedRoute,
  onSelectRoute,
  selectedRouteNodes = [],
  network,
  theme = 'dark',
  sourceNode = 'HQ_Chennai',
  targetNode = 'HQ_Madurai',
  onCorridorChange,
}) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('route');
  const isLight = theme === 'light';

  const scorecard = timelineResult?.resilience_scorecard;
  const candidateRoutes = timelineResult?.primary_rerouted_solutions || [];
  const activeRoute = selectedRoute || candidateRoutes[0] || null;

  // Build edge lookup table for leg distances and times
  const edgeLookup = useMemo(() => {
    const map = new Map<string, { distance_km: number; travel_time_hr: number }>();
    if (network?.routes) {
      for (const r of network.routes) {
        map.set(`${r.source}->${r.target}`, { distance_km: r.distance_km, travel_time_hr: r.travel_time_hr });
        map.set(`${r.target}->${r.source}`, { distance_km: r.distance_km, travel_time_hr: r.travel_time_hr });
      }
    }
    return map;
  }, [network]);

  // Compute route legs for stepper path breakdown (prioritize backend-computed simulation legs)
  const routeLegs = useMemo(() => {
    if (!activeRoute || activeRoute.path_nodes.length === 0) return [];

    // If backend provided simulation-degraded legs, use them directly
    if (activeRoute.legs && activeRoute.legs.length > 0) {
      return activeRoute.legs;
    }

    const legs: Array<{ from: string; to: string; distance_km: number; travel_time_hr: number }> = [];
    const nodes = activeRoute.path_nodes;
    const totalHops = Math.max(1, nodes.length - 1);
    const avgDist = (activeRoute.travel_time_hr * 62) / totalHops;
    const avgTime = activeRoute.travel_time_hr / totalHops;

    for (let i = 0; i < nodes.length - 1; i++) {
      const u = nodes[i];
      const v = nodes[i + 1];
      const match = edgeLookup.get(`${u}->${v}`);
      legs.push({
        from: u,
        to: v,
        distance_km: match ? match.distance_km : Number(avgDist.toFixed(1)),
        travel_time_hr: match ? match.travel_time_hr : Number(avgTime.toFixed(2)),
      });
    }
    return legs;
  }, [activeRoute, edgeLookup]);

  // Top vulnerable/affected hubs extracted from live posteriors
  const topVulnerableHubs = useMemo(() => {
    const posteriors = currentFrame?.node_posteriors;
    if (posteriors && Object.keys(posteriors).length > 0) {
      const list = Object.entries(posteriors).map(([nodeId, probs]) => {
        const pCritical = probs['High'] ?? probs['Critical'] ?? 0;
        const pWarning = probs['Medium'] ?? probs['Warning'] ?? 0;
        const pNominal = probs['Low'] ?? probs['Nominal'] ?? 0;
        return {
          nodeId,
          pNominal: Number(pNominal.toFixed(3)),
          pWarning: Number(pWarning.toFixed(3)),
          pCritical: Number(pCritical.toFixed(3)),
        };
      });
      // Sort by highest disruption severity (pCritical)
      list.sort((a, b) => b.pCritical - a.pCritical);
      return list.slice(0, 5);
    }

    // Analytical reference values prior to simulation trigger
    return [
      { nodeId: 'Hub_Cuddalore', pNominal: 0.18, pWarning: 0.32, pCritical: 0.50 },
      { nodeId: 'Hub_Nagapattinam', pNominal: 0.22, pWarning: 0.35, pCritical: 0.43 },
      { nodeId: 'Hub_Thanjavur', pNominal: 0.38, pWarning: 0.38, pCritical: 0.24 },
      { nodeId: 'HQ_Chennai', pNominal: 0.72, pWarning: 0.22, pCritical: 0.06 },
      { nodeId: 'Hub_Coimbatore', pNominal: 0.84, pWarning: 0.13, pCritical: 0.03 },
    ];
  }, [currentFrame]);

  // Circular Radial Gauge Math
  const resilienceVal = scorecard?.overall_resilience_index ?? (timelineResult ? 0.616 : 0.679);
  const gaugeRadius = 50;
  const gaugeCircumference = 2 * Math.PI * gaugeRadius;
  const strokeDashoffset = gaugeCircumference - resilienceVal * gaugeCircumference;
  const resilienceStatusTag =
    resilienceVal >= 0.75
      ? '[HIGH RESILIENCE]'
      : resilienceVal >= 0.50
      ? '[MODERATE RESILIENCE]'
      : '[DEGRADED RESILIENCE]';

  // Hero metric values
  const transitValue = activeRoute ? `${activeRoute.travel_time_hr.toFixed(2)}h` : '16.95h';
  const reliabilityValue = activeRoute
    ? `${(activeRoute.on_time_reliability_alpha * 100).toFixed(1)}%`
    : '48.5%';
  const riskValue = activeRoute
    ? `${(activeRoute.disruption_prob * 100).toFixed(1)}%`
    : '51.5%';

  return (
    <div
      className={`w-[440px] rounded-2xl p-4 shadow-2xl flex flex-col gap-3.5 h-full overflow-hidden font-sans select-none transition-all duration-300 ${
        isLight
          ? 'bg-white/80 backdrop-blur-2xl border border-slate-300/60 shadow-2xl text-slate-900'
          : 'bg-slate-950/75 backdrop-blur-xl border border-white/10 text-slate-200'
      }`}
    >
      {/* 1. Sleek Segmented Navigation Tabs */}
      <div
        className={`grid grid-cols-3 gap-1 p-1 rounded-xl border text-xs shrink-0 font-sans transition-colors ${
          isLight
            ? 'bg-slate-200/80 border-slate-300/80'
            : 'bg-slate-900/80 border-slate-800'
        }`}
      >
        <button
          type="button"
          onClick={() => setActiveTab('route')}
          className={`py-1.5 px-2 rounded-lg text-center font-medium transition-colors ${
            activeTab === 'route'
              ? isLight
                ? 'bg-white text-sky-800 border border-sky-300 shadow-sm font-semibold'
                : 'bg-sky-500/20 border border-sky-500/50 text-sky-200 shadow-sm'
              : isLight
              ? 'text-slate-600 hover:text-slate-900'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Route Analytics
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('beliefs')}
          className={`py-1.5 px-2 rounded-lg text-center font-medium transition-colors ${
            activeTab === 'beliefs'
              ? isLight
                ? 'bg-white text-sky-800 border border-sky-300 shadow-sm font-semibold'
                : 'bg-sky-500/20 border border-sky-500/50 text-sky-200 shadow-sm'
              : isLight
              ? 'text-slate-600 hover:text-slate-900'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Bayesian Beliefs
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('scorecard')}
          className={`py-1.5 px-2 rounded-lg text-center font-medium transition-colors ${
            activeTab === 'scorecard'
              ? isLight
                ? 'bg-white text-sky-800 border border-sky-300 shadow-sm font-semibold'
                : 'bg-sky-500/20 border border-sky-500/50 text-sky-200 shadow-sm'
              : isLight
              ? 'text-slate-600 hover:text-slate-900'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Resilience Scorecard
        </button>
      </div>

      {/* 2. Scrollable Body */}
      <div className="flex-1 overflow-y-auto space-y-3.5 pr-0.5">
        {/* ================================================================= */}
        {/* TAB 1: ROUTE ANALYTICS & STOCHASTIC DOMINANCE                     */}
        {/* ================================================================= */}
        {activeTab === 'route' && (
          <div className="space-y-3.5">
            {/* Dynamic Strategic Freight Corridor Selector */}
            <div
              className={`p-3 rounded-xl border transition-colors space-y-2.5 shadow-sm ${
                isLight
                  ? 'bg-slate-100/90 border-slate-200/90 text-slate-800'
                  : 'bg-slate-900/70 border border-slate-800/80 text-slate-200'
              }`}
            >
              <div className={`flex items-center justify-between pb-1.5 border-b ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
                <span className={`text-xs font-semibold uppercase tracking-wider font-sans ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>
                  Strategic Freight Corridor
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${isLight ? 'bg-sky-100 text-sky-800 border border-sky-300' : 'bg-sky-950/80 text-sky-300 border border-sky-800/60'}`}>
                  RSPP-A* Dynamic
                </span>
              </div>

              {/* Origin -> Swap -> Destination Selectors */}
              <div className="flex items-center gap-2">
                {/* Origin Dropdown */}
                <div className="flex-1 min-w-0">
                  <label className={`block text-[10px] font-mono uppercase mb-1 font-semibold ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                    From (Origin)
                  </label>
                  <select
                    value={sourceNode}
                    onChange={(e) => onCorridorChange?.(e.target.value, targetNode)}
                    className={`w-full text-xs font-mono py-1.5 px-2 rounded-lg border outline-none cursor-pointer transition-colors ${
                      isLight
                        ? 'bg-white border-slate-300 text-slate-900 focus:border-sky-500'
                        : 'bg-slate-950 border-slate-700 text-slate-100 focus:border-sky-400'
                    }`}
                  >
                    {CORRIDOR_OPTIONS.map((grp) => (
                      <optgroup key={grp.group} label={grp.group}>
                        {grp.items.map((item) => (
                          <option key={item.id} value={item.id} disabled={item.id === targetNode}>
                            {item.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                {/* Swap Button */}
                <div className="flex flex-col items-center justify-end pt-3">
                  <button
                    type="button"
                    onClick={() => onCorridorChange?.(targetNode, sourceNode)}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm transition-all active:scale-90 border shadow-xs cursor-pointer ${
                      isLight
                        ? 'bg-white border-slate-300 text-slate-700 hover:text-sky-600 hover:border-sky-400'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-sky-300 hover:border-sky-500'
                    }`}
                    title="Swap Origin and Destination"
                  >
                    ⇄
                  </button>
                </div>

                {/* Destination Dropdown */}
                <div className="flex-1 min-w-0">
                  <label className={`block text-[10px] font-mono uppercase mb-1 font-semibold ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                    To (Destination)
                  </label>
                  <select
                    value={targetNode}
                    onChange={(e) => onCorridorChange?.(sourceNode, e.target.value)}
                    className={`w-full text-xs font-mono py-1.5 px-2 rounded-lg border outline-none cursor-pointer transition-colors ${
                      isLight
                        ? 'bg-white border-slate-300 text-slate-900 focus:border-sky-500'
                        : 'bg-slate-950 border-slate-700 text-slate-100 focus:border-sky-400'
                    }`}
                  >
                    {CORRIDOR_OPTIONS.map((grp) => (
                      <optgroup key={grp.group} label={grp.group}>
                        {grp.items.map((item) => (
                          <option key={item.id} value={item.id} disabled={item.id === sourceNode}>
                            {item.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              </div>

              {/* Quick Preset Corridor Pills */}
              <div className="space-y-1 pt-1">
                <span className={`block text-[9.5px] font-mono uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Quick Strategic Corridors
                </span>
                <div className="grid grid-cols-2 gap-1.5">
                  {PRESET_CORRIDORS.map((preset) => {
                    const isSelected =
                      (sourceNode === preset.source && targetNode === preset.target) ||
                      (sourceNode === preset.target && targetNode === preset.source);

                    return (
                      <button
                        key={preset.label}
                        type="button"
                        onClick={() => onCorridorChange?.(preset.source, preset.target)}
                        className={`p-1.5 rounded-lg text-left transition-all cursor-pointer border ${
                          isSelected
                            ? isLight
                              ? 'bg-sky-50 border-sky-400 text-sky-950 shadow-xs font-semibold'
                              : 'bg-sky-500/20 border-sky-400/80 text-sky-200 shadow-xs font-semibold'
                            : isLight
                            ? 'bg-white/80 border-slate-200/90 hover:bg-slate-200/60 text-slate-700'
                            : 'bg-slate-800/50 border-slate-700/60 hover:bg-slate-800 text-slate-300'
                        }`}
                      >
                        <div className="text-[11px] font-sans font-medium">
                          {preset.label}
                        </div>
                        <div className={`text-[9px] leading-tight ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                          {preset.desc}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Hero Probability Cards (3-column grid) */}
            <div className="grid grid-cols-3 gap-2">
              <div
                className={`p-2.5 rounded-xl border transition-colors ${
                  isLight
                    ? 'bg-slate-100/80 border-slate-200/80 text-slate-800'
                    : 'bg-slate-900/70 border border-slate-800/80 text-slate-200'
                }`}
              >
                <div className={`text-[10px] uppercase tracking-tight font-sans ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Expected Transit
                </div>
                <div className={`text-base font-bold font-mono mt-0.5 ${isLight ? 'text-sky-700' : 'text-sky-300'}`}>
                  E[T] = {transitValue}
                </div>
              </div>

              <div
                className={`p-2.5 rounded-xl border transition-colors ${
                  isLight
                    ? 'bg-slate-100/80 border-slate-200/80 text-slate-800'
                    : 'bg-slate-900/70 border border-slate-800/80 text-slate-200'
                }`}
              >
                <div className={`text-[10px] uppercase tracking-tight font-sans ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  On-Time Reliability
                </div>
                <div className={`text-base font-bold font-mono mt-0.5 ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  P(T &le; &tau;) &ge; {reliabilityValue}
                </div>
              </div>

              <div
                className={`p-2.5 rounded-xl border transition-colors ${
                  isLight
                    ? 'bg-slate-100/80 border-slate-200/80 text-slate-800'
                    : 'bg-slate-900/70 border border-slate-800/80 text-slate-200'
                }`}
              >
                <div className={`text-[10px] uppercase tracking-tight font-sans ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Disruption Risk
                </div>
                <div className={`text-base font-bold font-mono mt-0.5 ${isLight ? 'text-rose-700' : 'text-rose-400'}`}>
                  P(Disr | E) = {riskValue}
                </div>
              </div>
            </div>

            {/* Strategic Pareto Routing Alternatives (Interactive Decision Support) */}
            {candidateRoutes.length > 0 && (
              <div
                className={`p-3 rounded-xl border space-y-2 transition-colors ${
                  isLight
                    ? 'bg-slate-100/80 border-slate-200/80'
                    : 'bg-slate-900/70 border border-slate-800/80'
                }`}
              >
                <div className={`flex items-center justify-between border-b pb-1.5 ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
                  <span className={`text-xs font-semibold font-sans flex items-center gap-1.5 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                    <span>Pareto Routing Strategies</span>
                    <span className="text-[10px] font-mono opacity-60">({candidateRoutes.length} Available)</span>
                  </span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${isLight ? 'bg-sky-100 text-sky-800 font-medium' : 'bg-slate-800 text-sky-300'}`}>
                    FSD Stochastic Dominance
                  </span>
                </div>

                <div className="space-y-1.5">
                  {candidateRoutes.map((cr, idx) => {
                    const isSelected =
                      activeRoute?.route === cr.route ||
                      selectedRouteNodes.join(',') === cr.path_nodes.join(',');

                    const isDetour = cr.strategy_tag?.toLowerCase().includes('detour');
                    const isHighShock = cr.disruption_prob >= 0.35;

                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => onSelectRoute && onSelectRoute(cr)}
                        className={`w-full text-left p-2 rounded-xl border transition-all cursor-pointer ${
                          isSelected
                            ? isLight
                              ? 'bg-sky-50/90 border-sky-500 ring-2 ring-sky-400/30 text-slate-900 shadow-sm'
                              : 'bg-sky-950/60 border-sky-400 ring-1 ring-sky-500/40 text-slate-100 shadow-md'
                            : isLight
                            ? 'bg-white/80 border-slate-200 hover:border-slate-300 text-slate-800'
                            : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                        }`}
                      >
                        <div className="flex justify-between items-center text-xs font-sans">
                          <div className="flex items-center gap-1.5">
                            <span className="font-bold">
                              {isDetour ? '🛡️ Strategy #' + (idx + 1) : isHighShock ? '⚡ Strategy #' + (idx + 1) : 'Corridor #' + (idx + 1)}
                            </span>
                            {cr.is_recommended && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">
                                Recommended
                              </span>
                            )}
                          </div>
                          <span className="font-mono text-xs font-semibold">
                            E[T] = {cr.travel_time_hr.toFixed(2)}h
                          </span>
                        </div>

                        {cr.strategy_tag && (
                          <div className={`text-[10.5px] font-medium mt-0.5 ${
                            isDetour
                              ? isLight ? 'text-emerald-700 font-semibold' : 'text-emerald-400 font-semibold'
                              : isHighShock
                              ? isLight ? 'text-amber-700 font-semibold' : 'text-amber-400 font-semibold'
                              : isLight ? 'text-sky-700' : 'text-sky-400'
                          }`}>
                            {cr.strategy_tag}
                          </div>
                        )}

                        <div className={`flex justify-between items-center text-[10px] font-mono mt-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                          <span>Reliability: {(cr.on_time_reliability_alpha * 100).toFixed(1)}%</span>
                          <span className={isHighShock ? (isLight ? 'text-rose-600 font-semibold' : 'text-rose-400 font-semibold') : ''}>
                            Risk: {(cr.disruption_prob * 100).toFixed(1)}%
                          </span>
                          <span>{cr.hops} Hops</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Fat-Tailed Delay Distribution Plot */}
            <div
              className={`p-3 rounded-xl border space-y-1.5 transition-colors ${
                isLight
                  ? 'bg-slate-100/80 border-slate-200/80'
                  : 'bg-slate-900/70 border border-slate-800/80'
              }`}
            >
              <div className={`flex items-center justify-between border-b pb-1.5 ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
                <span className={`text-xs font-semibold font-sans ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                  Fat-Tailed Delay Distribution
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${isLight ? 'bg-sky-100 text-sky-800 border border-sky-300' : 'text-slate-400'}`}>
                  Jones &amp; Faddy Model
                </span>
              </div>
              <p className={`text-[11px] font-sans leading-tight ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                Exposes heavy-tailed delay risk unaccounted for by classical Gaussian models.
              </p>

              {/* High-Contrast SVG Curves */}
              <div className="w-full h-32 pt-1">
                <svg viewBox="0 0 320 110" className="w-full h-full select-none">
                  <defs>
                    <linearGradient id="skewFillGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={isLight ? '#0284c7' : '#38bdf8'} stopOpacity={isLight ? 0.22 : 0.28} />
                      <stop offset="100%" stopColor={isLight ? '#0284c7' : '#38bdf8'} stopOpacity={0.0} />
                    </linearGradient>
                  </defs>

                  {/* Coordinate Axes */}
                  <line x1="25" y1="92" x2="310" y2="92" stroke={isLight ? '#94a3b8' : '#334155'} strokeWidth="1" />
                  <line x1="25" y1="10" x2="25" y2="92" stroke={isLight ? '#94a3b8' : '#334155'} strokeWidth="1" />

                  {/* Grid Line */}
                  <line x1="25" y1="52" x2="310" y2="52" stroke={isLight ? '#e2e8f0' : '#1e293b'} strokeWidth="0.8" strokeDasharray="3 3" />

                  {/* Skew-t Distribution Curve with Heavy Right Tail */}
                  <path
                    d="M 25 92 C 45 90, 60 22, 90 22 C 120 22, 140 50, 180 66 C 220 78, 260 84, 305 87"
                    fill="url(#skewFillGrad)"
                  />
                  <path
                    d="M 25 92 C 45 90, 60 22, 90 22 C 120 22, 140 50, 180 66 C 220 78, 260 84, 305 87"
                    fill="none"
                    stroke={isLight ? '#0284c7' : '#38bdf8'}
                    strokeWidth="2.2"
                  />

                  {/* Dotted Curve for Naive Normal / Gaussian Baseline */}
                  <path
                    d="M 25 92 C 55 92, 85 18, 105 18 C 125 18, 155 92, 185 92 L 305 92"
                    fill="none"
                    stroke={isLight ? '#64748b' : '#94a3b8'}
                    strokeWidth="1.8"
                    strokeDasharray="4 3"
                  />

                  {/* Vertical Cutoff Line */}
                  <line x1="190" y1="10" x2="190" y2="92" stroke={isLight ? '#d97706' : '#fbbf24'} strokeWidth="1.8" strokeDasharray="2 2" />

                  {/* Cutoff Marker Annotation */}
                  <text x="194" y="24" fill={isLight ? '#b45309' : '#fbbf24'} fontSize="8.5" fontFamily="monospace" fontWeight="bold">
                    Cutoff &tau; (&alpha; = 0.80)
                  </text>

                  {/* Tail Risk Annotation */}
                  <text x="212" y="74" fill={isLight ? '#e11d48' : '#f43f5e'} fontSize="8" fontFamily="monospace" fontWeight="semibold">
                    Tail Risk &Delta;P
                  </text>

                  {/* Axis Ticks & Labels */}
                  <text x="22" y="103" fill={isLight ? '#475569' : '#64748b'} fontSize="8" fontFamily="monospace">0h</text>
                  <text x="90" y="103" fill={isLight ? '#475569' : '#64748b'} fontSize="8" fontFamily="monospace">1.2h (Mode)</text>
                  <text x="185" y="103" fill={isLight ? '#475569' : '#64748b'} fontSize="8" fontFamily="monospace">3.5h</text>
                  <text x="290" y="103" fill={isLight ? '#475569' : '#64748b'} fontSize="8" fontFamily="monospace">6.0h</text>
                </svg>
              </div>

              {/* Legend */}
              <div className={`flex flex-wrap items-center justify-between text-[10px] font-sans pt-1 border-t ${isLight ? 'border-slate-200 text-slate-600' : 'border-slate-800/60 text-slate-400'}`}>
                <span className="flex items-center gap-1.5">
                  <span className={`w-3 h-0.5 inline-block ${isLight ? 'bg-sky-600' : 'bg-sky-400'}`} />
                  <span>Skew-t (PACE / SPOTAR Correlated Delay)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className={`w-3 h-0.5 border-t border-dotted inline-block ${isLight ? 'border-slate-600' : 'border-slate-400'}`} />
                  <span>Normal (Naive Gaussian Baseline)</span>
                </span>
              </div>
            </div>

            {/* RSPP-A* Optimal Path Breakdown */}
            <div
              className={`p-3 rounded-xl border space-y-2 transition-colors ${
                isLight
                  ? 'bg-slate-100/80 border-slate-200/80'
                  : 'bg-slate-900/70 border border-slate-800/80'
              }`}
            >
              <div className={`flex items-center justify-between border-b pb-1.5 ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
                <span className={`text-xs font-semibold font-sans ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                  RSPP-A* Optimal Path Breakdown
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${isLight ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold' : 'text-emerald-400'}`}>
                  {routeLegs.length} Leg Segments
                </span>
              </div>

              {routeLegs.length > 0 ? (
                <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                  {routeLegs.map((leg, idx) => (
                    <div
                      key={idx}
                      className={`p-2 rounded-lg border text-xs font-mono flex items-center justify-between transition-colors ${
                        isLight
                          ? idx % 2 === 0
                            ? 'bg-white border-slate-200/90 text-slate-800'
                            : 'bg-slate-50 border-slate-200/70 text-slate-800'
                          : idx % 2 === 0
                          ? 'bg-slate-950/80 border-slate-800/80 text-slate-200'
                          : 'bg-slate-900/50 border-slate-800/60 text-slate-200'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${isLight ? 'bg-sky-100 text-sky-800 border border-sky-300' : 'bg-slate-800 text-sky-400'}`}>
                          Leg {String(idx + 1).padStart(2, '0')}
                        </span>
                        <span className={isLight ? 'text-slate-900 font-medium' : 'text-slate-200'}>
                          {leg.from} &rarr; {leg.to}
                        </span>
                      </div>
                      <div className={`text-[11px] ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        <span>{leg.distance_km} km</span>
                        <span className="mx-1">&middot;</span>
                        <span className={`font-semibold ${isLight ? 'text-sky-700' : 'text-sky-300'}`}>{leg.travel_time_hr}h</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`text-xs font-sans py-3 text-center ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                  Click &ldquo;Apply Hazard&rdquo; on the left to solve RSPP-A* stochastic routing.
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: BAYESIAN NETWORK BELIEF INSPECTOR                           */}
        {/* ================================================================= */}
        {activeTab === 'beliefs' && (
          <div className="space-y-3.5">
            {/* Live Posterior Probability Breakdown */}
            <div
              className={`p-3 rounded-xl border space-y-3 transition-colors ${
                isLight
                  ? 'bg-slate-100/80 border-slate-200/80'
                  : 'bg-slate-900/70 border border-slate-800/80'
              }`}
            >
              <div className={`border-b pb-2 ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
                <h3 className={`text-xs font-semibold font-sans ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>
                  Live Posterior Belief Breakdown: P(State | Evidence)
                </h3>
                <p className={`text-[11px] font-sans mt-0.5 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                  Computed via Exact Marginalization (Sum-Product Variable Elimination)
                </p>
              </div>

              {/* 3-Color Segmented Probability Bars for Top 5 Affected Hubs */}
              <div className="space-y-3 pt-1">
                {topVulnerableHubs.map((hub) => (
                  <div key={hub.nodeId} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className={`font-medium font-sans ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                        {hub.nodeId}
                      </span>
                      <span className={`font-mono text-[11px] ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        {(hub.pNominal * 100).toFixed(0)}% &middot; {(hub.pWarning * 100).toFixed(0)}% &middot; {(hub.pCritical * 100).toFixed(0)}%
                      </span>
                    </div>

                    {/* Smooth 3-color segmented bar */}
                    <div className={`w-full h-3 rounded-full overflow-hidden flex border ${isLight ? 'bg-slate-200 border-slate-300' : 'bg-slate-950 border-slate-800'}`}>
                      <div
                        className="bg-emerald-500 h-full transition-all duration-300 flex items-center justify-center text-[9px] font-mono text-emerald-950 font-bold"
                        style={{ width: `${Math.max(0, hub.pNominal * 100)}%` }}
                        title={`P(Nominal | E) = ${hub.pNominal}`}
                      >
                        {hub.pNominal > 0.15 ? `${(hub.pNominal * 100).toFixed(0)}%` : ''}
                      </div>
                      <div
                        className="bg-amber-500 h-full transition-all duration-300 flex items-center justify-center text-[9px] font-mono text-amber-950 font-bold"
                        style={{ width: `${Math.max(0, hub.pWarning * 100)}%` }}
                        title={`P(Warning | E) = ${hub.pWarning}`}
                      >
                        {hub.pWarning > 0.15 ? `${(hub.pWarning * 100).toFixed(0)}%` : ''}
                      </div>
                      <div
                        className="bg-rose-500 h-full transition-all duration-300 flex items-center justify-center text-[9px] font-mono text-rose-950 font-bold"
                        style={{ width: `${Math.max(0, hub.pCritical * 100)}%` }}
                        title={`P(Critical | E) = ${hub.pCritical}`}
                      >
                        {hub.pCritical > 0.15 ? `${(hub.pCritical * 100).toFixed(0)}%` : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* State Legend */}
              <div className={`flex items-center justify-between pt-2 border-t text-[10px] font-sans ${isLight ? 'border-slate-200 text-slate-600' : 'border-slate-800/60 text-slate-400'}`}>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                  <span>P(Nominal | E)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                  <span>P(Warning | E)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                  <span>P(Critical | E)</span>
                </span>
              </div>
            </div>

            {/* Model Telemetry & Theoretical Specs Card */}
            <div
              className={`p-3 rounded-xl border space-y-2 text-xs font-sans transition-colors ${
                isLight
                  ? 'bg-slate-100/80 border-slate-200/80'
                  : 'bg-slate-900/70 border border-slate-800/80'
              }`}
            >
              <div className={`font-semibold uppercase tracking-wider text-[11px] border-b pb-1 ${isLight ? 'text-slate-800 border-slate-200' : 'text-slate-200 border-slate-800'}`}>
                Model Telemetry &amp; Theoretical Specs
              </div>
              <div className="space-y-1.5 text-[11px]">
                <div className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-200' : 'border-slate-800/60'}`}>
                  <span className={isLight ? 'text-slate-600' : 'text-slate-400'}>Architecture:</span>
                  <span className={`font-mono ${isLight ? 'text-sky-700 font-semibold' : 'text-sky-300'}`}>2-Time-Slice Dynamic Bayesian Network (2-TBN)</span>
                </div>
                <div className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-200' : 'border-slate-800/60'}`}>
                  <span className={isLight ? 'text-slate-600' : 'text-slate-400'}>Inference:</span>
                  <span className={`font-mono ${isLight ? 'text-emerald-700 font-semibold' : 'text-emerald-400'}`}>Exact Variable Elimination across unrolled time slices</span>
                </div>
                <div className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-200' : 'border-slate-800/60'}`}>
                  <span className={isLight ? 'text-slate-600' : 'text-slate-400'}>Corridor Correlation:</span>
                  <span className={`font-mono ${isLight ? 'text-purple-700 font-semibold' : 'text-purple-300'}`}>SPOTAR / PACE Joint Corridor Distributions</span>
                </div>
                <div className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-200' : 'border-slate-800/60'}`}>
                  <span className={isLight ? 'text-slate-600' : 'text-slate-400'}>Delay Discretization:</span>
                  <span className={`font-mono ${isLight ? 'text-slate-800 font-medium' : 'text-slate-200'}`}>Jones &amp; Faddy Skew-t Density Quantiles</span>
                </div>
                <div className={`pt-1.5 text-[10px] leading-relaxed font-mono ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                  Markov Transition: P(X_t+1 | X_t, H_t+1) captures physical persistence and dissipation.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: RESILIENCE SCORECARD & RADIAL GAUGE                        */}
        {/* ================================================================= */}
        {activeTab === 'scorecard' && (
          <div className="space-y-3.5">
            {/* Radial Composite Resilience Gauge */}
            <div
              className={`p-4 rounded-xl border flex flex-col items-center justify-center space-y-2 transition-colors ${
                isLight
                  ? 'bg-slate-100/80 border-slate-200/80'
                  : 'bg-slate-900/70 border border-slate-800/80'
              }`}
            >
              <div className="relative w-36 h-36 flex items-center justify-center">
                <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                  {/* Background Track */}
                  <circle
                    cx="60"
                    cy="60"
                    r={gaugeRadius}
                    fill="none"
                    stroke={isLight ? '#e2e8f0' : '#1e293b'}
                    strokeWidth="10"
                  />
                  {/* Active Gauge Arc */}
                  <circle
                    cx="60"
                    cy="60"
                    r={gaugeRadius}
                    fill="none"
                    stroke={isLight ? '#0284c7' : '#38bdf8'}
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={gaugeCircumference}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-700 ease-out"
                  />
                </svg>

                {/* Central Value */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className={`text-2xl font-bold font-mono ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>
                    {(resilienceVal * 100).toFixed(1)}%
                  </span>
                  <span className={`text-[10px] uppercase tracking-widest font-mono mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    Composite
                  </span>
                </div>
              </div>

              <div className="text-center">
                <div className={`text-xs font-bold font-mono tracking-wider ${isLight ? 'text-sky-800' : 'text-sky-400'}`}>
                  {resilienceStatusTag}
                </div>
                <div className={`text-[10px] font-sans mt-0.5 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                  Jiang et al. (2020) Unified DBN Resilience Framework
                </div>
              </div>
            </div>

            {/* The 5 Core Capabilities */}
            {scorecard ? (
              <div
                className={`p-3 rounded-xl border space-y-3 text-xs font-sans transition-colors ${
                  isLight
                    ? 'bg-slate-100/80 border-slate-200/80'
                    : 'bg-slate-900/70 border border-slate-800/80'
                }`}
              >
                <div className={`font-semibold uppercase tracking-wider text-[11px] border-b pb-1 ${isLight ? 'text-slate-800 border-slate-200' : 'text-slate-200 border-slate-800'}`}>
                  5 Core DBN Resilience Metrics
                </div>

                {[
                  {
                    name: '1. Rapid Response',
                    sub: 'Shock absorption gradient (t0 -> t1)',
                    val: scorecard.rapid_response,
                    color: isLight ? 'bg-emerald-600' : 'bg-emerald-400',
                  },
                  {
                    name: '2. Sustained Resistance',
                    sub: 'Delay avoidance (1 - max P_Critical)',
                    val: scorecard.sustained_resistance,
                    color: isLight ? 'bg-sky-600' : 'bg-sky-400',
                  },
                  {
                    name: '3. Continuous Running',
                    sub: 'Pareto route stability across time horizon',
                    val: scorecard.continuous_running,
                    color: isLight ? 'bg-purple-600' : 'bg-purple-400',
                  },
                  {
                    name: '4. Rapid Convergence',
                    sub: 'Post-shock Markovian recovery rate (t_peak -> t_H)',
                    val: scorecard.rapid_convergence,
                    color: isLight ? 'bg-amber-600' : 'bg-amber-400',
                  },
                  {
                    name: '5. Dynamic Evolution',
                    sub: 'Terminal network reliability trajectory',
                    val: scorecard.dynamic_evolution,
                    color: isLight ? 'bg-cyan-600' : 'bg-cyan-400',
                  },
                ].map((cap) => (
                  <div key={cap.name} className="space-y-1">
                    <div className="flex justify-between items-baseline text-[11px]">
                      <div>
                        <span className={`font-medium font-sans ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{cap.name}:</span>
                        <span className={`text-[10px] ml-1.5 font-sans ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>{cap.sub}</span>
                      </div>
                      <span className={`font-bold font-mono ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>{(cap.val * 100).toFixed(1)}%</span>
                    </div>
                    <div className={`w-full h-1.5 rounded-full overflow-hidden border ${isLight ? 'bg-slate-200 border-slate-300' : 'bg-slate-950 border-slate-850'}`}>
                      <div
                        className={`h-full ${cap.color} rounded-full transition-all duration-500`}
                        style={{ width: `${Math.min(100, Math.max(0, cap.val * 100))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={`text-xs font-sans py-4 text-center rounded-xl border ${isLight ? 'bg-slate-100/80 border-slate-200 text-slate-600' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>
                Execute simulation to compute Jiang et al. resilience metrics.
              </div>
            )}

            {/* Bottleneck Diagnostics */}
            {timelineResult?.vulnerable_hub && (
              <div
                className={`p-3 rounded-xl border space-y-2 text-xs font-sans transition-colors ${
                  isLight
                    ? 'bg-rose-100/70 border-rose-300/80'
                    : 'bg-rose-950/20 border border-rose-900/40'
                }`}
              >
                <div className={`font-semibold uppercase tracking-wider text-[11px] ${isLight ? 'text-rose-900' : 'text-rose-400'}`}>
                  Bottleneck Diagnostics
                </div>
                <div className="space-y-1.5 text-[11px]">
                  <div className={`flex justify-between items-center p-2 rounded-lg border ${isLight ? 'bg-white/90 border-rose-200 text-slate-800' : 'bg-rose-950/40 border-rose-900/50 text-slate-300'}`}>
                    <span>Vulnerable Hub:</span>
                    <span className={`font-bold font-mono ${isLight ? 'text-rose-700' : 'text-rose-300'}`}>{timelineResult.vulnerable_hub}</span>
                  </div>
                  {timelineResult.high_risk_edge && (
                    <div className={`flex justify-between items-center p-2 rounded-lg border ${isLight ? 'bg-white/90 border-amber-200 text-slate-800' : 'bg-amber-950/40 border-amber-900/50 text-slate-300'}`}>
                      <span>Critical Corridor Link:</span>
                      <span className={`font-bold font-mono ${isLight ? 'text-amber-700' : 'text-amber-300'}`}>{timelineResult.high_risk_edge}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResilienceRoutePanel;
