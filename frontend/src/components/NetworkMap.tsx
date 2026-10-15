import React, { useMemo, useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, CircleMarker, Marker, Polyline, Popup, Circle, useMapEvents, useMap } from 'react-leaflet';
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
  nodeStates?: Record<string, string>;
  basemap?: 'dark' | 'street' | 'satellite';
  onBasemapChange?: (bm: 'dark' | 'street' | 'satellite') => void;
  theme?: 'light' | 'dark';
}

// Center of Tamil Nadu (approx Trichy coordinates)
const TN_CENTER: LatLngExpression = [11.1271, 78.6569];
const DEFAULT_ZOOM = 7;

function MapEventsHandler({
  onMapClick,
  onZoomChange,
}: {
  onMapClick?: (lat: number, lon: number) => void;
  onZoomChange?: (zoom: number) => void;
}) {
  const map = useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
    zoomend() {
      if (onZoomChange) {
        onZoomChange(map.getZoom());
      }
    },
    zoom() {
      if (onZoomChange) {
        onZoomChange(map.getZoom());
      }
    },
  });
  return null;
}

function MapFloatingControls({ isLight }: { isLight: boolean }) {
  const map = useMap();
  return (
    <div
      className={`absolute bottom-28 right-4 z-[1000] flex flex-col items-center gap-1 p-1 rounded-xl backdrop-blur-xl border shadow-xl font-mono select-none pointer-events-auto ${
        isLight
          ? 'bg-white/90 border-slate-300/80 text-slate-800'
          : 'bg-slate-900/85 border-slate-700/60 text-slate-200'
      }`}
    >
      <button
        type="button"
        onClick={() => map.zoomIn()}
        className={`w-9 h-8 flex items-center justify-center rounded-lg font-bold text-base transition-colors ${
          isLight
            ? 'hover:bg-slate-200/80 text-slate-800'
            : 'hover:bg-slate-800 text-slate-200 hover:text-white'
        }`}
        title="Zoom In"
      >
        +
      </button>
      <button
        type="button"
        onClick={() => map.zoomOut()}
        className={`w-9 h-8 flex items-center justify-center rounded-lg font-bold text-base transition-colors ${
          isLight
            ? 'hover:bg-slate-200/80 text-slate-800'
            : 'hover:bg-slate-800 text-slate-200 hover:text-white'
        }`}
        title="Zoom Out"
      >
        -
      </button>
      <div className={`w-7 h-[1px] my-0.5 ${isLight ? 'bg-slate-300' : 'bg-slate-700/80'}`} />
      <button
        type="button"
        onClick={() => map.setView(TN_CENTER, DEFAULT_ZOOM, { animate: true })}
        className={`px-2 py-1 text-[11px] font-sans font-medium rounded-lg transition-colors tracking-tight whitespace-nowrap ${
          isLight
            ? 'hover:bg-slate-200/80 text-slate-700 hover:text-sky-600'
            : 'hover:bg-slate-800 text-slate-300 hover:text-sky-300'
        }`}
        title="Recenter Tamil Nadu Network"
      >
        Recenter
      </button>
    </div>
  );
}

function RouteBoundsFitter({
  routeNodes,
  nodeCoordsMap,
}: {
  routeNodes: string[];
  nodeCoordsMap: Map<string, [number, number]>;
}) {
  const map = useMap();
  const prevNodesRef = useRef<string>('');

  useEffect(() => {
    if (routeNodes.length < 2) return;
    const key = `${routeNodes[0]}->${routeNodes[routeNodes.length - 1]}`;
    if (key !== prevNodesRef.current) {
      prevNodesRef.current = key;
      const latLngs: [number, number][] = [];
      for (const nid of routeNodes) {
        const c = nodeCoordsMap.get(nid);
        if (c) latLngs.push([c[1], c[0]]);
      }
      if (latLngs.length >= 2) {
        const bounds = L.latLngBounds(latLngs);
        map.flyToBounds(bounds, {
          padding: [70, 70],
          maxZoom: 9,
          duration: 1.0,
        });
      }
    }
  }, [routeNodes, nodeCoordsMap, map]);

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
  nodeStates = {},
  basemap,
  onBasemapChange,
  theme,
}) => {
  const [currentZoom, setCurrentZoom] = useState<number>(DEFAULT_ZOOM);

  // Dynamic HQ pin sizing based on map zoom level
  const getHqIconSize = (zoom: number, isSelected: boolean) => {
    // Scales smoothly according to zoom level (from ~24px at overview to ~70px at close zoom)
    const baseWidth = Math.max(22, Math.min(76, Math.round(34 * Math.pow(1.22, zoom - DEFAULT_ZOOM))));
    const width = isSelected ? Math.round(baseWidth * 1.25) : baseWidth;
    const height = Math.round(width * (356 / 300));
    return [width, height] as [number, number];
  };

  const createHqIcon = (
    width: number,
    height: number,
    isHighlighted: boolean,
    isSelected: boolean,
    state?: string,
    exposure: number = 0
  ) => {
    const isHighDisruption = state === 'High' || exposure > 0.6;
    const isMedDisruption = state === 'Medium' || exposure > 0.25;

    let filterStyle = 'drop-shadow(0 4px 6px rgba(0,0,0,0.6))';
    if (isSelected) {
      filterStyle = 'drop-shadow(0 0 12px rgba(56, 189, 248, 0.95)) drop-shadow(0 4px 6px rgba(0,0,0,0.6))';
    } else if (isHighlighted) {
      filterStyle = 'drop-shadow(0 0 10px rgba(56, 189, 248, 0.9))';
    } else if (isHighDisruption) {
      filterStyle = 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.95))';
    } else if (isMedDisruption) {
      filterStyle = 'drop-shadow(0 0 8px rgba(249, 115, 22, 0.85))';
    }

    const html = `
      <div style="
        width: ${width}px;
        height: ${height}px;
        position: relative;
        filter: ${filterStyle};
        transition: transform 0.15s ease-out;
        cursor: pointer;
        user-select: none;
      ">
        <img
          src="/hq-icon.png"
          alt="HQ"
          style="
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            pointer-events: none;
          "
        />
        ${isHighDisruption ? `
          <span style="
            position: absolute;
            top: 0px;
            right: 0px;
            width: 10px;
            height: 10px;
            background: #ef4444;
            border: 1.5px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 6px #ef4444;
          "></span>
        ` : ''}
      </div>
    `;

    return L.divIcon({
      html,
      className: 'hq-marker-icon',
      iconSize: [width, height],
      iconAnchor: [width / 2, height],
      popupAnchor: [0, -height + 4],
    });
  };

  // Dynamic Warehouse pin sizing based on map zoom level
  const getWarehouseIconSize = (zoom: number, isSelected: boolean) => {
    // 30 Warehouses scale proportionately with map zoom
    const baseWidth = Math.max(16, Math.min(56, Math.round(24 * Math.pow(1.22, zoom - DEFAULT_ZOOM))));
    const width = isSelected ? Math.round(baseWidth * 1.25) : baseWidth;
    const height = Math.round(width * (341 / 315));
    return [width, height] as [number, number];
  };

  const createWarehouseIcon = (
    width: number,
    height: number,
    isHighlighted: boolean,
    isSelected: boolean,
    state?: string,
    exposure: number = 0
  ) => {
    const isHighDisruption = state === 'High' || exposure > 0.6;
    const isMedDisruption = state === 'Medium' || exposure > 0.25;

    let filterStyle = 'drop-shadow(0 3px 5px rgba(0,0,0,0.5))';
    if (isSelected) {
      filterStyle = 'drop-shadow(0 0 10px rgba(56, 189, 248, 0.95)) drop-shadow(0 3px 5px rgba(0,0,0,0.6))';
    } else if (isHighlighted) {
      filterStyle = 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.9))';
    } else if (isHighDisruption) {
      filterStyle = 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.95))';
    } else if (isMedDisruption) {
      filterStyle = 'drop-shadow(0 0 6px rgba(249, 115, 22, 0.85))';
    }

    const html = `
      <div style="
        width: ${width}px;
        height: ${height}px;
        position: relative;
        filter: ${filterStyle};
        transition: transform 0.15s ease-out;
        cursor: pointer;
        user-select: none;
      ">
        <img
          src="/warehouse-icon.png"
          alt="Warehouse"
          style="
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            pointer-events: none;
          "
        />
        ${isHighDisruption ? `
          <span style="
            position: absolute;
            top: 0px;
            right: 0px;
            width: 8px;
            height: 8px;
            background: #ef4444;
            border: 1.5px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 5px #ef4444;
          "></span>
        ` : ''}
      </div>
    `;

    return L.divIcon({
      html,
      className: 'warehouse-marker-icon',
      iconSize: [width, height],
      iconAnchor: [width / 2, height],
      popupAnchor: [0, -height + 4],
    });
  };

  // Dynamic Regional Hub pin sizing based on map zoom level
  const getHubIconSize = (zoom: number, isSelected: boolean) => {
    // 10 Regional Hubs scale smoothly between HQ and Warehouse sizes
    const baseWidth = Math.max(18, Math.min(66, Math.round(29 * Math.pow(1.22, zoom - DEFAULT_ZOOM))));
    const width = isSelected ? Math.round(baseWidth * 1.25) : baseWidth;
    const height = Math.round(width * (358 / 310));
    return [width, height] as [number, number];
  };

  const createHubIcon = (
    width: number,
    height: number,
    isHighlighted: boolean,
    isSelected: boolean,
    state?: string,
    exposure: number = 0
  ) => {
    const isHighDisruption = state === 'High' || exposure > 0.6;
    const isMedDisruption = state === 'Medium' || exposure > 0.25;

    let filterStyle = 'drop-shadow(0 3.5px 5.5px rgba(0,0,0,0.55))';
    if (isSelected) {
      filterStyle = 'drop-shadow(0 0 11px rgba(56, 189, 248, 0.95)) drop-shadow(0 3.5px 5.5px rgba(0,0,0,0.6))';
    } else if (isHighlighted) {
      filterStyle = 'drop-shadow(0 0 9px rgba(56, 189, 248, 0.9))';
    } else if (isHighDisruption) {
      filterStyle = 'drop-shadow(0 0 9px rgba(239, 68, 68, 0.95))';
    } else if (isMedDisruption) {
      filterStyle = 'drop-shadow(0 0 7px rgba(249, 115, 22, 0.85))';
    }

    const html = `
      <div style="
        width: ${width}px;
        height: ${height}px;
        position: relative;
        filter: ${filterStyle};
        transition: transform 0.15s ease-out;
        cursor: pointer;
        user-select: none;
      ">
        <img
          src="/hub-icon.png"
          alt="Regional Hub"
          style="
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            pointer-events: none;
          "
        />
        ${isHighDisruption ? `
          <span style="
            position: absolute;
            top: 0px;
            right: 0px;
            width: 9px;
            height: 9px;
            background: #ef4444;
            border: 1.5px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 5px #ef4444;
          "></span>
        ` : ''}
      </div>
    `;

    return L.divIcon({
      html,
      className: 'hub-marker-icon',
      iconSize: [width, height],
      iconAnchor: [width / 2, height],
      popupAnchor: [0, -height + 4],
    });
  };

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

  // Index of node coordinates: node_id -> [lon, lat]
  const nodeCoordsMap = useMemo(() => {
    const map = new Map<string, [number, number]>();
    if (network?.geojson?.features) {
      for (const f of network.geojson.features) {
        if (f.geometry.type === 'Point') {
          const pf = f as GeoJSONPointFeature;
          map.set(pf.properties.id, pf.geometry.coordinates);
        }
      }
    }
    return map;
  }, [network]);

  // Google Maps-style OSRM road geometry state
  const [osrmRoadPositions, setOsrmRoadPositions] = useState<[number, number][]>([]);

  // Fetch curved driving highway geometry via OSRM when active route changes
  useEffect(() => {
    // Immediately clear previous road polyline to prevent ghost corridor display
    setOsrmRoadPositions([]);

    if (highlightedRouteNodes.length < 2) {
      return;
    }

    const coords: [number, number][] = [];
    for (const nid of highlightedRouteNodes) {
      const c = nodeCoordsMap.get(nid);
      if (c) coords.push(c);
    }

    if (coords.length < 2) {
      setOsrmRoadPositions([]);
      return;
    }

    // Topological straight-line fallback coordinates: [lat, lon]
    const fallbackCoords: [number, number][] = coords.map(([lon, lat]) => [lat, lon]);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const coordsParam = coords.map(([lon, lat]) => `${lon},${lat}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsParam}?overview=full&geometries=geojson`;

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`OSRM status ${res.status}`);
        return res.json();
      })
      .then((data) => {
        clearTimeout(timeoutId);
        if (data?.routes?.[0]?.geometry?.coordinates) {
          const roadPoints: [number, number][] = data.routes[0].geometry.coordinates.map(
            ([lon, lat]: [number, number]) => [lat, lon]
          );
          setOsrmRoadPositions(roadPoints);
        } else {
          setOsrmRoadPositions(fallbackCoords);
        }
      })
      .catch(() => {
        clearTimeout(timeoutId);
        setOsrmRoadPositions(fallbackCoords);
      });

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [highlightedRouteNodes, nodeCoordsMap]);

  // Color generator based on node type, hazard exposure, and DBN state
  const getNodeColor = (type: string, exposure: number = 0, state?: string, isHighlighted: boolean = false) => {
    if (isHighlighted) return '#38bdf8'; // Bright cyan for active route
    if (state === 'High' || exposure > 0.6) return '#ef4444'; // Red (Severe hazard exposure)
    if (state === 'Medium' || exposure > 0.25) return '#f97316'; // Orange (Moderate exposure)
    if (state === 'Low' || exposure > 0.05) return '#eab308'; // Yellow (Light exposure)

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
  const [internalBasemap, setInternalBasemap] = React.useState<'dark' | 'street' | 'satellite'>('dark');
  const activeBasemap = basemap !== undefined ? basemap : internalBasemap;
  const setBasemap = onBasemapChange || setInternalBasemap;
  const isLight = theme !== undefined ? theme === 'light' : activeBasemap === 'street';

  const BASEMAPS: Record<'dark' | 'street' | 'satellite', { url: string; attribution: string; label: string }> = {
    dark: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      label: 'Dark Canvas',
    },
    street: {
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
    <div className={`relative w-full h-full rounded-xl overflow-hidden shadow-2xl border transition-colors ${isLight ? 'border-slate-300/80' : 'border-slate-800'}`}>
      <MapContainer
        center={TN_CENTER}
        zoom={DEFAULT_ZOOM}
        className="w-full h-full"
        scrollWheelZoom={true}
        zoomControl={false}
      >
        {/* Active Free Public Tile Layer */}
        <TileLayer
          key={activeBasemap}
          attribution={BASEMAPS[activeBasemap].attribution}
          url={BASEMAPS[activeBasemap].url}
          maxZoom={19}
        />

        <MapEventsHandler onMapClick={onMapClick} onZoomChange={setCurrentZoom} />
        <MapFloatingControls isLight={isLight} />
        <RouteBoundsFitter routeNodes={highlightedRouteNodes} nodeCoordsMap={nodeCoordsMap} />

        {/* 1. Macro Corridor Edges (Subtle dashed highway background network) */}
        {lineFeatures.map((line) => {
          const [uCoord, vCoord] = line.geometry.coordinates;
          const positions: [number, number][] = [
            [uCoord[1], uCoord[0]],
            [vCoord[1], vCoord[0]],
          ];

          return (
            <Polyline
              key={line.id}
              positions={positions}
              pathOptions={{
                color: '#475569',
                weight: 1.5,
                opacity: 0.35,
                dashArray: '4, 6',
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

        {/* 1b. Active Resilient Route: Glowing Google Maps-Style Highway Polyline */}
        {osrmRoadPositions.length > 1 && (
          <Polyline
            positions={osrmRoadPositions}
            pathOptions={{
              color: '#38bdf8',
              weight: 5,
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round',
              className: 'route-glowing-highway',
            }}
          />
        )}

        {/* 2. Active Hazard Circle (if placed) */}
        {activeHazard && (
          <Circle
            center={[activeHazard.latitude, activeHazard.longitude]}
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
                <div>Intensity: {(activeHazard.intensity * 100).toFixed(0)}%</div>
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

          // Render Headquarters using custom zoom-responsive HQ icon
          if (type === 'HQ') {
            const [iconWidth, iconHeight] = getHqIconSize(currentZoom, isSelected);
            const hqIcon = createHqIcon(
              iconWidth,
              iconHeight,
              isHighlighted,
              isSelected,
              nodeStates[id],
              exposure
            );

            return (
              <Marker
                key={id}
                position={[lat, lon]}
                icon={hqIcon}
                eventHandlers={{
                  click: () => onSelectNode(id),
                }}
              >
                <Popup className="text-slate-900">
                  <div className="text-xs font-sans min-w-[150px]">
                    <div className="flex items-center justify-between border-b pb-1 mb-1 gap-2">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        <img src="/hq-icon.png" alt="HQ" className="w-4 h-4 object-contain" />
                        <span>{name}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold bg-sky-100 text-sky-800">
                        {type} (T{tier})
                      </span>
                    </div>
                    <div>District: <span className="font-medium">{district}</span></div>
                    <div>Coordinates: <span className="font-mono text-[11px]">{lat.toFixed(3)}, {lon.toFixed(3)}</span></div>
                    {nodeStates[id] && (
                      <div className="mt-1 pt-1 border-t flex justify-between">
                        <span className="text-slate-500">DBN Disruption:</span>
                        <span className={`font-bold ${nodeStates[id] === 'High' ? 'text-red-600' : nodeStates[id] === 'Medium' ? 'text-amber-600' : 'text-emerald-600'}`}>
                          {nodeStates[id]}
                        </span>
                      </div>
                    )}
                    {exposure > 0 && (
                      <div className="flex justify-between text-red-600 font-semibold">
                        <span>Spatial Exposure:</span>
                        <span>{(exposure * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          }

          // Render Warehouses using custom zoom-responsive Warehouse icon
          if (type === 'Warehouse') {
            const [iconWidth, iconHeight] = getWarehouseIconSize(currentZoom, isSelected);
            const warehouseIcon = createWarehouseIcon(
              iconWidth,
              iconHeight,
              isHighlighted,
              isSelected,
              nodeStates[id],
              exposure
            );

            return (
              <Marker
                key={id}
                position={[lat, lon]}
                icon={warehouseIcon}
                eventHandlers={{
                  click: () => onSelectNode(id),
                }}
              >
                <Popup className="text-slate-900">
                  <div className="text-xs font-sans min-w-[150px]">
                    <div className="flex items-center justify-between border-b pb-1 mb-1 gap-2">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        <img src="/warehouse-icon.png" alt="Warehouse" className="w-4 h-4 object-contain" />
                        <span>{name}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold bg-amber-100 text-amber-900">
                        {type} (T{tier})
                      </span>
                    </div>
                    <div>District: <span className="font-medium">{district}</span></div>
                    <div>Coordinates: <span className="font-mono text-[11px]">{lat.toFixed(3)}, {lon.toFixed(3)}</span></div>
                    {nodeStates[id] && (
                      <div className="mt-1 pt-1 border-t flex justify-between">
                        <span className="text-slate-500">DBN Disruption:</span>
                        <span className={`font-bold ${nodeStates[id] === 'High' ? 'text-red-600' : nodeStates[id] === 'Medium' ? 'text-amber-600' : 'text-emerald-600'}`}>
                          {nodeStates[id]}
                        </span>
                      </div>
                    )}
                    {exposure > 0 && (
                      <div className="flex justify-between text-red-600 font-semibold">
                        <span>Spatial Exposure:</span>
                        <span>{(exposure * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          }

          // Render Regional Hubs using custom zoom-responsive Hub icon
          if (type === 'Hub') {
            const [iconWidth, iconHeight] = getHubIconSize(currentZoom, isSelected);
            const hubIcon = createHubIcon(
              iconWidth,
              iconHeight,
              isHighlighted,
              isSelected,
              nodeStates[id],
              exposure
            );

            return (
              <Marker
                key={id}
                position={[lat, lon]}
                icon={hubIcon}
                eventHandlers={{
                  click: () => onSelectNode(id),
                }}
              >
                <Popup className="text-slate-900">
                  <div className="text-xs font-sans min-w-[150px]">
                    <div className="flex items-center justify-between border-b pb-1 mb-1 gap-2">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        <img src="/hub-icon.png" alt="Hub" className="w-4 h-4 object-contain" />
                        <span>{name}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold bg-emerald-100 text-emerald-900">
                        {type} (T{tier})
                      </span>
                    </div>
                    <div>District: <span className="font-medium">{district}</span></div>
                    <div>Coordinates: <span className="font-mono text-[11px]">{lat.toFixed(3)}, {lon.toFixed(3)}</span></div>
                    {nodeStates[id] && (
                      <div className="mt-1 pt-1 border-t flex justify-between">
                        <span className="text-slate-500">DBN Disruption:</span>
                        <span className={`font-bold ${nodeStates[id] === 'High' ? 'text-red-600' : nodeStates[id] === 'Medium' ? 'text-amber-600' : 'text-emerald-600'}`}>
                          {nodeStates[id]}
                        </span>
                      </div>
                    )}
                    {exposure > 0 && (
                      <div className="flex justify-between text-red-600 font-semibold">
                        <span>Spatial Exposure:</span>
                        <span>{(exposure * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          }

          // Fallback for any other custom node types
          return (
            <CircleMarker
              key={id}
              center={[lat, lon]}
              radius={getNodeRadius(type) + (isSelected ? 3 : 0)}
              pathOptions={{
                fillColor: getNodeColor(type, exposure, nodeStates[id], isHighlighted),
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
                    <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold bg-purple-100 text-purple-800">
                      {type} (T{tier})
                    </span>
                  </div>
                  <div>District: <span className="font-medium">{district}</span></div>
                  <div>Coordinates: <span className="font-mono text-[11px]">{lat.toFixed(3)}, {lon.toFixed(3)}</span></div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Basemap Style Switcher (Top-Right) */}
      <div
        className={`absolute top-4 right-4 z-[1000] p-1 rounded-lg backdrop-blur-md border shadow-xl flex gap-1 pointer-events-auto transition-colors ${
          isLight
            ? 'bg-white/85 border-slate-300/80 shadow-lg'
            : 'bg-slate-900/90 border-slate-700/60'
        }`}
      >
        {(Object.keys(BASEMAPS) as Array<keyof typeof BASEMAPS>).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setBasemap(key)}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition ${
              activeBasemap === key
                ? isLight
                  ? 'bg-sky-600 text-white font-semibold shadow'
                  : 'bg-sky-500 text-slate-950 font-semibold shadow'
                : isLight
                ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/80'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {BASEMAPS[key].label}
          </button>
        ))}
      </div>

      {/* Map Legend Overlay (Positioned above bottom timeline) */}
      <div
        className={`absolute bottom-26 left-4 z-[1000] px-3 py-2 rounded-lg backdrop-blur-md border text-xs shadow-xl pointer-events-auto transition-colors ${
          isLight
            ? 'bg-white/85 border-slate-300/80 text-slate-800'
            : 'bg-slate-900/90 border-slate-700/60 text-slate-200'
        }`}
      >
        <div className={`font-semibold mb-1.5 text-[11px] uppercase tracking-wider ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
          Topology Legend
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <img src="/hq-icon.png" alt="HQ" className="w-3.5 h-3.5 object-contain" />
            <span>Headquarters (3)</span>
          </div>
          <div className="flex items-center gap-2">
            <img src="/hub-icon.png" alt="Hub" className="w-3.5 h-3.5 object-contain" />
            <span>Regional Hubs (10)</span>
          </div>
          <div className="flex items-center gap-2">
            <img src="/warehouse-icon.png" alt="WH" className="w-3.5 h-3.5 object-contain" />
            <span>Warehouses (30)</span>
          </div>
          <div className={`flex items-center gap-2 pt-1 border-t ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
            <span className={isLight ? 'text-red-600 font-medium' : 'text-red-300'}>Hazard Exposure</span>
          </div>
        </div>
      </div>
    </div>
  );
};
