export type NodeType = 'HQ' | 'Hub' | 'Warehouse';

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
  macro_corridors: Record<string, { name: string; description: string }>;
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
  hazard_type: 'cyclone' | 'flood' | 'strike' | 'heatwave' | 'infrastructure_failure';
  epicenter_lat: number;
  epicenter_lon: number;
  radius_km: number;
  severity: number;
  duration_hours?: number;
}

export interface CandidateRoute {
  path: string[];
  travel_time_hr: number;
  reliability_alpha: number;
  disruption_prob: number;
  resilience_score: number;
  hops: number;
  is_pareto_optimal?: boolean;
}

export interface ResilienceScorecard {
  overall_resilience: number;
  absorptive_capacity: number;
  restorative_capacity: number;
  adaptive_capacity: number;
  redundancy_metric: number;
  rapidity_metric: number;
  vulnerable_hubs: string[];
  high_risk_corridors: string[];
}

export interface TimelineFrame {
  hour: number;
  timestamp_offset: string;
  node_exposures: Record<string, number>;
  node_states: Record<string, string>;
  edge_disruption_probs: Record<string, number>;
  recommended_route: CandidateRoute | null;
  candidate_routes: CandidateRoute[];
  pruned_candidates_count: number;
  resilience_scorecard: ResilienceScorecard;
  active_hazard: HazardInput;
}

export interface EngineTimelineResult {
  simulation_id: string;
  hazard_applied: HazardInput;
  total_frames: number;
  time_horizon_hours: number;
  frames: TimelineFrame[];
}
