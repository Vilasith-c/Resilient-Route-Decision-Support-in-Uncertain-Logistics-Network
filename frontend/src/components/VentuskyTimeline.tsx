import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  ChevronsLeft,
  ChevronsRight,
  Play,
  Pause,
  Loader2,
  RotateCcw,
} from 'lucide-react';
import type { EngineTimelineResult } from '../types/network';

interface VentuskyTimelineProps {
  timelineResult: EngineTimelineResult | null;
  currentFrameIndex: number;
  onSelectFrame: (index: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onApplyHazard?: () => void;
  onClearHazard?: () => void;
  isLoading?: boolean;
  timeHorizon?: number;
}

interface TimeTick {
  index: number;
  timeHour: number;
  timeFormatted: string;
  ampm: string;
  label: string;
}

export const VentuskyTimeline: React.FC<VentuskyTimelineProps> = ({
  timelineResult,
  currentFrameIndex,
  onSelectFrame,
  isPlaying,
  onTogglePlay,
  onApplyHazard,
  onClearHazard,
  isLoading = false,
  timeHorizon = 10,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);

  const framesCount = timelineResult?.frames.length ?? (timeHorizon + 1);
  const totalSteps = Math.max(1, framesCount - 1);

  // Generate hourly ticks based on start time (08:30 AM like the reference UI)
  const ticks: TimeTick[] = React.useMemo(() => {
    const list: TimeTick[] = [];
    const baseHour = 8;
    const baseMinute = 30;

    for (let i = 0; i < framesCount; i++) {
      const totalMinutes = (baseHour + i) * 60 + baseMinute;
      let hour24 = Math.floor(totalMinutes / 60) % 24;
      const ampm = hour24 >= 12 ? 'PM' : 'AM';
      let hour12 = hour24 % 12;
      if (hour12 === 0) hour12 = 12;
      const timeFormatted = `${hour12}:${baseMinute.toString().padStart(2, '0')}`;

      list.push({
        index: i,
        timeHour: i,
        timeFormatted,
        ampm,
        label: i === 0 ? 'Onset t=0' : i === framesCount - 1 ? 'Terminal' : `+${i}h`,
      });
    }
    return list;
  }, [framesCount]);

  // Handle click or scrub along track
  const handleScrub = useCallback(
    (clientX: number) => {
      if (!trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();
      const relativeX = clientX - rect.left;
      const ratio = Math.max(0, Math.min(1, relativeX / rect.width));
      const targetIndex = Math.round(ratio * totalSteps);
      onSelectFrame(targetIndex);
    },
    [totalSteps, onSelectFrame]
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    handleScrub(e.clientX);
  };

  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      if (isDragging) {
        handleScrub(e.clientX);
      }
    }
    function handleMouseUp() {
      if (isDragging) {
        setIsDragging(false);
      }
    }

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleScrub]);

  const handlePrev = () => {
    if (currentFrameIndex > 0) {
      onSelectFrame(currentFrameIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentFrameIndex < totalSteps) {
      onSelectFrame(currentFrameIndex + 1);
    }
  };

  const handlePlayClick = () => {
    if (!timelineResult && onApplyHazard) {
      onApplyHazard();
    } else {
      onTogglePlay();
    }
  };

  const progressPercent = totalSteps > 0 ? (currentFrameIndex / totalSteps) * 100 : 0;

  return (
    /* Completely Transparent Container - No dark mask over map */
    <div className="w-full bg-transparent pb-3 pt-2 px-6 select-none pointer-events-auto">
      <div className="max-w-7xl mx-auto flex items-end gap-4 md:gap-6">
        {/* 1. Left Action Buttons (Previous & Play) */}
        <div className="flex items-start gap-2.5 shrink-0 pb-1">
          {/* Previous Button */}
          <div className="flex flex-col items-center">
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentFrameIndex === 0}
              className="w-10 h-10 rounded-full bg-slate-900/85 hover:bg-slate-800 active:scale-95 disabled:opacity-30 disabled:pointer-events-none text-white flex items-center justify-center border border-white/20 shadow-xl backdrop-blur-md transition-all cursor-pointer"
              title="Previous Hour"
            >
              <ChevronsLeft className="w-5 h-5 text-white" strokeWidth={2.2} />
            </button>
            <span className="text-[10px] text-white font-medium tracking-tight mt-1 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
              Previous
            </span>
          </div>

          {/* Play / Pause Button */}
          <div className="flex flex-col items-center">
            <button
              type="button"
              onClick={handlePlayClick}
              disabled={isLoading}
              className="w-10 h-10 rounded-full bg-slate-900/85 hover:bg-slate-800 active:scale-95 text-white flex items-center justify-center border border-white/20 shadow-xl backdrop-blur-md transition-all cursor-pointer group"
              title={isPlaying ? 'Pause Simulation' : 'Play Timeline'}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
              ) : isPlaying ? (
                <Pause className="w-4 h-4 text-white fill-current" />
              ) : (
                <Play className="w-4 h-4 text-white fill-current ml-0.5 group-hover:scale-105 transition-transform" />
              )}
            </button>
            <span className="text-[10px] text-white font-medium tracking-tight mt-1 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
              {isPlaying ? 'Pause' : 'Play'}
            </span>
          </div>
        </div>

        {/* 2. Transparent Scrubber Track with Ticks & Playhead */}
        <div className="flex-1 flex flex-col justify-end min-w-0 pb-1">
          {/* Track Bar with Thumb */}
          <div
            ref={trackRef}
            onMouseDown={handleMouseDown}
            className="relative h-6 flex items-center cursor-pointer group"
            title="Click or drag to scrub simulation timeline"
          >
            {/* The Horizontal Line Track (Floating cleanly over map) */}
            <div className="w-full h-[3.5px] bg-white/40 shadow-[0_1px_3px_rgba(0,0,0,0.9)] rounded-full group-hover:h-[4.5px] transition-all relative overflow-visible">
              {/* Highlighted active portion */}
              <div
                className="h-full bg-white/90 shadow-[0_0_6px_rgba(255,255,255,0.7)] rounded-full"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* Circular Playhead Knob */}
            <div
              className="absolute -translate-x-1/2 w-4 h-4 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,1),0_2px_5px_rgba(0,0,0,0.9)] border-2 border-slate-900 group-hover:scale-125 transition-transform duration-100 cursor-grab active:cursor-grabbing z-20"
              style={{ left: `${progressPercent}%` }}
            />
          </div>

          {/* Time Labels with Ticks */}
          <div className="relative w-full flex justify-between items-start mt-0.5 pt-0.5">
            {ticks.map((tick) => {
              const isActive = tick.index === currentFrameIndex;

              return (
                <div
                  key={tick.index}
                  onClick={() => onSelectFrame(tick.index)}
                  className="flex flex-col items-center cursor-pointer group/tick flex-1"
                >
                  {/* Subtle vertical tick line */}
                  <div
                    className={`w-[1.5px] h-2 transition-colors mb-1 shadow-[0_1px_2px_rgba(0,0,0,0.8)] ${
                      isActive
                        ? 'bg-white'
                        : 'bg-white/60 group-hover/tick:bg-white'
                    }`}
                  />

                  {/* Hour text: e.g. 8:30 with AM/PM underneath */}
                  <div className="flex flex-col items-center text-center">
                    <span
                      className={`text-[12px] leading-tight tracking-tight drop-shadow-[0_1.5px_3px_rgba(0,0,0,0.95)] transition-colors ${
                        isActive
                          ? 'font-extrabold text-white scale-105'
                          : 'font-semibold text-white/80 group-hover/tick:text-white'
                      }`}
                    >
                      {tick.timeFormatted}
                    </span>
                    <span
                      className={`text-[8.5px] font-bold uppercase tracking-wider drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] ${
                        isActive
                          ? 'text-white'
                          : 'text-white/70 group-hover/tick:text-white'
                      }`}
                    >
                      {tick.ampm}
                    </span>

                    {/* Active highlight bar below current time (Ventusky style) */}
                    <div
                      className={`h-[2px] w-6 mt-0.5 rounded-full transition-all ${
                        isActive ? 'bg-white shadow-[0_0_8px_#fff]' : 'bg-transparent'
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. Right Next Button & Optional Reset */}
        <div className="flex items-start gap-2 shrink-0 pb-1">
          {onClearHazard && timelineResult && (
            <div className="flex flex-col items-center">
              <button
                type="button"
                onClick={onClearHazard}
                className="w-10 h-10 rounded-full bg-slate-900/85 hover:bg-rose-950/80 active:scale-95 text-slate-300 hover:text-rose-300 flex items-center justify-center border border-white/20 shadow-xl backdrop-blur-md transition-all cursor-pointer"
                title="Reset simulation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <span className="text-[10px] text-white font-medium tracking-tight mt-1 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
                Reset
              </span>
            </div>
          )}

          <div className="flex flex-col items-center">
            <button
              type="button"
              onClick={handleNext}
              disabled={currentFrameIndex >= totalSteps}
              className="w-10 h-10 rounded-full bg-slate-900/85 hover:bg-slate-800 active:scale-95 disabled:opacity-30 disabled:pointer-events-none text-white flex items-center justify-center border border-white/20 shadow-xl backdrop-blur-md transition-all cursor-pointer"
              title="Next Hour"
            >
              <ChevronsRight className="w-5 h-5 text-white" strokeWidth={2.2} />
            </button>
            <span className="text-[10px] text-white font-medium tracking-tight mt-1 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
              Next
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
