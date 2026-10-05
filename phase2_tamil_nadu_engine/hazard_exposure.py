"""
hazard_exposure.py — Spatial Hazard Exposure Engine
===================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Module: Spatial Interception & Continuous Hazard-Effect Mapping (PRD 9 §4)

Key Academic & Engineering Properties:
  - Continuous exposure model: exposure = intensity * (1.0 - distance / radius) in [0, 1].
  - Intensity directly scales the continuous degradation (a 10% flood yields 0.10 exposure;
    a 90% flood yields 0.90 exposure at epicenter).
  - Continuous exposure is discretized into CPT states:
      * exposure >= 0.60              -> High Disruption
      * 0.25 <= exposure < 0.60       -> Medium Disruption
      * 0.05 <= exposure < 0.25       -> Low Disruption
      * exposure < 0.05 (or d > r)    -> Baseline / Normal
  - Point-to-line segment orthogonal projection distance evaluates exact transit corridor
    interception across all network links.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic Schemas for Hazard Requests and Exposure Metrics
# ---------------------------------------------------------------------------

class HazardInput(BaseModel):
    """Specification of an interactive hazard placed on the Tamil Nadu map."""
    hazard_id: Optional[str] = Field(default="hz_01", description="Unique hazard cell identifier")
    hazard_type: str = Field(
        default="flood",
        description="Hazard type: flood, cyclone, heatwave, landslide, roadblock, hub_outage"
    )
    latitude: float = Field(..., ge=8.0, le=14.0, description="Latitude coordinate in Tamil Nadu")
    longitude: float = Field(..., ge=76.0, le=81.0, description="Longitude coordinate in Tamil Nadu")
    radius_km: float = Field(default=50.0, gt=0.0, le=300.0, description="Hazard radius of effect in kilometers")
    intensity: float = Field(default=0.70, ge=0.0, le=1.0, description="Normalized intensity [0.0, 1.0] (0-100%)")
    time_horizon: int = Field(default=10, ge=1, le=24, description="Simulation temporal horizon (hours)")


class NodeExposureResult(BaseModel):
    """Computed exposure and operational degradation for a single node."""
    node_id: str
    distance_km: float
    exposure_ratio: float       # Continuous exposure: intensity * falloff in [0, 1]
    disruption_state: str       # "Low" | "Medium" | "High" (discretized per PRD 9 §4)
    capacity_multiplier: float  # Remaining operational capacity factor [0.0, 1.0]
    hazard_type: str


class EdgeExposureResult(BaseModel):
    """Computed exposure and travel delay degradation for a network corridor link."""
    edge_id: str
    source: str
    target: str
    distance_km: float
    exposure_ratio: float       # Continuous exposure on closest point of edge segment
    disruption_state: str       # "Low" | "Medium" | "High"
    travel_time_factor: float   # Multiplier for travel time (e.g. 1.0 = normal, 3.2 = severe delay)
    on_time_prob_multiplier: float  # Multiplier for edge reliability [0.0, 1.0]
    operational_pct: float      # Remaining edge capacity percent [0.0, 1.0]


# ---------------------------------------------------------------------------
# Geospatial Distance Utilities
# ---------------------------------------------------------------------------

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes Great Circle distance between two points in km."""
    r_earth = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def point_to_segment_distance_km(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float
) -> float:
    """
    Computes minimum orthogonal distance from point P to line segment AB on an
    equirectangular local projection (valid for regional scales ~50-500 km).
    """
    mean_lat_rad = math.radians((a_lat + b_lat + p_lat) / 3.0)
    kx = 111.320 * math.cos(mean_lat_rad)  # km per degree longitude
    ky = 110.574                          # km per degree latitude

    px = (p_lon - a_lon) * kx
    py = (p_lat - a_lat) * ky
    bx = (b_lon - a_lon) * kx
    by = (b_lat - a_lat) * ky

    seg_len_sq = bx * bx + by * by
    if seg_len_sq <= 1e-6:
        return math.sqrt(px * px + py * py)

    t = (px * bx + py * by) / seg_len_sq
    t_clamped = max(0.0, min(1.0, t))

    qx = t_clamped * bx
    qy = t_clamped * by

    dx = px - qx
    dy = py - qy
    return math.sqrt(dx * dx + dy * dy)


# ---------------------------------------------------------------------------
# Continuous Hazard-Effect Mapping Engine
# ---------------------------------------------------------------------------

class HazardExposureEngine:
    """
    Maps continuous spatial exposure (intensity * falloff) into physical degradation
    and discrete evidence states for the DBN and RSPP-A* router.
    """

    HAZARD_SEVERITY_WEIGHTS = {
        "flood": {"node_drain": 0.85, "edge_delay": 2.8, "reliability_drain": 0.70},
        "cyclone": {"node_drain": 0.90, "edge_delay": 3.2, "reliability_drain": 0.75},
        "heatwave": {"node_drain": 0.40, "edge_delay": 1.4, "reliability_drain": 0.35},
        "landslide": {"node_drain": 0.95, "edge_delay": 4.5, "reliability_drain": 0.85},
        "roadblock": {"node_drain": 0.35, "edge_delay": 5.0, "reliability_drain": 0.90},
        "hub_outage": {"node_drain": 0.98, "edge_delay": 1.5, "reliability_drain": 0.50},
    }

    @staticmethod
    def exposure_to_disruption_state(exposure: float) -> str:
        """
        Discretizes continuous exposure [0.0, 1.0] into discrete CPT evidence states.
        Per PRD 9 §4:
          exposure >= 0.60         -> High
          0.25 <= exposure < 0.60  -> Medium
          0.05 <= exposure < 0.25  -> Low
          exposure < 0.05          -> Low (Baseline Clear)
        """
        if exposure >= 0.60:
            return "High"
        elif exposure >= 0.25:
            return "Medium"
        else:
            return "Low"

    @classmethod
    def evaluate_node_exposure(
        cls,
        node_id: str,
        node_lat: float,
        node_lon: float,
        hazard: HazardInput
    ) -> NodeExposureResult:
        dist_km = haversine_distance_km(hazard.latitude, hazard.longitude, node_lat, node_lon)
        r = hazard.radius_km
        intensity = hazard.intensity
        hz_type = hazard.hazard_type.lower()
        weights = cls.HAZARD_SEVERITY_WEIGHTS.get(hz_type, cls.HAZARD_SEVERITY_WEIGHTS["flood"])

        if dist_km >= r:
            return NodeExposureResult(
                node_id=node_id,
                distance_km=round(dist_km, 2),
                exposure_ratio=0.0,
                disruption_state="Low",
                capacity_multiplier=1.0,
                hazard_type=hz_type
            )

        # PRD 9 §4 Continuous linear falloff: 1.0 at epicenter to 0.0 at perimeter
        falloff = 1.0 - (dist_km / r)
        # Intensity directly scales the continuous exposure value!
        raw_exposure = max(0.0, min(1.0, intensity * falloff))

        # Discretize continuous exposure to discrete CPT state
        state = cls.exposure_to_disruption_state(raw_exposure)

        # Capacity scales continuously with raw_exposure
        cap_drain = weights["node_drain"] * raw_exposure
        cap_mult = max(0.05, 1.0 - cap_drain)

        return NodeExposureResult(
            node_id=node_id,
            distance_km=round(dist_km, 2),
            exposure_ratio=round(raw_exposure, 4),
            disruption_state=state,
            capacity_multiplier=round(cap_mult, 4),
            hazard_type=hz_type
        )

    @classmethod
    def evaluate_edge_exposure(
        cls,
        source_id: str,
        target_id: str,
        src_lat: float, src_lon: float,
        dst_lat: float, dst_lon: float,
        hazard: HazardInput
    ) -> EdgeExposureResult:
        edge_id = f"{source_id}__{target_id}"
        dist_km = point_to_segment_distance_km(
            hazard.latitude, hazard.longitude,
            src_lat, src_lon,
            dst_lat, dst_lon
        )
        r = hazard.radius_km
        intensity = hazard.intensity
        hz_type = hazard.hazard_type.lower()
        weights = cls.HAZARD_SEVERITY_WEIGHTS.get(hz_type, cls.HAZARD_SEVERITY_WEIGHTS["flood"])

        if dist_km >= r:
            return EdgeExposureResult(
                edge_id=edge_id,
                source=source_id,
                target=target_id,
                distance_km=round(dist_km, 2),
                exposure_ratio=0.0,
                disruption_state="Low",
                travel_time_factor=1.0,
                on_time_prob_multiplier=1.0,
                operational_pct=1.0
            )

        falloff = 1.0 - (dist_km / r)
        raw_exposure = max(0.0, min(1.0, intensity * falloff))
        state = cls.exposure_to_disruption_state(raw_exposure)

        # Continuous delay and reliability degradation
        tt_factor = 1.0 + (weights["edge_delay"] - 1.0) * raw_exposure
        rel_mult = max(0.05, 1.0 - weights["reliability_drain"] * raw_exposure)
        op_pct = max(0.05, 1.0 - 0.90 * raw_exposure)

        return EdgeExposureResult(
            edge_id=edge_id,
            source=source_id,
            target=target_id,
            distance_km=round(dist_km, 2),
            exposure_ratio=round(raw_exposure, 4),
            disruption_state=state,
            travel_time_factor=round(tt_factor, 3),
            on_time_prob_multiplier=round(rel_mult, 4),
            operational_pct=round(op_pct, 4)
        )
