import React from 'react';
import type { TimelineFrame, CandidateRoute, EngineTimelineResult } from '../types/network';
import { ShieldCheck, Navigation, AlertOctagon, Activity } from 'lucide-react';

interface ResilienceRoutePanelProps {
  timelineResult: EngineTimelineResult | null;
  currentFrame: TimelineFrame | null;
  selectedRoute?: CandidateRoute | null;
  onSelectRoute?: (route: CandidateRoute) => void;
  selectedRouteNodes?: string[];
}

export const ResilienceRoutePanel: React.FC<ResilienceRoutePanelProps> = ({
  timelineResult,
  currentFrame,
  selectedRoute,
  onSelectRoute,
  selectedRouteNodes = [],
}) => {
  const scorecard = timelineResult?.resilience_scorecard;
  const candidateRoutes = timelineResult?.primary_rerouted_solutions || [];
  const activeRoute = selectedRoute || candidateRoutes[0] || null;

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 backdrop-blur-md p-4 rounded-xl border border-slate-800 text-slate-200 overflow-y-auto h-full shadow-2xl">
      {/* 1. Recommended Route Overview */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-sky-400" />
            <h2 className="font-semibold text-slate-100 text-sm tracking-wide uppercase">
              RSPP-A* Resilient Route
            </h2>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-950 text-sky-400 font-semibold border border-sky-800/60">
            FSD Pareto-Optimal
          </span>
        </div>

        {activeRoute ? (
          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Total Travel Time:</span>
              <span className="font-mono text-sm font-bold text-sky-300">
                {activeRoute.travel_time_hr.toFixed(2)} hrs
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">On-Time Reliability (&alpha;):</span>
              <span className="font-mono text-xs font-semibold text-emerald-400">
                {(activeRoute.on_time_reliability_alpha * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Disruption Risk:</span>
              <span className="font-mono text-xs font-semibold text-rose-400">
                {(activeRoute.disruption_prob * 100).toFixed(1)}%
              </span>
            </div>

            {/* Path Breadcrumbs */}
            <div className="mt-1 pt-2 border-t border-slate-800 text-xs">
              <div className="text-[11px] text-slate-400 mb-1">
                Route Path ({activeRoute.hops} hops):
              </div>
              <div className="font-mono text-[11px] text-slate-300 bg-slate-900/80 p-2 rounded border border-slate-800/60 break-words leading-relaxed">
                {activeRoute.path_nodes.map((node, i) => (
                  <span key={node}>
                    <span className="text-sky-300 font-medium">{node}</span>
                    {i < activeRoute.path_nodes.length - 1 && (
                      <span className="text-slate-600 mx-1">&rarr;</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : timelineResult ? (
          <div className="text-xs text-amber-400/90 italic p-3 text-center bg-amber-950/20 rounded-lg border border-amber-900/40">
            Severe corridor chokepoints: no viable route met the &alpha;-reliability threshold under this shock scenario.
          </div>
        ) : (
          <div className="text-xs text-slate-500 italic p-3 text-center bg-slate-950/40 rounded-lg border border-slate-800/40">
            No route calculated. Click "Run Simulation" to solve RSPP-A*.
          </div>
        )}
      </div>

      {/* 2. Jiang et al. (2020) 5 DBN Resilience Capabilities */}
      <div className="flex flex-col gap-2 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-2 pb-1">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold text-slate-100 text-sm tracking-wide uppercase">
            Resilience Scorecard
          </h2>
        </div>

        {scorecard ? (
          <div className="flex flex-col gap-2.5 text-xs">
            {/* Overall Composite Score */}
            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60 flex items-center justify-between">
              <span className="text-slate-300 font-medium">Composite Resilience Index:</span>
              <span className="font-mono text-base font-bold text-emerald-400">
                {(scorecard.overall_resilience_index * 100).toFixed(1)}%
              </span>
            </div>

            {/* 5 Core Jiang et al. Capabilities */}
            {[
              { label: 'Rapid Response (Shock Absorption)', val: scorecard.rapid_response, color: 'bg-emerald-500' },
              { label: 'Sustained Resistance (Delay Avoidance)', val: scorecard.sustained_resistance, color: 'bg-blue-500' },
              { label: 'Continuous Running (Pareto Stability)', val: scorecard.continuous_running, color: 'bg-purple-500' },
              { label: 'Rapid Convergence (Post-Shock Recovery)', val: scorecard.rapid_convergence, color: 'bg-amber-500' },
              { label: 'Dynamic Evolution (Terminal Reliability)', val: scorecard.dynamic_evolution, color: 'bg-cyan-500' },
            ].map((metric) => (
              <div key={metric.label} className="flex flex-col gap-1">
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>{metric.label}</span>
                  <span className="font-mono text-slate-200">{(metric.val * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${metric.color} transition-all duration-300 rounded-full`}
                    style={{ width: `${Math.min(100, Math.max(0, metric.val * 100))}%` }}
                  />
                </div>
              </div>
            ))}

            {/* Vulnerable Hub & High-Risk Edge Diagnostic */}
            {timelineResult.vulnerable_hub && (
              <div className="mt-2 pt-2 border-t border-slate-800 flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5 text-rose-400 text-[11px] font-semibold uppercase">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  <span>Bottleneck Diagnostics:</span>
                </div>
                <div className="flex flex-col gap-1 text-[11px]">
                  <div className="flex justify-between bg-slate-950/60 p-1.5 rounded border border-slate-800">
                    <span className="text-slate-400">Vulnerable Hub:</span>
                    <span className="font-mono text-rose-300 font-semibold">{timelineResult.vulnerable_hub}</span>
                  </div>
                  {timelineResult.high_risk_edge && (
                    <div className="flex justify-between bg-slate-950/60 p-1.5 rounded border border-slate-800">
                      <span className="text-slate-400">Critical Link:</span>
                      <span className="font-mono text-amber-300 font-semibold">{timelineResult.high_risk_edge}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-slate-500 italic p-3 text-center bg-slate-950/40 rounded-lg border border-slate-800/40">
            Awaiting simulation data...
          </div>
        )}
      </div>

      {/* 3. Candidate Pareto Routes List */}
      {candidateRoutes.length > 1 && (
        <div className="flex flex-col gap-2 pt-2 border-t border-slate-800 text-xs">
          <div className="font-semibold text-slate-300 text-[11px] uppercase tracking-wide">
            Alternative Candidate Routes ({candidateRoutes.length})
          </div>
          <div className="flex flex-col gap-1.5">
            {candidateRoutes.map((cr, idx) => {
              const isSelected = activeRoute?.route === cr.route || selectedRouteNodes.join(',') === cr.path_nodes.join(',');
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectRoute && onSelectRoute(cr)}
                  className={`text-left p-2 rounded-lg border transition ${
                    isSelected
                      ? 'bg-sky-950/60 border-sky-500/80 text-sky-200'
                      : 'bg-slate-950/40 border-slate-800/80 text-slate-400 hover:bg-slate-850 hover:text-slate-200'
                  }`}
                >
                  <div className="flex justify-between font-mono text-[11px] font-medium">
                    <span>Route #{idx + 1} ({cr.hops} hops)</span>
                    <span className="text-sky-300">{cr.travel_time_hr.toFixed(1)}h</span>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                    <span>Rel: {(cr.on_time_reliability_alpha * 100).toFixed(0)}%</span>
                    <span>Risk: {(cr.disruption_prob * 100).toFixed(0)}%</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Cascade Effects in current hour */}
      {currentFrame?.cascade_effects && currentFrame.cascade_effects.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-800 text-xs">
          <div className="flex items-center gap-1 text-amber-400 font-semibold text-[11px] uppercase">
            <Activity className="w-3.5 h-3.5" />
            <span>Active Cascade Effects (Hour {currentFrame.time_hour}):</span>
          </div>
          <div className="flex flex-col gap-1">
            {currentFrame.cascade_effects.slice(0, 3).map((eff, i) => (
              <div key={i} className="text-[11px] bg-slate-950/60 p-1.5 rounded border border-slate-800/70">
                <span className="font-semibold text-slate-200">{eff.node}:</span>{' '}
                <span className="text-slate-400">{eff.impact}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
