export type NodeType = 'HQ' | 'Hub' | 'Warehouse';
export type BasemapType = 'dark' | 'street' | 'satellite';

export interface NodeProperties {
  id: string;
  name: string;
  type: NodeType;
  tier: number;
  district: string;
  lat: number;
  lon: number;
  capacity_factor?: number;
}

export interface EdgeProperties {
  source: string;
  target: string;
  macro_corridor_id: string;
  macro_corridor_name: string;
  distance_km: number;
  travel_time_hr: number;
  on_time_prob: number;
  disruption_prob: number;
}

export interface GeoJSONPointFeature {
  type: 'Feature';
  id: string;
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  properties: NodeProperties;
}

export interface GeoJSONLineFeature {
  type: 'Feature';
  id: string;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][]; // [[lon, lat], [lon, lat]]
  };
  properties: EdgeProperties;
}

export interface NetworkResponse {
  network_name: string;
  nodes_summary: {
    total_nodes: number;
    hqs: number;
    hubs: number;
    warehouses: number;
  };
  edges_summary: {
    total_directed_edges: number;
    unique_routes: number;
    macro_corridors_count: number;
  };
  macro_corridors: Record<string, { name: string; description?: string }>;
  geojson: {
    type: 'FeatureCollection';
    features: (GeoJSONPointFeature | GeoJSONLineFeature)[];
  };
  routes: Array<{
    route_id: string;
    source: string;
    target: string;
    macro_corridor_id: string;
    macro_corridor_name: string;
    distance_km: number;
    travel_time_hr: number;
  }>;
}

export interface HazardInput {
  hazard_id?: string;
  hazard_type: string;
  latitude: number;
  longitude: number;
  radius_km: number;
  intensity: number;
  time_horizon?: number;
  source?: string;
  target?: string;
}

export interface CandidateRoute {
  route: string;
  path_nodes: string[];
  travel_time_hr: number;
  on_time_reliability_alpha: number;
  disruption_prob: number;
  hops: number;
}

export interface JiangResilienceScorecard {
  rapid_response: number;
  sustained_resistance: number;
  continuous_running: number;
  rapid_convergence: number;
  dynamic_evolution: number;
  overall_resilience_index: number;
}

export interface RouteStatus {
  route_id: string;
  source: string;
  target: string;
  corridor_id: string;
  corridor_name: string;
  distance_km: number;
  travel_time_hr: number;
  operational_pct: number;
  status: string;
}

export interface CascadeEffect {
  node: string;
  time_hour: number;
  cause: string;
  impact: string;
  severity: number;
}

export interface TimelineFrame {
  time_hour: number;
  node_states: Record<string, string>;
  node_posteriors: Record<string, Record<string, number>>;
  corridor_disruptions: Record<string, number>;
  route_status: RouteStatus[];
  cascade_effects: CascadeEffect[];
  network_operational_index: number;
}

export interface EngineTimelineResult {
  hazard_applied: HazardInput;
  frames: TimelineFrame[];
  resilience_scorecard: JiangResilienceScorecard;
  vulnerable_hub: string;
  high_risk_edge: string;
  primary_rerouted_solutions: CandidateRoute[];
  execution_time_ms: number;
  network_summary?: Record<string, any>;
}
