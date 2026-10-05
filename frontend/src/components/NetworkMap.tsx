import React, { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, Circle, useMapEvents } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import type { NetworkResponse, GeoJSONPointFeature, GeoJSONLineFeature, HazardInput } from '../types/network';

interface NetworkMapProps {
  network: NetworkResponse | null;
  selectedNode: string | null;
  onSelectNode: (nodeId: string | null) => void;
  activeHazard: HazardInput | null;
  onMapClick?: (lat: number, lon: number) => void;
  highlightedRouteNodes?: string[];
  nodeExposures?: Record<string, number>;
}

// Center of Tamil Nadu (approx Trichy coordinates)
const TN_CENTER: LatLngExpression = [11.1271, 78.6569];
const DEFAULT_ZOOM = 7;

function MapEventsHandler({ onMapClick }: { onMapClick?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

export const NetworkMap: React.FC<NetworkMapProps> = ({
  network,
  selectedNode,
  onSelectNode,
  activeHazard,
  onMapClick,
  highlightedRouteNodes = [],
  nodeExposures = {},
}) => {
  // Separate points and lines from GeoJSON
  const { nodeFeatures, lineFeatures } = useMemo(() => {
    if (!network?.geojson?.features) {
      return { nodeFeatures: [], lineFeatures: [] };
    }
    const nodes: GeoJSONPointFeature[] = [];
    const lines: GeoJSONLineFeature[] = [];

    for (const f of network.geojson.features) {
      if (f.geometry.type === 'Point') {
        nodes.push(f as GeoJSONPointFeature);
      } else if (f.geometry.type === 'LineString') {
        lines.push(f as GeoJSONLineFeature);
      }
    }
    return { nodeFeatures: nodes, lineFeatures: lines };
  }, [network]);

  // Color generator based on node type and hazard exposure
  const getNodeColor = (type: string, exposure: number = 0, isHighlighted: boolean = false) => {
    if (isHighlighted) return '#38bdf8'; // Bright cyan for active route
    if (exposure > 0.6) return '#ef4444'; // Red (Severe hazard exposure)
    if (exposure > 0.3) return '#f97316'; // Orange (Moderate exposure)
    if (exposure > 0.05) return '#eab308'; // Yellow (Light exposure)

    switch (type) {
      case 'HQ':
        return '#0284c7'; // Deep Cyan/Sky
      case 'Hub':
        return '#8b5cf6'; // Indigo/Purple
      case 'Warehouse':
      default:
        return '#10b981'; // Emerald Green
    }
  };

  const getNodeRadius = (type: string) => {
    switch (type) {
      case 'HQ':
        return 9;
      case 'Hub':
        return 7;
      case 'Warehouse':
      default:
        return 5;
    }
  };

  // Basemap style options (100% Free, NO API Keys, NO Watermarks)
  const [basemap, setBasemap] = React.useState<'dark' | 'osm' | 'satellite'>('dark');

  const BASEMAPS = {
    dark: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      label: 'Dark Canvas',
    },
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      label: 'Street (OSM)',
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Source: Esri, Maxar, Earthstar Geographics',
      label: 'Satellite',
    },
  };

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden shadow-2xl border border-slate-800">
      <MapContainer
        center={TN_CENTER}
        zoom={DEFAULT_ZOOM}
        className="w-full h-full"
        scrollWheelZoom={true}
      >
        {/* Active Free Public Tile Layer */}
        <TileLayer
          key={basemap}
          attribution={BASEMAPS[basemap].attribution}
          url={BASEMAPS[basemap].url}
          maxZoom={19}
        />

        <MapEventsHandler onMapClick={onMapClick} />

        {/* 1. Macro Corridor Edges (LineStrings) */}
        {lineFeatures.map((line) => {
          const [uCoord, vCoord] = line.geometry.coordinates;
          const positions: [number, number][] = [
            [uCoord[1], uCoord[0]],
            [vCoord[1], vCoord[0]],
          ];

          const isRouteEdge =
            highlightedRouteNodes.length > 1 &&
            highlightedRouteNodes.some((node, i) => {
              const next = highlightedRouteNodes[i + 1];
              return (
                (line.properties.source === node && line.properties.target === next) ||
                (line.properties.target === node && line.properties.source === next)
              );
            });

          return (
            <Polyline
              key={line.id}
              positions={positions}
              pathOptions={{
                color: isRouteEdge ? '#38bdf8' : '#64748b',
                weight: isRouteEdge ? 4 : 2,
                opacity: isRouteEdge ? 0.95 : 0.45,
                dashArray: isRouteEdge ? undefined : '3, 4',
              }}
            >
              <Popup className="text-slate-900">
                <div className="text-xs font-sans">
                  <div className="font-bold text-slate-800 border-b pb-1 mb-1">
                    {line.properties.macro_corridor_name}
                  </div>
                  <div>Segment: <span className="font-semibold">{line.properties.source} &rarr; {line.properties.target}</span></div>
                  <div>Distance: <span className="font-semibold">{line.properties.distance_km} km</span></div>
                  <div>Est. Travel Time: <span className="font-semibold">{line.properties.travel_time_hr} hrs</span></div>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* 2. Active Hazard Circle (if placed) */}
        {activeHazard && (
          <Circle
            center={[activeHazard.epicenter_lat, activeHazard.epicenter_lon]}
            radius={activeHazard.radius_km * 1000}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#dc2626',
              fillOpacity: 0.25,
              weight: 2,
              dashArray: '4, 6',
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold text-red-600 uppercase tracking-wide">
                  Hazard: {activeHazard.hazard_type}
                </div>
                <div>Radius: {activeHazard.radius_km} km</div>
                <div>Severity: {(activeHazard.severity * 100).toFixed(0)}%</div>
              </div>
            </Popup>
          </Circle>
        )}

        {/* 3. Physical Network Nodes */}
        {nodeFeatures.map((node) => {
          const [lon, lat] = node.geometry.coordinates;
          const { id, name, type, district, tier } = node.properties;
          const exposure = nodeExposures[id] || 0;
          const isHighlighted = highlightedRouteNodes.includes(id);
          const isSelected = selectedNode === id;

          return (
            <CircleMarker
              key={id}
              center={[lat, lon]}
              radius={getNodeRadius(type) + (isSelected ? 3 : 0)}
              pathOptions={{
                fillColor: getNodeColor(type, exposure, isHighlighted),
                fillOpacity: 0.9,
                color: isSelected ? '#ffffff' : isHighlighted ? '#bae6fd' : '#0f172a',
                weight: isSelected ? 3 : 1.5,
              }}
              eventHandlers={{
                click: () => onSelectNode(id),
              }}
            >
              <Popup className="text-slate-900">
                <div className="text-xs font-sans min-w-[140px]">
                  <div className="flex items-center justify-between border-b pb-1 mb-1">
                    <span className="font-bold text-slate-900">{name}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                        type === 'HQ'
                          ? 'bg-sky-100 text-sky-800'
                          : type === 'Hub'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {type} (T{tier})
                    </span>
                  </div>
                  <div>District: <span className="font-medium">{district}</span></div>
                  <div>Coordinates: <span className="font-mono text-[11px]">{lat.toFixed(3)}, {lon.toFixed(3)}</span></div>
                  {exposure > 0 && (
                    <div className="mt-1 pt-1 border-t text-red-600 font-semibold">
                      Exposure: {(exposure * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Basemap Style Switcher (Top-Right) */}
      <div className="absolute top-4 right-4 z-[1000] bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-700/60 shadow-xl flex gap-1 pointer-events-auto">
        {(Object.keys(BASEMAPS) as Array<keyof typeof BASEMAPS>).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setBasemap(key)}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition ${
              basemap === key
                ? 'bg-sky-500 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {BASEMAPS[key].label}
          </button>
        ))}
      </div>

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/60 text-xs text-slate-200 shadow-xl pointer-events-auto">
        <div className="font-semibold text-slate-300 mb-1.5 text-[11px] uppercase tracking-wider">Topology Legend</div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-sky-500 border border-slate-900" />
            <span>Headquarters (3)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500 border border-slate-900" />
            <span>Regional Hubs (10)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 border border-slate-900" />
            <span>Warehouses (30)</span>
          </div>
          <div className="flex items-center gap-2 pt-1 border-t border-slate-800">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-red-300">Hazard Exposure</span>
          </div>
        </div>
      </div>
    </div>
  );
};
