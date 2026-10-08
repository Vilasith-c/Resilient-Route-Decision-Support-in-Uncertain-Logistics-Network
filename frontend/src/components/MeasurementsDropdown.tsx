import React, { useState, useRef, useEffect } from 'react';
import { SlidersHorizontal, ChevronDown, Play, Loader2, RotateCcw } from 'lucide-react';
import type { HazardInput } from '../types/network';

interface MeasurementsDropdownProps {
  hazard: HazardInput;
  onChangeHazard: (h: HazardInput) => void;
  onApplyHazard?: () => void;
  isLoading?: boolean;
  isOpen?: boolean;
  onToggle?: () => void;
  onClose?: () => void;
}

export const MeasurementsDropdown: React.FC<MeasurementsDropdownProps> = ({
  hazard,
  onChangeHazard,
  onApplyHazard,
  isLoading = false,
  isOpen: controlledIsOpen,
  onToggle,
  onClose,
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const toggleDropdown = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalIsOpen((prev) => !prev);
    }
  };
  const closeDropdown = () => {
    if (onClose) {
      onClose();
    } else {
      setInternalIsOpen(false);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        closeDropdown();
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleRadiusChange = (radius: number) => {
    onChangeHazard({
      ...hazard,
      radius_km: radius,
    });
  };

  const handleIntensityChange = (intensity: number) => {
    onChangeHazard({
      ...hazard,
      intensity: Number(intensity.toFixed(2)),
    });
  };

  const intensityPercent = Math.round(hazard.intensity * 100);

  // Percentage for CSS custom gradient tracks (min 10km to max 150km for radius)
  const radiusPercent = Math.min(100, Math.max(0, ((hazard.radius_km - 10) / (150 - 10)) * 100));

  return (
    <div className="relative inline-block select-none" ref={dropdownRef}>
      {/* 
        Ventusky-styled Capsule Button for Measurements
        Matches format: White circular icon badge + dark rounded capsule with text "Measurements"
      */}
      <button
        type="button"
        onClick={toggleDropdown}
        className="flex items-center h-10 pl-1 pr-3.5 rounded-full bg-[#1e232a]/95 hover:bg-[#252b34] active:scale-[0.98] border border-slate-700/60 shadow-xl transition-all duration-200 cursor-pointer group backdrop-blur-md"
        title="Adjust Hazard Measurements (Radius & Intensity)"
      >
        {/* Left White Circular Icon Badge */}
        <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-md shrink-0">
          <SlidersHorizontal className="w-4.5 h-4.5 text-blue-600" strokeWidth={2.2} />
        </div>

        {/* Label: Measurements + dynamic values badge */}
        <div className="flex items-center gap-2 ml-2.5">
          <span className="font-bold text-white text-[13px] tracking-tight">
            Measurements
          </span>

          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-950/80 text-sky-400 border border-sky-800/60 font-semibold tracking-wider">
            {hazard.radius_km} km &bull; {intensityPercent}%
          </span>
        </div>

        {/* Dropdown Chevron */}
        <ChevronDown
          className={`w-3.5 h-3.5 ml-2 text-slate-400 group-hover:text-white transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-white' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu Overlay */}
      {isOpen && (
        <div className="absolute top-12 left-0 z-[1100] w-84 bg-[#181d24]/98 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl p-3.5 text-slate-200 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="pb-2.5 mb-3 border-b border-slate-800/80 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Hazard Measurements
              </span>
              <p className="text-[10px] text-slate-500">
                Calibrate spatial perimeter & disruption impact
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                handleRadiusChange(45);
                handleIntensityChange(0.75);
              }}
              title="Reset measurements to standard defaults"
              className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 px-1.5 py-0.5 rounded hover:bg-slate-800 transition cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>

          <div className="flex flex-col gap-4">
            {/* 1. Radius Slider */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">Radius:</span>
                <span className="font-mono font-bold text-slate-100 text-sm">
                  {hazard.radius_km} <span className="text-xs font-normal text-slate-400">km</span>
                </span>
              </div>

              {/* Slider Track conforming to reference image style */}
              <div className="relative flex items-center my-1">
                <input
                  type="range"
                  min="10"
                  max="150"
                  step="5"
                  value={hazard.radius_km}
                  onChange={(e) => handleRadiusChange(Number(e.target.value))}
                  style={{
                    background: `linear-gradient(to right, #f43f5e 0%, #f43f5e ${radiusPercent}%, #e2e8f0 ${radiusPercent}%, #e2e8f0 100%)`,
                  }}
                  className="w-full h-2 rounded-full appearance-none cursor-pointer accent-rose-500 focus:outline-none shadow-inner"
                />
              </div>

              {/* Quick Preset Buttons for Radius */}
              <div className="flex items-center gap-1.5 pt-0.5">
                {[25, 45, 75, 100].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => handleRadiusChange(val)}
                    className={`flex-1 py-1 rounded-md text-[10px] font-mono transition cursor-pointer ${
                      hazard.radius_km === val
                        ? 'bg-rose-500/25 border border-rose-500/60 text-rose-300 font-bold'
                        : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/50'
                    }`}
                  >
                    {val}km
                  </button>
                ))}
              </div>
            </div>

            {/* 2. Intensity Slider */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">Intensity:</span>
                <span className="font-mono font-bold text-slate-100 text-sm">
                  {intensityPercent}%
                </span>
              </div>

              {/* Slider Track conforming to reference image style */}
              <div className="relative flex items-center my-1">
                <input
                  type="range"
                  min="0.10"
                  max="1.00"
                  step="0.05"
                  value={hazard.intensity}
                  onChange={(e) => handleIntensityChange(Number(e.target.value))}
                  style={{
                    background: `linear-gradient(to right, #f43f5e 0%, #f43f5e ${intensityPercent}%, #e2e8f0 ${intensityPercent}%, #e2e8f0 100%)`,
                  }}
                  className="w-full h-2 rounded-full appearance-none cursor-pointer accent-rose-500 focus:outline-none shadow-inner"
                />
              </div>

              {/* Quick Preset Buttons for Intensity */}
              <div className="flex items-center gap-1.5 pt-0.5">
                {[
                  { label: '30%', val: 0.3 },
                  { label: '50%', val: 0.5 },
                  { label: '75%', val: 0.75 },
                  { label: '90%', val: 0.9 },
                ].map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => handleIntensityChange(item.val)}
                    className={`flex-1 py-1 rounded-md text-[10px] font-mono transition cursor-pointer ${
                      Math.abs(hazard.intensity - item.val) < 0.03
                        ? 'bg-rose-500/25 border border-rose-500/60 text-rose-300 font-bold'
                        : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/50'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Direct Run Simulation Action in Dropdown */}
          {onApplyHazard && (
            <div className="pt-3 mt-3 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => {
                  closeDropdown();
                  onApplyHazard();
                }}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-medium text-xs shadow-md transition disabled:opacity-50 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Recalculating Resilience...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Apply Measurements & Simulate</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
