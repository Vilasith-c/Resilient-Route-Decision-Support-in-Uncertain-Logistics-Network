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
  theme?: 'light' | 'dark';
}

export const MeasurementsDropdown: React.FC<MeasurementsDropdownProps> = ({
  hazard,
  onChangeHazard,
  onApplyHazard,
  isLoading = false,
  isOpen: controlledIsOpen,
  onToggle,
  onClose,
  theme = 'dark',
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isLight = theme === 'light';

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
  const trackBgColor = isLight ? '#cbd5e1' : '#334155';

  return (
    <div className="relative inline-block select-none" ref={dropdownRef}>
      {/* 
        Ventusky-styled Capsule Button for Measurements
        Apple White Frosted Glass in light mode vs. Obsidian Dark Glass in dark mode
      */}
      <button
        type="button"
        onClick={toggleDropdown}
        className={`flex items-center h-10 pl-1 pr-3.5 rounded-full active:scale-[0.98] shadow-xl transition-all duration-200 cursor-pointer group backdrop-blur-2xl ${
          isLight
            ? 'bg-white/80 hover:bg-white/95 border border-slate-300/70 text-slate-900'
            : 'bg-[#1e232a]/95 hover:bg-[#252b34] border border-slate-700/60 text-white'
        }`}
        title="Adjust Hazard Measurements (Radius & Intensity)"
      >
        {/* Left Circular Icon Badge */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center shadow-md shrink-0 ${
            isLight ? 'bg-slate-100 border border-slate-200/90' : 'bg-white'
          }`}
        >
          <SlidersHorizontal className="w-4.5 h-4.5 text-blue-600" strokeWidth={2.2} />
        </div>

        {/* Label: Measurements + dynamic values badge */}
        <div className="flex items-center gap-2 ml-2.5">
          <span className={`font-bold text-[13px] tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
            Measurements
          </span>

          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold tracking-wider ${
              isLight
                ? 'bg-sky-100 text-sky-800 border border-sky-300/80 shadow-xs'
                : 'bg-sky-950/80 text-sky-400 border border-sky-800/60'
            }`}
          >
            {hazard.radius_km} km &bull; {intensityPercent}%
          </span>
        </div>

        {/* Dropdown Chevron */}
        <ChevronDown
          className={`w-3.5 h-3.5 ml-2 transition-transform duration-200 ${
            isLight
              ? 'text-slate-500 group-hover:text-slate-900'
              : 'text-slate-400 group-hover:text-white'
          } ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Menu Overlay */}
      {isOpen && (
        <div
          className={`absolute top-12 left-0 z-[1100] w-84 backdrop-blur-2xl rounded-2xl shadow-2xl p-3.5 animate-in fade-in slide-in-from-top-2 duration-150 ${
            isLight
              ? 'bg-white/90 border border-slate-300/80 text-slate-800'
              : 'bg-[#181d24]/98 border border-slate-700/80 text-slate-200'
          }`}
        >
          <div className={`pb-2.5 mb-3 border-b flex items-center justify-between ${isLight ? 'border-slate-200/90' : 'border-slate-800/80'}`}>
            <div>
              <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-800' : 'text-slate-400'}`}>
                Hazard Measurements
              </span>
              <p className={`text-[10px] ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
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
              className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded transition cursor-pointer ${
                isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>

          <div className="flex flex-col gap-4">
            {/* 1. Radius Slider */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className={`font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Radius:</span>
                <span className={`font-mono font-bold text-sm ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>
                  {hazard.radius_km} <span className={`text-xs font-normal ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>km</span>
                </span>
              </div>

              {/* Slider Track */}
              <div className="relative flex items-center my-1">
                <input
                  type="range"
                  min="10"
                  max="150"
                  step="5"
                  value={hazard.radius_km}
                  onChange={(e) => handleRadiusChange(Number(e.target.value))}
                  style={{
                    background: `linear-gradient(to right, #f43f5e 0%, #f43f5e ${radiusPercent}%, ${trackBgColor} ${radiusPercent}%, ${trackBgColor} 100%)`,
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
                        ? isLight
                          ? 'bg-rose-100 border border-rose-400 text-rose-800 font-bold shadow-xs'
                          : 'bg-rose-500/25 border border-rose-500/60 text-rose-300 font-bold'
                        : isLight
                        ? 'bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200/90'
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
                <span className={`font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Intensity:</span>
                <span className={`font-mono font-bold text-sm ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>
                  {intensityPercent}%
                </span>
              </div>

              {/* Slider Track */}
              <div className="relative flex items-center my-1">
                <input
                  type="range"
                  min="0.10"
                  max="1.00"
                  step="0.05"
                  value={hazard.intensity}
                  onChange={(e) => handleIntensityChange(Number(e.target.value))}
                  style={{
                    background: `linear-gradient(to right, #f43f5e 0%, #f43f5e ${intensityPercent}%, ${trackBgColor} ${intensityPercent}%, ${trackBgColor} 100%)`,
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
                        ? isLight
                          ? 'bg-rose-100 border border-rose-400 text-rose-800 font-bold shadow-xs'
                          : 'bg-rose-500/25 border border-rose-500/60 text-rose-300 font-bold'
                        : isLight
                        ? 'bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200/90'
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
            <div className={`pt-3 mt-3 border-t ${isLight ? 'border-slate-200/90' : 'border-slate-800/80'}`}>
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
