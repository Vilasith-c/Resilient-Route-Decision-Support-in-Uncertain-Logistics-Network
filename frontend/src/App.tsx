import React, { useState, useEffect, useRef } from 'react';
import type { NetworkResponse, HazardInput, EngineTimelineResult, CandidateRoute } from './types/network';
import { fetchNetwork, simulateHazard, fetchHealth } from './services/api';
import { NetworkMap } from './components/NetworkMap';
import { HazardDropdown } from './components/HazardDropdown';
import { MeasurementsDropdown } from './components/MeasurementsDropdown';
import { ResilienceRoutePanel } from './components/ResilienceRoutePanel';
import { VentuskyTimeline } from './components/VentuskyTimeline';

export const App: React.FC = () => {
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Active Hazard State conforming to FastAPI HazardInput
  const [hazard, setHazard] = useState<HazardInput>({
    hazard_type: 'flood',
    latitude: 11.9401, // Near Cuddalore / East Coast by default
    longitude: 79.7719,
    radius_km: 45,
    intensity: 0.75,
    time_horizon: 10,
  });

  // Timeline Simulation State
  const [timelineResult, setTimelineResult] = useState<EngineTimelineResult | null>(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedRoute, setSelectedRoute] = useState<CandidateRoute | null>(null);
  const [openDropdown, setOpenDropdown] = useState<'hazard' | 'measurements' | null>(null);

  const playbackTimerRef = useRef<number | null>(null);

  // 1. Initial Load: Fetch network topology and check backend health
  useEffect(() => {
    async function init() {
      try {
        setBackendStatus('connecting');
        await fetchHealth();
        const net = await fetchNetwork();
        setNetwork(net);
        setBackendStatus('connected');
      } catch (err) {
        console.error('Failed to connect to FastAPI backend:', err);
        setBackendStatus('disconnected');
      }
    }
    init();
  }, []);

  // 2. Playback timer for timeline scrubbing
  useEffect(() => {
    if (isPlaying && timelineResult && timelineResult.frames.length > 0) {
      playbackTimerRef.current = window.setInterval(() => {
        setCurrentFrameIndex((prev) => {
          if (prev >= timelineResult.frames.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
        playbackTimerRef.current = null;
      }
    }
    return () => {
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    };
  }, [isPlaying, timelineResult]);

  // Map Click Handler: Relocates hazard epicenter
  const handleMapClick = (lat: number, lon: number) => {
    setHazard((prev) => ({
      ...prev,
      latitude: Number(lat.toFixed(4)),
      longitude: Number(lon.toFixed(4)),
    }));
  };

  // Run Simulation Handler
  const handleApplyHazard = async () => {
    try {
      setIsLoading(true);
      const result = await simulateHazard(hazard);
      setTimelineResult(result);
      setCurrentFrameIndex(0);
      setIsPlaying(true);
      const solutions = result.primary_rerouted_solutions || [];
      setSelectedRoute(solutions.length > 0 ? solutions[0] : null);
    } catch (err: any) {
      console.error('Simulation error:', err);
      alert(`Simulation error: ${err.message || 'Check console'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear Hazard
  const handleClearHazard = () => {
    setTimelineResult(null);
    setCurrentFrameIndex(0);
    setIsPlaying(false);
    setSelectedRoute(null);
  };

  // Active frame data
  const currentFrame = timelineResult?.frames[currentFrameIndex] || null;

  // Active highlighted route path nodes
  const highlightedRouteNodes =
    selectedRoute?.path_nodes ||
    (timelineResult?.primary_rerouted_solutions?.[0]?.path_nodes ?? []);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans">


      {/* 2. Main Dashboard Layout */}
      <main className="flex-1 relative flex overflow-hidden p-3 gap-3">
        {/* Left Side: Interactive Map */}
        <div className="flex-1 h-full relative">
          <NetworkMap
            network={network}
            selectedNode={selectedNode}
            onSelectNode={setSelectedNode}
            activeHazard={hazard}
            onMapClick={handleMapClick}
            highlightedRouteNodes={highlightedRouteNodes}
            nodeStates={currentFrame?.node_states}
          />

          {/* Ventusky-Style Floating Controls on the Left Side */}
          <div className="absolute top-4 left-4 z-[1000] flex flex-col items-start gap-2.5 pointer-events-auto">
            <HazardDropdown
              hazard={hazard}
              onChangeHazard={setHazard}
              onApplyHazard={handleApplyHazard}
              isLoading={isLoading}
              isOpen={openDropdown === 'hazard'}
              onToggle={() => setOpenDropdown((prev) => (prev === 'hazard' ? null : 'hazard'))}
              onClose={() => setOpenDropdown(null)}
            />

            <MeasurementsDropdown
              hazard={hazard}
              onChangeHazard={setHazard}
              onApplyHazard={handleApplyHazard}
              isLoading={isLoading}
              isOpen={openDropdown === 'measurements'}
              onToggle={() => setOpenDropdown((prev) => (prev === 'measurements' ? null : 'measurements'))}
              onClose={() => setOpenDropdown(null)}
            />
          </div>

          {/* Ventusky-Style Bottom Timeline Bar */}
          <div className="absolute bottom-0 left-0 right-0 z-[1000] pointer-events-auto">
            <VentuskyTimeline
              timelineResult={timelineResult}
              currentFrameIndex={currentFrameIndex}
              onSelectFrame={setCurrentFrameIndex}
              isPlaying={isPlaying}
              onTogglePlay={() => setIsPlaying(!isPlaying)}
              onApplyHazard={handleApplyHazard}
              onClearHazard={handleClearHazard}
              isLoading={isLoading}
              timeHorizon={hazard.time_horizon}
            />
          </div>

          {backendStatus === 'disconnected' && (
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-[1100] flex items-center justify-center p-6">
              <div className="bg-slate-900 border border-rose-500/40 p-6 rounded-2xl max-w-md text-center shadow-2xl">
                <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 mx-auto flex items-center justify-center mb-3 text-2xl font-bold">
                  !
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">Backend Not Connected</h3>
                <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                  The frontend is looking for the FastAPI backend service at{' '}
                  <code className="bg-slate-950 px-2 py-0.5 rounded text-sky-400">http://127.0.0.1:8000</code>.
                  Start the server using:
                </p>
                <div className="bg-slate-950 p-2.5 rounded text-left font-mono text-xs text-slate-300 border border-slate-800">
                  cd phase2_tamil_nadu_engine<br />
                  uvicorn main:app --reload --port 8000
                </div>
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="mt-4 w-full bg-sky-600 hover:bg-sky-500 text-white font-medium py-2 rounded-lg text-xs transition"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Side: RSPP-A* Route Recommendation & Resilience Scorecard */}
        <div className="w-[420px] flex flex-col shrink-0 h-full overflow-hidden">
          <ResilienceRoutePanel
            timelineResult={timelineResult}
            currentFrame={currentFrame}
            selectedRoute={selectedRoute}
            onSelectRoute={setSelectedRoute}
            selectedRouteNodes={highlightedRouteNodes}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
