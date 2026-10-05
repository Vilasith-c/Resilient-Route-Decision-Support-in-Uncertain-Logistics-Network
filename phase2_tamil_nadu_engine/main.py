"""
main.py — FastAPI Application & Service Endpoints
=================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Module: Phase 2 - Backend REST API Service (Aligned with PRDs 1-10)

Endpoints:
  - GET  /health   : System status, versioning, network stats, and model readiness.
  - GET  /network  : Complete 43-node topology, 8 macro corridors, and GeoJSON FeatureCollection.
  - POST /hazard   : 8-stage simulation execution returning ENGINE_TIMELINE_RESULT
                     with Jiang et al. (2020) 5 DBN resilience capabilities.
"""

from __future__ import annotations
import os
import sys
import time
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local modules
from hazard_exposure import HazardInput
from corridor_model import TAMIL_NADU_CORRIDORS
from orchestrator import SimulationOrchestrator, EngineTimelineResult
from phase1_benchmark import TN_NODES, NODE_ALIASES, build_tamil_nadu_network, haversine_distance_km


# ---------------------------------------------------------------------------
# FastAPI Initialization & CORS Configuration
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Interactive Tamil Nadu Resilient Logistics Simulator API",
    description="High-performance backend serving DBN belief propagation, RSPP-A* routing, and spatial hazard simulations.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend applications (Vite / React running on any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singleton orchestrator initialized with the 43-node Tamil Nadu graph
base_network = build_tamil_nadu_network()
orchestrator = SimulationOrchestrator(base_network)


# ---------------------------------------------------------------------------
# 1. Health Check Endpoint
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Returns system status, active version, and model readiness."""
    return {
        "status": "healthy",
        "service": "Tamil Nadu Resilient Logistics Simulator Engine",
        "version": "2.1.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "network": {
            "total_nodes": len(TN_NODES),
            "hqs": 3,
            "hubs": 10,
            "warehouses": 30,
            "directed_edges": base_network.number_of_edges(),
            "macro_corridors": len(TAMIL_NADU_CORRIDORS),
        },
        "academic_framework": {
            "path_centric_corridor_model": "PACE / SPOTAR (Andonov & Yang)",
            "delay_distribution": "Jones & Faddy Skew-t / Skew-Normal",
            "routing_search": "RSPP-A* with FSD Dominance Pruning (Chen et al. 2012)",
            "resilience_scoring": "5 DBN Capabilities (Jiang et al. 2020)",
        },
        "python_version": sys.version.split()[0],
    }


# ---------------------------------------------------------------------------
# 2. Network Topology & GeoJSON Endpoint
# ---------------------------------------------------------------------------

@app.get("/network", tags=["Network"])
def get_network() -> Dict[str, Any]:
    """
    Returns the complete 43-node Tamil Nadu logistics topology.
    Includes:
      - GeoJSON FeatureCollection (Point features for nodes, LineString features for routes).
      - Structured registry of HQs, Hubs (including Thoothukudi), and Warehouses.
      - 8 Macro Corridors (PACE / SPOTAR path-centric dependency model).
      - Route travel times and baseline capacities.
    """
    # 1. Node features (Points)
    features: List[Dict[str, Any]] = []
    for node_id, data in TN_NODES.items():
        feat = {
            "type": "Feature",
            "id": node_id,
            "geometry": {
                "type": "Point",
                # GeoJSON coordinates format is [lon, lat]
                "coordinates": [data["lon"], data["lat"]],
            },
            "properties": {
                "id": node_id,
                "name": data["name"],
                "type": data["type"],
                "tier": data["tier"],
                "district": data["district"],
                "lat": data["lat"],
                "lon": data["lon"],
                "capacity_factor": data.get("capacity_factor", 0.8),
            }
        }
        features.append(feat)

    # 2. Corridor features (LineStrings)
    seen_undirected = set()
    routes_summary = []

    for u, v, data in base_network.edges(data=True):
        edge_key = tuple(sorted([u, v]))
        if edge_key not in seen_undirected:
            seen_undirected.add(edge_key)
            u_coord = [TN_NODES[u]["lon"], TN_NODES[u]["lat"]]
            v_coord = [TN_NODES[v]["lon"], TN_NODES[v]["lat"]]

            cid = data.get("corridor_id", "corridor_nh44_central_artery")
            cname = data.get("corridor_name", "Transit Corridor")

            feat = {
                "type": "Feature",
                "id": f"{u}__{v}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [u_coord, v_coord]
                },
                "properties": {
                    "source": u,
                    "target": v,
                    "macro_corridor_id": cid,
                    "macro_corridor_name": cname,
                    "distance_km": data["distance_km"],
                    "travel_time_hr": data["travel_time_hr"],
                    "on_time_prob": data["on_time_prob"],
                    "disruption_prob": data["disruption_prob"],
                }
            }
            features.append(feat)

            routes_summary.append({
                "route_id": f"{u}__{v}",
                "source": u,
                "target": v,
                "macro_corridor_id": cid,
                "macro_corridor_name": cname,
                "distance_km": data["distance_km"],
                "travel_time_hr": data["travel_time_hr"]
            })

    return {
        "network_name": "Tamil Nadu Resilient Logistics Multi-Echelon Network",
        "nodes_summary": {
            "total_nodes": len(TN_NODES),
            "hqs": 3,
            "hubs": 10,
            "warehouses": 30,
        },
        "edges_summary": {
            "total_directed_edges": base_network.number_of_edges(),
            "unique_routes": len(seen_undirected),
            "macro_corridors_count": len(TAMIL_NADU_CORRIDORS),
        },
        "macro_corridors": TAMIL_NADU_CORRIDORS,
        "geojson": {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features
        },
        "routes": routes_summary,
    }


# ---------------------------------------------------------------------------
# 3. Interactive Hazard Simulation Endpoint
# ---------------------------------------------------------------------------

@app.post("/hazard", response_model=EngineTimelineResult, tags=["Simulation"])
def simulate_hazard(hazard_request: HazardInput) -> EngineTimelineResult:
    """
    Simulates a placed hazard cell on Tamil Nadu:
      1. Spatial Hazard Interception (continuous exposure = intensity * falloff).
      2. Stage 2 SPOTAR / PACE Macro Corridor Correlated Dependency activation.
      3. Stage 3 Skew-t Discretized Delay Distributions CPT integration.
      4. Stage 5 DBN Belief Propagation across t_0 ... t_H.
      5. Stage 6 RSPP-A* Dynamic Re-routing with FSD Dominance Pruning.
      6. Stage 7 Jiang et al. (2020) 5 DBN Resilience Capabilities Scoring.
      7. Stage 8 Unified ENGINE_TIMELINE_RESULT payload assembly.
    """
    try:
        result = orchestrator.run_simulation(hazard_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
