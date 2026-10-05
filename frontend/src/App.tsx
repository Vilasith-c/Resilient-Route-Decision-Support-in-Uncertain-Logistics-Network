import React, { useState, useEffect, useRef } from 'react';
import type { NetworkResponse, HazardInput, EngineTimelineResult, CandidateRoute } from './types/network';
import { fetchNetwork, simulateHazard, fetchHealth } from './services/api';
import { Header } from './components/Header';
import { NetworkMap } from './components/NetworkMap';
import { HazardControlPanel } from './components/HazardControlPanel';
import { ResilienceRoutePanel } from './components/ResilienceRoutePanel';

export const App: React.FC = () => {
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Active Hazard State
  const [hazard, setHazard] = useState<HazardInput>({
    hazard_type: 'cyclone',
    epicenter_lat: 11.9401, // Near Cuddalore / East Coast by default
    epicenter_lon: 79.7719,
    radius_km: 45,
    severity: 0.75,
  });

  // Timeline Simulation State
  const [timelineResult, setTimelineResult] = useState<EngineTimelineResult | null>(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedRoute, setSelectedRoute] = useState<CandidateRoute | null>(null);

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
      epicenter_lat: lat,
      epicenter_lon: lon,
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
      if (result.frames[0]?.recommended_route) {
        setSelectedRoute(result.frames[0].recommended_route);
      }
    } catch (err) {
      console.error('Simulation error:', err);
      alert('Simulation error. Please verify the FastAPI backend is running on port 8000.');
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
    selectedRoute?.path || currentFrame?.recommended_route?.path || [];

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      {/* 1. System Header */}
      <Header network={network} backendStatus={backendStatus} />

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
            nodeExposures={currentFrame?.node_exposures}
          />

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

        {/* Right Side: Control Panels */}
        <div className="w-[420px] flex flex-col gap-3 shrink-0 h-full overflow-hidden">
          {/* Spatial Hazard Placement & Timeline Controller */}
          <HazardControlPanel
            hazard={hazard}
            onChangeHazard={setHazard}
            onApplyHazard={handleApplyHazard}
            onClearHazard={handleClearHazard}
            isLoading={isLoading}
            timelineResult={timelineResult}
            currentFrameIndex={currentFrameIndex}
            onChangeFrame={setCurrentFrameIndex}
            isPlaying={isPlaying}
            onTogglePlay={() => setIsPlaying(!isPlaying)}
          />

          {/* RSPP-A* Route Recommendation & Resilience Scorecard */}
          <ResilienceRoutePanel
            currentFrame={currentFrame}
            onSelectRoute={setSelectedRoute}
            selectedRouteNodes={highlightedRouteNodes}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
