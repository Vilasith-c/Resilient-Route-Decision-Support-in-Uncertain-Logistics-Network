import React, { useState, useRef, useEffect } from 'react';
import {
  Radar,
  ChevronDown,
  Wind,
  Waves,
  Flame,
  CloudLightning,
  Mountain,
  Zap,
  AlertTriangle,
  Building2,
  Check,
  Play,
  Loader2,
} from 'lucide-react';
import type { HazardInput } from '../types/network';

interface HazardDropdownProps {
  hazard: HazardInput;
  onChangeHazard: (h: HazardInput) => void;
  onApplyHazard?: () => void;
  isLoading?: boolean;
  isOpen?: boolean;
  onToggle?: () => void;
  onClose?: () => void;
}

interface HazardOption {
  id: string;
  name: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  iconColor: string;
  bgCircleColor: string;
  defaultLat: number;
  defaultLon: number;
  defaultRadius: number;
  defaultIntensity: number;
}

const HAZARD_OPTIONS: HazardOption[] = [
  {
    id: 'cyclone',
    name: 'Cyclone',
    subtitle: 'Coastal Storm & Surge (NH-32 / ECR)',
    icon: Wind,
    iconColor: 'text-sky-500',
    bgCircleColor: 'bg-sky-50',
    defaultLat: 11.9401,
    defaultLon: 79.7719,
    defaultRadius: 50,
    defaultIntensity: 0.85,
  },
  {
    id: 'flood',
    name: 'Flood',
    subtitle: 'Cauvery Riverine & Delta Inundation',
    icon: Waves,
    iconColor: 'text-blue-600',
    bgCircleColor: 'bg-blue-50',
    defaultLat: 10.787,
    defaultLon: 79.1378,
    defaultRadius: 45,
    defaultIntensity: 0.75,
  },
  {
    id: 'heatwave',
    name: 'Heatwave',
    subtitle: 'Extreme Thermal Stress & Engine Delays',
    icon: Flame,
    iconColor: 'text-orange-500',
    bgCircleColor: 'bg-orange-50',
    defaultLat: 12.9165,
    defaultLon: 79.1325,
    defaultRadius: 60,
    defaultIntensity: 0.65,
  },
  {
    id: 'thunderstorm',
    name: 'Thunderstorm',
    subtitle: 'Severe Convective Squalls & Tree Falls',
    icon: CloudLightning,
    iconColor: 'text-purple-500',
    bgCircleColor: 'bg-purple-50',
    defaultLat: 11.0168,
    defaultLon: 76.9558,
    defaultRadius: 35,
    defaultIntensity: 0.7,
  },
  {
    id: 'landslide',
    name: 'Landslide',
    subtitle: 'Ghat Route Slope Failure (Nilgiris NH-181)',
    icon: Mountain,
    iconColor: 'text-amber-600',
    bgCircleColor: 'bg-amber-50',
    defaultLat: 11.4102,
    defaultLon: 76.695,
    defaultRadius: 25,
    defaultIntensity: 0.8,
  },
  {
    id: 'infrastructure_failure',
    name: 'Infrastructure Failure',
    subtitle: 'Critical Bridge / Substation Outage (NH-48)',
    icon: Zap,
    iconColor: 'text-rose-500',
    bgCircleColor: 'bg-rose-50',
    defaultLat: 12.9675,
    defaultLon: 79.9404,
    defaultRadius: 30,
    defaultIntensity: 0.85,
  },
  {
    id: 'strike',
    name: 'Transporter Strike',
    subtitle: 'Freight Blockade & Toll Stoppage (Salem)',
    icon: AlertTriangle,
    iconColor: 'text-yellow-500',
    bgCircleColor: 'bg-yellow-50',
    defaultLat: 11.6643,
    defaultLon: 78.146,
    defaultRadius: 40,
    defaultIntensity: 0.6,
  },
  {
    id: 'hub_outage',
    name: 'Hub Outage',
    subtitle: 'Central Distribution Center Disruption',
    icon: Building2,
    iconColor: 'text-red-500',
    bgCircleColor: 'bg-red-50',
    defaultLat: 9.9252,
    defaultLon: 78.1198,
    defaultRadius: 20,
    defaultIntensity: 0.95,
  },
];

export const HazardDropdown: React.FC<HazardDropdownProps> = ({
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

  const activeOption =
    HAZARD_OPTIONS.find((opt) => opt.id.toLowerCase() === hazard.hazard_type.toLowerCase()) ||
    HAZARD_OPTIONS[0];

  const handleSelectHazard = (option: HazardOption) => {
    onChangeHazard({
      ...hazard,
      hazard_type: option.id,
      latitude: option.defaultLat,
      longitude: option.defaultLon,
      radius_km: option.defaultRadius,
      intensity: option.defaultIntensity,
    });
    closeDropdown();
  };

  return (
    <div className="relative inline-block select-none" ref={dropdownRef}>
      {/* 
        Ventusky-styled Capsule Button 
        Matches format from image: White circular icon badge + dark rounded capsule with text "Hazard"
      */}
      <button
        type="button"
        onClick={toggleDropdown}
        className="flex items-center h-10 pl-1 pr-3.5 rounded-full bg-[#1e232a]/95 hover:bg-[#252b34] active:scale-[0.98] border border-slate-700/60 shadow-xl transition-all duration-200 cursor-pointer group backdrop-blur-md"
        title="Select Active Hazard Scenario"
      >
        {/* Left White Circular Icon Badge */}
        <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-md shrink-0">
          <Radar className="w-5 h-5 text-blue-600" strokeWidth={2.2} />
        </div>

        {/* Label: Hazard + selected badge indicator */}
        <div className="flex items-center gap-2 ml-2.5">
          <span className="font-bold text-white text-[13px] tracking-tight">
            Hazard
          </span>

          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-sky-950/80 text-sky-400 border border-sky-800/60 font-semibold tracking-wider">
            {activeOption.name}
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
        <div className="absolute top-12 left-0 z-[1100] w-84 bg-[#181d24]/98 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl p-2 text-slate-200 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="px-3 py-2 border-b border-slate-800/80 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Logistics Hazard Types
              </span>
              <p className="text-[10px] text-slate-500">
                Choose uncertainty event for route stress test
              </p>
            </div>
            <span className="text-[10px] font-mono text-sky-400 bg-sky-950/60 px-1.5 py-0.5 rounded border border-sky-800/50">
              {HAZARD_OPTIONS.length} Presets
            </span>
          </div>

          {/* List of Hazards */}
          <div className="flex flex-col gap-1 py-1.5 max-h-80 overflow-y-auto">
            {HAZARD_OPTIONS.map((item) => {
              const Icon = item.icon;
              const isSelected = item.id.toLowerCase() === hazard.hazard_type.toLowerCase();

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleSelectHazard(item)}
                  className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-sky-500/15 border border-sky-500/40 text-white'
                      : 'hover:bg-slate-800/60 border border-transparent text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    {/* Ventusky style mini circular badge */}
                    <div
                      className={`w-7 h-7 rounded-full ${item.bgCircleColor} flex items-center justify-center shrink-0 shadow-sm`}
                    >
                      <Icon className={`w-4 h-4 ${item.iconColor}`} strokeWidth={2.2} />
                    </div>

                    <div>
                      <div className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
                        {item.name}
                        {isSelected && (
                          <span className="text-[9px] bg-sky-500/20 text-sky-400 px-1.5 py-0.2 rounded font-mono font-normal">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {item.subtitle}
                      </div>
                    </div>
                  </div>

                  {isSelected && <Check className="w-4 h-4 text-sky-400 shrink-0 ml-2" />}
                </button>
              );
            })}
          </div>

          {/* Optional Direct Run Simulation Action in Dropdown */}
          {onApplyHazard && (
            <div className="pt-2 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => {
                  closeDropdown();
                  onApplyHazard();
                }}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-medium text-xs shadow-md transition disabled:opacity-50 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Evaluating Network Exposure...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Apply & Simulate {activeOption.name}</span>
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
