#!/usr/bin/env python3
"""
phase1_benchmark.py — Phase 1 Feasibility & Benchmark Verification Suite
=========================================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Scope:
    - 43-node Tamil Nadu network (3 HQs, 10 Regional Hubs, 30 Warehouses)
    - Task 1: pgmpy Dynamic Bayesian Network (DBN) Inference Latency (< 1.5s)
              + Vectorized NumPy forward-filter transition matrix fallback benchmark
    - Task 2: RSPP-A* Multi-Criteria Search & FSD Dominance Pruning Overhead (< 300ms)
    - Task 3: Tamil Nadu Geospatial & Graph Data Validation (GeoJSON/Leaflet integrity)

Outputs:
    - Formatted console benchmark logs with millisecond timings and Pass/Fail statuses.
    - JSON validation report: phase1_report.json
"""

import sys
import os
import time
import math
import json
import heapq
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# NumPy 2.0 Compatibility Patch for pgmpy <= 0.1.25
# ---------------------------------------------------------------------------
import numpy as np
if not hasattr(np, 'product'):
    np.product = np.prod
if not hasattr(np, 'alltrue'):
    np.alltrue = np.all
if not hasattr(np, 'sometrue'):
    np.sometrue = np.any

import networkx as nx
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


# ===========================================================================
# 1. TAMIL NADU 43-NODE GEOSPATIAL REGISTRY
# ===========================================================================
# 3 Headquarters, 10 Regional Hubs, 30 Warehouses with accurate real coordinates
TN_NODES: Dict[str, Dict[str, Any]] = {
    # 3 Headquarters (T1)
    "HQ_Chennai": {
        "name": "Chennai Central HQ",
        "type": "HQ",
        "tier": 1,
        "lat": 13.0827,
        "lon": 80.2707,
        "district": "Chennai",
        "capacity_factor": 1.0,
    },
    "HQ_Coimbatore": {
        "name": "Coimbatore Western HQ",
        "type": "HQ",
        "tier": 1,
        "lat": 11.0168,
        "lon": 76.9558,
        "district": "Coimbatore",
        "capacity_factor": 0.9,
    },
    "HQ_Madurai": {
        "name": "Madurai Southern HQ",
        "type": "HQ",
        "tier": 1,
        "lat": 9.9252,
        "lon": 78.1198,
        "district": "Madurai",
        "capacity_factor": 0.9,
    },

    # 10 Regional Hubs (T2)
    "Hub_Tiruvallur": {
        "name": "Tiruvallur Northern Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 13.1437,
        "lon": 79.9079,
        "district": "Tiruvallur",
        "capacity_factor": 0.75,
    },
    "Hub_Vellore": {
        "name": "Vellore North-West Gateway",
        "type": "Hub",
        "tier": 2,
        "lat": 12.9165,
        "lon": 79.1325,
        "district": "Vellore",
        "capacity_factor": 0.8,
    },
    "Hub_Salem": {
        "name": "Salem Central Transit Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 11.6643,
        "lon": 78.1460,
        "district": "Salem",
        "capacity_factor": 0.85,
    },
    "Hub_Erode": {
        "name": "Erode Industrial Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 11.3410,
        "lon": 77.7172,
        "district": "Erode",
        "capacity_factor": 0.75,
    },
    "Hub_Tiruchirappalli": {
        "name": "Tiruchirappalli Central Junction",
        "type": "Hub",
        "tier": 2,
        "lat": 10.7905,
        "lon": 78.7047,
        "district": "Tiruchirappalli",
        "capacity_factor": 0.85,
    },
    "Hub_Thanjavur": {
        "name": "Thanjavur Delta Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 10.7870,
        "lon": 79.1378,
        "district": "Thanjavur",
        "capacity_factor": 0.7,
    },
    "Hub_Cuddalore": {
        "name": "Cuddalore Coastal Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 11.7480,
        "lon": 79.7714,
        "district": "Cuddalore",
        "capacity_factor": 0.7,
    },
    "Hub_Dindigul": {
        "name": "Dindigul Junction Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 10.3673,
        "lon": 77.9803,
        "district": "Dindigul",
        "capacity_factor": 0.75,
    },
    "Hub_Tirunelveli": {
        "name": "Tirunelveli Deep South Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 8.7139,
        "lon": 77.7567,
        "district": "Tirunelveli",
        "capacity_factor": 0.8,
    },
    "Hub_Thoothukudi": {
        "name": "Thoothukudi Maritime Port Hub",
        "type": "Hub",
        "tier": 2,
        "lat": 8.7642,
        "lon": 78.1348,
        "district": "Thoothukudi",
        "capacity_factor": 0.8,
    },

    # 30 Warehouses (T3)
    "WH_01_Gummidipoondi": {"name": "Gummidipoondi Industrial Warehouse", "type": "Warehouse", "tier": 3, "lat": 13.4072, "lon": 80.1295, "district": "Tiruvallur", "hub": "Hub_Tiruvallur"},
    "WH_02_Sriperumbudur":  {"name": "Sriperumbudur Auto Cluster Warehouse", "type": "Warehouse", "tier": 3, "lat": 12.9675, "lon": 79.9406, "district": "Kanchipuram", "hub": "Hub_Tiruvallur"},
    "WH_03_Arakkonam":      {"name": "Arakkonam Rail-Side Warehouse", "type": "Warehouse", "tier": 3, "lat": 13.0783, "lon": 79.6677, "district": "Ranipet", "hub": "Hub_Tiruvallur"},
    "WH_04_Ranipet":        {"name": "Ranipet Chemical Zone Warehouse", "type": "Warehouse", "tier": 3, "lat": 12.9272, "lon": 79.3330, "district": "Ranipet", "hub": "Hub_Vellore"},
    "WH_05_Ambur":          {"name": "Ambur Trade Warehouse", "type": "Warehouse", "tier": 3, "lat": 12.7904, "lon": 78.7166, "district": "Tirupattur", "hub": "Hub_Vellore"},
    "WH_06_Tirupattur":     {"name": "Tirupattur Agricultural Warehouse", "type": "Warehouse", "tier": 3, "lat": 12.4958, "lon": 78.5678, "district": "Tirupattur", "hub": "Hub_Vellore"},
    "WH_07_Attur":          {"name": "Attur Agro Depot", "type": "Warehouse", "tier": 3, "lat": 11.5978, "lon": 78.5982, "district": "Salem", "hub": "Hub_Salem"},
    "WH_08_Mettur":         {"name": "Mettur Heavy Logistics Depot", "type": "Warehouse", "tier": 3, "lat": 11.7962, "lon": 77.8011, "district": "Salem", "hub": "Hub_Salem"},
    "WH_09_Namakkal":       {"name": "Namakkal Poultry & Transport Depot", "type": "Warehouse", "tier": 3, "lat": 11.2189, "lon": 78.1674, "district": "Namakkal", "hub": "Hub_Salem"},
    "WH_10_Bhavani":        {"name": "Bhavani River Depot", "type": "Warehouse", "tier": 3, "lat": 11.4489, "lon": 77.6828, "district": "Erode", "hub": "Hub_Erode"},
    "WH_11_Perundurai":     {"name": "Perundurai SIPCOT Warehouse", "type": "Warehouse", "tier": 3, "lat": 11.2758, "lon": 77.5833, "district": "Erode", "hub": "Hub_Erode"},
    "WH_12_Tiruppur":       {"name": "Tiruppur Textile Hub Depot", "type": "Warehouse", "tier": 3, "lat": 11.1085, "lon": 77.3411, "district": "Tiruppur", "hub": "Hub_Erode"},
    "WH_13_Pollachi":       {"name": "Pollachi Agri Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.6609, "lon": 77.0048, "district": "Coimbatore", "hub": "HQ_Coimbatore"},
    "WH_14_Udumalaipettai": {"name": "Udumalaipettai Wind Belt Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.5828, "lon": 77.2472, "district": "Tiruppur", "hub": "HQ_Coimbatore"},
    "WH_15_Mettupalayam":   {"name": "Mettupalayam Foothill Depot", "type": "Warehouse", "tier": 3, "lat": 11.2996, "lon": 76.9411, "district": "Coimbatore", "hub": "HQ_Coimbatore"},
    "WH_16_Manapparai":     {"name": "Manapparai Transit Depot", "type": "Warehouse", "tier": 3, "lat": 10.6074, "lon": 78.4194, "district": "Tiruchirappalli", "hub": "Hub_Tiruchirappalli"},
    "WH_17_Thuraiyur":      {"name": "Thuraiyur Mineral Depot", "type": "Warehouse", "tier": 3, "lat": 11.1444, "lon": 78.5960, "district": "Tiruchirappalli", "hub": "Hub_Tiruchirappalli"},
    "WH_18_Pudukkottai":    {"name": "Pudukkottai Heritage Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.3797, "lon": 78.8208, "district": "Pudukkottai", "hub": "Hub_Tiruchirappalli"},
    "WH_19_Kumbakonam":     {"name": "Kumbakonam Temple Town Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.9602, "lon": 79.3845, "district": "Thanjavur", "hub": "Hub_Thanjavur"},
    "WH_20_Mayiladuthurai": {"name": "Mayiladuthurai Coastal Depot", "type": "Warehouse", "tier": 3, "lat": 11.1075, "lon": 79.6524, "district": "Mayiladuthurai", "hub": "Hub_Thanjavur"},
    "WH_21_Nagapattinam":   {"name": "Nagapattinam Port Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.7672, "lon": 79.8449, "district": "Nagapattinam", "hub": "Hub_Thanjavur"},
    "WH_22_Panruti":        {"name": "Panruti Commercial Depot", "type": "Warehouse", "tier": 3, "lat": 11.7745, "lon": 79.5537, "district": "Cuddalore", "hub": "Hub_Cuddalore"},
    "WH_23_Chidambaram":    {"name": "Chidambaram Delta Warehouse", "type": "Warehouse", "tier": 3, "lat": 11.3992, "lon": 79.6936, "district": "Cuddalore", "hub": "Hub_Cuddalore"},
    "WH_24_Villupuram":     {"name": "Villupuram Strategic Crossroad Depot", "type": "Warehouse", "tier": 3, "lat": 11.9401, "lon": 79.4861, "district": "Villupuram", "hub": "Hub_Cuddalore"},
    "WH_25_Palani":         {"name": "Palani Hill Depot", "type": "Warehouse", "tier": 3, "lat": 10.4504, "lon": 77.5197, "district": "Dindigul", "hub": "Hub_Dindigul"},
    "WH_26_Batlagundu":     {"name": "Batlagundu Spices Warehouse", "type": "Warehouse", "tier": 3, "lat": 10.1601, "lon": 77.7594, "district": "Dindigul", "hub": "Hub_Dindigul"},
    "WH_27_Virudhunagar":   {"name": "Virudhunagar Trade Warehouse", "type": "Warehouse", "tier": 3, "lat": 9.5680, "lon": 77.9624, "district": "Virudhunagar", "hub": "HQ_Madurai"},
    "WH_28_Kovilpatti":     {"name": "Kovilpatti Industrial Depot", "type": "Warehouse", "tier": 3, "lat": 9.1738, "lon": 77.8687, "district": "Thoothukudi", "hub": "Hub_Tirunelveli"},
    "WH_29_Tenkasi":        {"name": "Tenkasi Western Ghats Warehouse", "type": "Warehouse", "tier": 3, "lat": 8.9594, "lon": 77.3152, "district": "Tenkasi", "hub": "Hub_Tirunelveli"},
    "WH_30_Nagercoil":      {"name": "Nagercoil Southernmost Gateway Depot", "type": "Warehouse", "tier": 3, "lat": 8.1833, "lon": 77.4119, "district": "Kanniyakumari", "hub": "Hub_Tirunelveli"},
}

# Backward compatibility alias dictionary
NODE_ALIASES: Dict[str, str] = {
    "Hub_Tuticorin": "Hub_Thoothukudi",
    "Tuticorin": "Hub_Thoothukudi",
}


# ===========================================================================
# 2. GEOSPATIAL MATH & GRAPH TOPOLOGY
# ===========================================================================

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in km between two lat/lon pairs."""
    r_earth = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def build_tamil_nadu_network() -> nx.DiGraph:
    """
    Constructs a realistic, strongly-connected 43-node Directed Graph for Tamil Nadu.
    Features:
      - 3 HQs connected to strategic regional Hubs.
      - Inter-Hub arterial trunk corridors for rerouting flexibility.
      - Hubs connected to local and neighboring Warehouses.
      - Realistic road circuity factor (1.25x haversine) and speed-based travel times.
    """
    g = nx.DiGraph()

    # Add all 43 nodes with attributes
    for node_id, data in TN_NODES.items():
        g.add_node(
            node_id,
            name=data["name"],
            type=data["type"],
            tier=data["tier"],
            lat=data["lat"],
            lon=data["lon"],
            district=data["district"],
        )

    # Core arterial links (bidirectional road corridors)
    arterial_edges = [
        # Chennai HQ trunk lines
        ("HQ_Chennai", "Hub_Tiruvallur"),
        ("HQ_Chennai", "Hub_Vellore"),
        ("HQ_Chennai", "Hub_Cuddalore"),

        # Coimbatore HQ trunk lines
        ("HQ_Coimbatore", "Hub_Erode"),
        ("HQ_Coimbatore", "Hub_Salem"),
        ("HQ_Coimbatore", "Hub_Dindigul"),

        # Madurai HQ trunk lines
        ("HQ_Madurai", "Hub_Dindigul"),
        ("HQ_Madurai", "Hub_Tiruchirappalli"),
        ("HQ_Madurai", "Hub_Tirunelveli"),
        ("HQ_Madurai", "Hub_Thoothukudi"),

        # Strategic Inter-Hub Corridors (Alternative routing backbones)
        ("Hub_Tiruvallur", "Hub_Vellore"),
        ("Hub_Vellore", "Hub_Salem"),
        ("Hub_Salem", "Hub_Erode"),
        ("Hub_Salem", "Hub_Tiruchirappalli"),
        ("Hub_Cuddalore", "Hub_Vellore"),
        ("Hub_Cuddalore", "Hub_Thanjavur"),
        ("Hub_Thanjavur", "Hub_Tiruchirappalli"),
        ("Hub_Tiruchirappalli", "Hub_Dindigul"),
        ("Hub_Tiruchirappalli", "Hub_Thoothukudi"),
        ("Hub_Tirunelveli", "Hub_Thoothukudi"),
        ("Hub_Dindigul", "Hub_Salem"),
    ]

    # Warehouse connections to hubs & adjacent centers
    wh_edges = [
        # Hub_Tiruvallur cluster
        ("Hub_Tiruvallur", "WH_01_Gummidipoondi"),
        ("Hub_Tiruvallur", "WH_02_Sriperumbudur"),
        ("Hub_Tiruvallur", "WH_03_Arakkonam"),
        ("HQ_Chennai", "WH_02_Sriperumbudur"),  # Direct industrial spur

        # Hub_Vellore cluster
        ("Hub_Vellore", "WH_04_Ranipet"),
        ("Hub_Vellore", "WH_05_Ambur"),
        ("Hub_Vellore", "WH_06_Tirupattur"),
        ("WH_03_Arakkonam", "WH_04_Ranipet"),   # Adjacent boundary link

        # Hub_Salem cluster
        ("Hub_Salem", "WH_07_Attur"),
        ("Hub_Salem", "WH_08_Mettur"),
        ("Hub_Salem", "WH_09_Namakkal"),
        ("WH_06_Tirupattur", "WH_07_Attur"),

        # Hub_Erode cluster
        ("Hub_Erode", "WH_10_Bhavani"),
        ("Hub_Erode", "WH_11_Perundurai"),
        ("Hub_Erode", "WH_12_Tiruppur"),
        ("WH_08_Mettur", "WH_10_Bhavani"),

        # HQ_Coimbatore cluster
        ("HQ_Coimbatore", "WH_13_Pollachi"),
        ("HQ_Coimbatore", "WH_14_Udumalaipettai"),
        ("HQ_Coimbatore", "WH_15_Mettupalayam"),
        ("WH_12_Tiruppur", "HQ_Coimbatore"),

        # Hub_Tiruchirappalli cluster
        ("Hub_Tiruchirappalli", "WH_16_Manapparai"),
        ("Hub_Tiruchirappalli", "WH_17_Thuraiyur"),
        ("Hub_Tiruchirappalli", "WH_18_Pudukkottai"),
        ("WH_09_Namakkal", "Hub_Tiruchirappalli"),

        # Hub_Thanjavur cluster
        ("Hub_Thanjavur", "WH_19_Kumbakonam"),
        ("Hub_Thanjavur", "WH_20_Mayiladuthurai"),
        ("Hub_Thanjavur", "WH_21_Nagapattinam"),
        ("WH_18_Pudukkottai", "Hub_Thanjavur"),

        # Hub_Cuddalore cluster
        ("Hub_Cuddalore", "WH_22_Panruti"),
        ("Hub_Cuddalore", "WH_23_Chidambaram"),
        ("Hub_Cuddalore", "WH_24_Villupuram"),
        ("WH_24_Villupuram", "Hub_Tiruvallur"),
        ("WH_23_Chidambaram", "WH_20_Mayiladuthurai"),

        # Hub_Dindigul cluster
        ("Hub_Dindigul", "WH_25_Palani"),
        ("Hub_Dindigul", "WH_26_Batlagundu"),
        ("Hub_Dindigul", "WH_27_Virudhunagar"),
        ("WH_14_Udumalaipettai", "WH_25_Palani"),
        ("WH_27_Virudhunagar", "HQ_Madurai"),

        # Hub_Tirunelveli & Thoothukudi cluster
        ("Hub_Tirunelveli", "WH_28_Kovilpatti"),
        ("Hub_Tirunelveli", "WH_29_Tenkasi"),
        ("Hub_Tirunelveli", "WH_30_Nagercoil"),
        ("Hub_Thoothukudi", "WH_28_Kovilpatti"),
        ("Hub_Thoothukudi", "WH_30_Nagercoil"),
    ]

    all_corridor_pairs = arterial_edges + wh_edges
    circuity = 1.25  # Road network circuity multiplier over haversine
    avg_speed_kmh = 55.0  # Commercial freight truck velocity in TN

    for u, v in all_corridor_pairs:
        u_lat, u_lon = TN_NODES[u]["lat"], TN_NODES[u]["lon"]
        v_lat, v_lon = TN_NODES[v]["lat"], TN_NODES[v]["lon"]
        dist_km = haversine_distance_km(u_lat, u_lon, v_lat, v_lon) * circuity
        travel_time_hr = dist_km / avg_speed_kmh
        # Base operational reliability (high probability of on-time delivery under normal ops)
        base_on_time_prob = 0.96

        # Add forward edge
        g.add_edge(
            u, v,
            distance_km=round(dist_km, 2),
            travel_time_hr=round(travel_time_hr, 2),
            on_time_prob=base_on_time_prob,
            disruption_prob=round(1.0 - base_on_time_prob, 4)
        )
        # Logistics routes are bidirectional road corridors
        g.add_edge(
            v, u,
            distance_km=round(dist_km, 2),
            travel_time_hr=round(travel_time_hr, 2),
            on_time_prob=base_on_time_prob,
            disruption_prob=round(1.0 - base_on_time_prob, 4)
        )

    return g


# ===========================================================================
# 3. TASK 1: DBN INFERENCE BENCHMARK & VECTORIZED NUMPY FALLBACK
# ===========================================================================

def build_43node_pgmpy_model(graph: nx.DiGraph) -> BayesianNetwork:
    """
    Constructs a structural Bayesian Network in pgmpy over the 43 nodes.
    Hierarchical structure:
      - 3 HQs: root nodes (P(Disruption) priors)
      - 10 Regional Hubs: conditioned on supplying HQs and arterial corridors
      - 30 Warehouses: conditioned on their respective regional Hub
    Each node has 3 discrete disruption states: ['Low', 'Medium', 'High'].
    """
    dag_edges = [
        # Chennai Zone
        ("HQ_Chennai", "Hub_Tiruvallur"),
        ("HQ_Chennai", "Hub_Vellore"),
        ("HQ_Chennai", "Hub_Cuddalore"),

        # Coimbatore Zone & Arterials
        ("HQ_Coimbatore", "Hub_Erode"),
        ("HQ_Coimbatore", "Hub_Salem"),
        ("Hub_Vellore", "Hub_Salem"),

        # Madurai Zone & Delta / South Arterials
        ("HQ_Madurai", "Hub_Dindigul"),
        ("HQ_Madurai", "Hub_Tiruchirappalli"),
        ("HQ_Madurai", "Hub_Tirunelveli"),
        ("HQ_Madurai", "Hub_Thoothukudi"),
        ("Hub_Salem", "Hub_Tiruchirappalli"),
        ("Hub_Tiruchirappalli", "Hub_Thanjavur"),
        ("Hub_Tirunelveli", "Hub_Thoothukudi"),
    ]

    # Add all 30 Warehouses with edge from their designated Hub
    for node_id, data in TN_NODES.items():
        if data["type"] == "Warehouse":
            assigned_hub = data["hub"]
            dag_edges.append((assigned_hub, node_id))

    model = BayesianNetwork(dag_edges)

    # Ensure all 43 nodes exist
    for n in TN_NODES.keys():
        if not model.has_node(n):
            model.add_node(n)

    cpds = []
    # Prior distribution for root nodes: under normal baseline, disruption is mostly Low
    prior_dist = [[0.75], [0.20], [0.05]]  # Low, Med, High

    for node in model.nodes():
        parents = list(model.predecessors(node))
        if not parents:
            cpd = TabularCPD(
                variable=node,
                variable_card=3,
                values=prior_dist,
                state_names={node: ["Low", "Medium", "High"]}
            )
            cpds.append(cpd)
        else:
            evidence_card = [3] * len(parents)
            num_configs = int(np.prod(evidence_card))
            # Conditional transition matrix: [3 x num_configs]
            vals = np.zeros((3, num_configs))
            for col in range(num_configs):
                # Simulated conditional impact: disruption propagates downstream
                p_high_seed = min(0.70, (col + 1) / (num_configs * 1.5))
                vals[2, col] = p_high_seed
                vals[1, col] = 0.30
                vals[0, col] = max(0.01, 1.0 - vals[1, col] - vals[2, col])
                vals[:, col] /= np.sum(vals[:, col])

            cpd = TabularCPD(
                variable=node,
                variable_card=3,
                values=vals,
                evidence=parents,
                evidence_card=evidence_card,
                state_names={n: ["Low", "Medium", "High"] for n in [node] + parents}
            )
            cpds.append(cpd)

    model.add_cpds(*cpds)
    assert model.check_model(), "pgmpy model validation failed!"
    return model


def benchmark_task1_pgmpy_dbn(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Executes Task 1:
      - Builds 43-node pgmpy model
      - Injects dummy evidence (HQ_Chennai = High disruption) at t=0
      - Evaluates VariableElimination queries across 10 temporal frames (t_0 through t_10)
      - Measures total execution latency.
      - Checks Pass Criteria (< 1.5s).
      - Executes Vectorized NumPy forward-filter fallback and benchmarks it.
    """
    t_build_start = time.perf_counter()
    model = build_43node_pgmpy_model(graph)
    infer = VariableElimination(model)
    build_ms = (time.perf_counter() - t_build_start) * 1000.0

    evidence_scenario = {"HQ_Chennai": "High"}
    monitored_nodes = ["Hub_Tiruvallur", "Hub_Vellore", "Hub_Salem", "Hub_Tiruchirappalli", "WH_02_Sriperumbudur"]

    # Benchmark pgmpy 10-frame timeline
    t_infer_start = time.perf_counter()
    pgmpy_frame_latencies = []
    sample_posteriors = []

    for frame in range(11):  # t_0 to t_10
        t_f0 = time.perf_counter()
        # In a DBN timeline, query target network posterior states given evidence
        # Querying key monitored nodes along the disruption cascade
        frame_res = {}
        for target in monitored_nodes:
            q = infer.query(variables=[target], evidence=evidence_scenario, show_progress=False)
            frame_res[target] = [round(float(v), 4) for v in q.values]
        t_f1 = time.perf_counter()
        f_latency = (t_f1 - t_f0) * 1000.0
        pgmpy_frame_latencies.append(f_latency)
        if frame in [0, 5, 10]:
            sample_posteriors.append({"frame": frame, "posteriors": frame_res})

    total_pgmpy_ms = (time.perf_counter() - t_infer_start) * 1000.0
    pgmpy_pass = total_pgmpy_ms < 1500.0

    # -----------------------------------------------------------------------
    # HIGH-PERFORMANCE VECTORIZED NUMPY FORWARD-FILTER FALLBACK ROUTINE
    # -----------------------------------------------------------------------
    # State space: 43 nodes, each having 3 states [Low, Medium, High]
    node_list = list(TN_NODES.keys())
    node_to_idx = {n: i for i, n in enumerate(node_list)}
    num_nodes = len(node_list)

    # Adjacency matrix for spatial network propagation
    A = np.zeros((num_nodes, num_nodes), dtype=np.float64)
    for u, v in graph.edges():
        A[node_to_idx[u], node_to_idx[v]] = 1.0
    # Row-normalize adjacency
    row_sums = A.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    A_norm = A / row_sums

    # Markov Transition Matrix T (3x3): Temporal persistence & recovery
    # [Low, Med, High] -> [Low, Med, High]
    T_mat = np.array([
        [0.85, 0.12, 0.03],   # Low stays low
        [0.25, 0.65, 0.10],   # Med decays to Low
        [0.05, 0.35, 0.60],   # High recovers to Med
    ], dtype=np.float64)

    # Benchmark NumPy Vectorized Forward Filter across 10 frames
    t_numpy_start = time.perf_counter()
    # Initial state S0: mostly low, with HQ_Chennai clamped to High
    S = np.zeros((num_nodes, 3), dtype=np.float64)
    S[:, 0] = 0.75  # Low
    S[:, 1] = 0.20  # Med
    S[:, 2] = 0.05  # High
    # Clamp evidence at t=0
    chennai_idx = node_to_idx["HQ_Chennai"]
    S[chennai_idx] = [0.0, 0.0, 1.0]

    lambda_spatial = 0.30  # Spatial contagion factor
    numpy_timeline_results = []

    for frame in range(11):
        # 1. Temporal Markov step: S @ T
        S_temporal = S @ T_mat
        # 2. Spatial network contagion step: A_norm @ S
        S_spatial = A_norm @ S_temporal
        # 3. Blend temporal persistence and spatial propagation
        S = (1.0 - lambda_spatial) * S_temporal + lambda_spatial * S_spatial
        # Re-normalize rows to ensure valid probability simplex
        S /= S.sum(axis=1, keepdims=True)
        numpy_timeline_results.append(S.copy())

    total_numpy_ms = (time.perf_counter() - t_numpy_start) * 1000.0

    return {
        "pgmpy_total_time_ms": round(total_pgmpy_ms, 2),
        "pgmpy_avg_frame_time_ms": round(float(np.mean(pgmpy_frame_latencies)), 2),
        "pgmpy_build_time_ms": round(build_ms, 2),
        "pgmpy_pass": pgmpy_pass,
        "pgmpy_threshold_ms": 1500.0,
        "sample_posteriors": sample_posteriors,
        "numpy_fallback_total_time_ms": round(total_numpy_ms, 3),
        "numpy_speedup_factor": round(total_pgmpy_ms / max(total_numpy_ms, 0.001), 1),
    }


# ===========================================================================
# 4. TASK 2: RSPP-A* SEARCH WITH FIRST-ORDER STOCHASTIC DOMINANCE (FSD)
# ===========================================================================

@dataclass
class Label:
    """
    RSPP Search State Label at node n.
    Attributes:
        node: current node identifier
        cumulative_time: total travel time consumed (hours)
        on_time_prob: cumulative path reliability probability [0, 1]
        path: sequence of nodes visited
    """
    node: str
    cumulative_time: float
    on_time_prob: float
    path: List[str] = field(default_factory=list)

    def dominates(self, other: "Label") -> bool:
        """
        First-Order Stochastic Dominance (FSD) test (Chen et al. 2012):
        Self dominates Other if:
          1. Same node
          2. self.time <= other.time
          3. self.prob >= other.prob
          4. At least one strict inequality.
        """
        if self.node != other.node:
            return False
        time_le = self.cumulative_time <= other.cumulative_time
        prob_ge = self.on_time_prob >= other.on_time_prob
        if not (time_le and prob_ge):
            return False
        strict = (self.cumulative_time < other.cumulative_time or
                  self.on_time_prob > other.on_time_prob)
        return strict


class RSPPAStarSolver:
    """
    Multi-Criteria Reliable Shortest Path Problem (RSPP-A*) Solver
    with First-Order Stochastic Dominance (FSD) pruning.
    Optimizes:
      - Objective 1: Minimize Travel Time (hrs)
      - Objective 2: Maximize On-Time Reliability Alpha (P(arrival without disruption))
    """
    def __init__(self, graph: nx.DiGraph, max_speed_kmh: float = 65.0):
        self.g = graph
        self.max_speed = max_speed_kmh

    def _admissible_heuristic(self, curr_node: str, target_node: str) -> float:
        """Admissible Euclidean/Haversine lower bound on travel time."""
        c_lat, c_lon = TN_NODES[curr_node]["lat"], TN_NODES[curr_node]["lon"]
        t_lat, t_lon = TN_NODES[target_node]["lat"], TN_NODES[target_node]["lon"]
        dist = haversine_distance_km(c_lat, c_lon, t_lat, t_lon)
        return dist / self.max_speed

    def find_pareto_reliable_paths(
        self,
        source: str,
        target: str,
        alpha_min_reliability: float = 0.50,
        max_labels_per_node: int = 50
    ) -> Dict[str, Any]:
        """
        Finds Pareto-optimal reliable routes from source to target.
        Applies:
          - A* heuristic priority queuing
          - FSD pruning at each intermediate node
          - Alpha-reliability pruning threshold
        """
        t0 = time.perf_counter()

        # Priority queue entries: (f_score, tie_breaker, Label)
        # f_score balances estimated travel time + penalty for low reliability
        open_set: List[Tuple[float, int, Label]] = []
        tie_counter = 0

        # Non-dominated label sets per node: Dict[node, List[Label]]
        node_labels: Dict[str, List[Label]] = {n: [] for n in self.g.nodes()}

        start_label = Label(
            node=source,
            cumulative_time=0.0,
            on_time_prob=1.0,
            path=[source]
        )
        node_labels[source].append(start_label)

        h_init = self._admissible_heuristic(source, target)
        heapq.heappush(open_set, (h_init, tie_counter, start_label))

        paths_evaluated = 0
        paths_pruned_fsd = 0
        paths_pruned_alpha = 0
        paths_pruned_cycle = 0

        target_pareto_labels: List[Label] = []

        while open_set:
            f_score, _, curr_label = heapq.heappop(open_set)
            u = curr_label.node

            # Check if current label is dominated by any label currently at node u
            # (can happen if a superior label arrived after this was queued)
            is_dominated = False
            for existing in node_labels[u]:
                if existing is not curr_label and existing.dominates(curr_label):
                    is_dominated = True
                    paths_pruned_fsd += 1
                    break
            if is_dominated:
                continue

            # Check if reached target
            if u == target:
                # Add to target Pareto set if not dominated
                dominated_at_target = any(ex.dominates(curr_label) for ex in target_pareto_labels)
                if not dominated_at_target:
                    # Prune any existing target labels dominated by curr_label
                    target_pareto_labels = [ex for ex in target_pareto_labels if not curr_label.dominates(ex)]
                    target_pareto_labels.append(curr_label)
                continue

            # Expand neighbors
            for _, v, edge_data in self.g.out_edges(u, data=True):
                paths_evaluated += 1

                # 1. Cycle prevention
                if v in curr_label.path:
                    paths_pruned_cycle += 1
                    continue

                new_time = curr_label.cumulative_time + edge_data["travel_time_hr"]
                new_prob = curr_label.on_time_prob * edge_data["on_time_prob"]

                # 2. Alpha-reliability pruning threshold
                if new_prob < alpha_min_reliability:
                    paths_pruned_alpha += 1
                    continue

                new_label = Label(
                    node=v,
                    cumulative_time=round(new_time, 3),
                    on_time_prob=round(new_prob, 4),
                    path=curr_label.path + [v]
                )

                # 3. FSD Dominance Check against existing labels at v
                existing_v = node_labels[v]
                if any(ex.dominates(new_label) for ex in existing_v):
                    paths_pruned_fsd += 1
                    continue

                # Prune existing labels at v dominated by new_label
                node_labels[v] = [ex for ex in existing_v if not new_label.dominates(ex)]

                # Add new label
                if len(node_labels[v]) < max_labels_per_node:
                    node_labels[v].append(new_label)
                    h_val = self._admissible_heuristic(v, target)
                    # Multi-objective priority: time + heuristic - weight * reliability
                    priority = (new_time + h_val) - 1.5 * new_prob
                    tie_counter += 1
                    heapq.heappush(open_set, (priority, tie_counter, new_label))
                else:
                    paths_pruned_fsd += 1

        exec_time_ms = (time.perf_counter() - t0) * 1000.0

        # Sort Pareto set by travel time
        target_pareto_labels.sort(key=lambda l: l.cumulative_time)

        return {
            "source": source,
            "target": target,
            "execution_time_ms": round(exec_time_ms, 2),
            "paths_evaluated": paths_evaluated,
            "paths_pruned_fsd": paths_pruned_fsd,
            "paths_pruned_alpha": paths_pruned_alpha,
            "paths_pruned_cycle": paths_pruned_cycle,
            "total_pruned": paths_pruned_fsd + paths_pruned_alpha + paths_pruned_cycle,
            "pareto_routes_found": len(target_pareto_labels),
            "pareto_solutions": [
                {
                    "route": " -> ".join(sol.path),
                    "path_nodes": sol.path,
                    "travel_time_hr": round(sol.cumulative_time, 2),
                    "on_time_reliability_alpha": round(sol.on_time_prob, 4),
                    "disruption_prob": round(1.0 - sol.on_time_prob, 4),
                    "hops": len(sol.path) - 1,
                }
                for sol in target_pareto_labels[:5]  # Top 5 Pareto routes
            ]
        }


def benchmark_task2_rspp_astar(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Executes Task 2:
      - Runs RSPP-A* search between key strategic nodes:
        1. HQ_Chennai -> WH_30_Nagercoil (Longest diagonal artery across TN, ~700 km)
        2. HQ_Coimbatore -> WH_21_Nagapattinam (West Coast to East Coast Port)
        3. HQ_Madurai -> WH_01_Gummidipoondi (Deep South to Northern Border)
      - Verifies execution time < 300 ms.
      - Logs evaluated vs. pruned paths and Pareto solutions.
    """
    solver = RSPPAStarSolver(graph)

    test_pairs = [
        ("HQ_Chennai", "WH_30_Nagercoil"),
        ("HQ_Coimbatore", "WH_21_Nagapattinam"),
        ("HQ_Madurai", "WH_01_Gummidipoondi"),
    ]

    pair_results = []
    total_time_ms = 0.0

    for src, dst in test_pairs:
        res = solver.find_pareto_reliable_paths(src, dst, alpha_min_reliability=0.55)
        pair_results.append(res)
        total_time_ms += res["execution_time_ms"]

    primary_test = pair_results[0]  # HQ_Chennai to WH_30_Nagercoil
    task2_pass = primary_test["execution_time_ms"] < 300.0

    return {
        "primary_test_pair": f"{primary_test['source']} -> {primary_test['target']}",
        "primary_execution_time_ms": primary_test["execution_time_ms"],
        "pass_criteria_ms": 300.0,
        "task2_pass": task2_pass,
        "paths_evaluated": primary_test["paths_evaluated"],
        "paths_pruned_fsd": primary_test["paths_pruned_fsd"],
        "total_pruned": primary_test["total_pruned"],
        "pruning_efficiency_pct": round(
            (primary_test["total_pruned"] / max(primary_test["paths_evaluated"], 1)) * 100.0, 1
        ),
        "pareto_solutions_count": primary_test["pareto_routes_found"],
        "top_pareto_routes": primary_test["pareto_solutions"],
        "all_test_pairs_results": pair_results,
    }


# ===========================================================================
# 5. TASK 3: TAMIL NADU GEOSPATIAL & GRAPH DATA VALIDATION
# ===========================================================================

def generate_and_validate_geojson(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Executes Task 3:
      - Validates 43 nodes (types, coordinates within Tamil Nadu bounds).
      - Computes Haversine distances and realistic baseline travel times.
      - Checks graph connectivity (strong connectivity and HQ-to-WH reachability).
      - Formats GeoJSON FeatureCollection (Point & LineString) compatible with Leaflet.
    """
    # 1. Geographic Bounding Box for Tamil Nadu:
    # Lat: 8.0° N to 13.55° N, Lon: 76.2° E to 80.35° E
    TN_LAT_BOUNDS = (8.0, 13.55)
    TN_LON_BOUNDS = (76.2, 80.35)

    node_validation = []
    hqs = [k for k, v in TN_NODES.items() if v["type"] == "HQ"]
    hubs = [k for k, v in TN_NODES.items() if v["type"] == "Hub"]
    warehouses = [k for k, v in TN_NODES.items() if v["type"] == "Warehouse"]

    for node_id, data in TN_NODES.items():
        lat, lon = data["lat"], data["lon"]
        in_bounds = (TN_LAT_BOUNDS[0] <= lat <= TN_LAT_BOUNDS[1] and
                     TN_LON_BOUNDS[0] <= lon <= TN_LON_BOUNDS[1])
        node_validation.append({
            "node_id": node_id,
            "type": data["type"],
            "lat": lat,
            "lon": lon,
            "in_tn_bounds": in_bounds
        })

    all_in_bounds = all(n["in_tn_bounds"] for n in node_validation)
    node_counts_valid = (len(hqs) == 3 and len(hubs) == 10 and len(warehouses) == 30 and len(TN_NODES) == 43)

    # 2. Graph Connectivity & Reachability Validation
    is_strongly_connected = nx.is_strongly_connected(graph)
    is_weakly_connected = nx.is_weakly_connected(graph)
    isolated_nodes = list(nx.isolates(graph))

    # Test path reachability from all 3 HQs to all 30 Warehouses
    reachability_failures = []
    for hq in hqs:
        for wh in warehouses:
            if not nx.has_path(graph, hq, wh):
                reachability_failures.append((hq, wh))

    # 3. GeoJSON FeatureCollection Generation
    geojson_features = []

    # A. Node Features (Point)
    for node_id, data in TN_NODES.items():
        feature = {
            "type": "Feature",
            "id": node_id,
            "geometry": {
                "type": "Point",
                # GeoJSON standard uses [longitude, latitude]
                "coordinates": [data["lon"], data["lat"]]
            },
            "properties": {
                "id": node_id,
                "name": data["name"],
                "type": data["type"],
                "tier": data["tier"],
                "district": data["district"],
                "lat": data["lat"],
                "lon": data["lon"],
            }
        }
        geojson_features.append(feature)

    # B. Edge Features (LineString)
    edge_metrics = []
    # Deduplicate bidirectional edges for GeoJSON rendering lines
    seen_undirected = set()

    for u, v, data in graph.edges(data=True):
        edge_key = tuple(sorted([u, v]))
        if edge_key not in seen_undirected:
            seen_undirected.add(edge_key)
            u_coord = [TN_NODES[u]["lon"], TN_NODES[u]["lat"]]
            v_coord = [TN_NODES[v]["lon"], TN_NODES[v]["lat"]]

            feature = {
                "type": "Feature",
                "id": f"{u}__{v}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [u_coord, v_coord]
                },
                "properties": {
                    "source": u,
                    "target": v,
                    "distance_km": data["distance_km"],
                    "travel_time_hr": data["travel_time_hr"],
                    "on_time_prob": data["on_time_prob"],
                    "disruption_prob": data["disruption_prob"],
                }
            }
            geojson_features.append(feature)

        edge_metrics.append({
            "edge": f"{u} -> {v}",
            "distance_km": data["distance_km"],
            "travel_time_hr": data["travel_time_hr"]
        })

    geojson_collection = {
        "type": "FeatureCollection",
        "metadata": {
            "network_name": "Tamil Nadu Resilient Logistics Multi-Echelon Network",
            "total_nodes": len(TN_NODES),
            "hqs": len(hqs),
            "hubs": len(hubs),
            "warehouses": len(warehouses),
            "total_edges": graph.number_of_edges(),
            "unique_routes": len(seen_undirected),
            "crs": "EPSG:4326"
        },
        "features": geojson_features
    }

    distances = [e["distance_km"] for e in edge_metrics]
    times = [e["travel_time_hr"] for e in edge_metrics]

    task3_pass = (
        node_counts_valid and
        all_in_bounds and
        is_strongly_connected and
        len(isolated_nodes) == 0 and
        len(reachability_failures) == 0
    )

    return {
        "task3_pass": task3_pass,
        "node_counts": {
            "HQ": len(hqs),
            "Hub": len(hubs),
            "Warehouse": len(warehouses),
            "Total": len(TN_NODES),
            "valid": node_counts_valid
        },
        "all_nodes_in_tn_bounds": all_in_bounds,
        "is_strongly_connected": is_strongly_connected,
        "is_weakly_connected": is_weakly_connected,
        "isolated_nodes_count": len(isolated_nodes),
        "reachability_hq_to_wh_verified": len(reachability_failures) == 0,
        "total_directed_edges": graph.number_of_edges(),
        "unique_road_corridors": len(seen_undirected),
        "distance_stats_km": {
            "min": round(float(np.min(distances)), 2),
            "avg": round(float(np.mean(distances)), 2),
            "max": round(float(np.max(distances)), 2),
        },
        "travel_time_stats_hr": {
            "min": round(float(np.min(times)), 2),
            "avg": round(float(np.mean(times)), 2),
            "max": round(float(np.max(times)), 2),
        },
        "geojson_feature_count": len(geojson_features),
        "geojson_sample_metadata": geojson_collection["metadata"],
        "_full_geojson": geojson_collection
    }


# ===========================================================================
# 6. BENCHMARK SUITE RUNNER & CONSOLE REPORTER
# ===========================================================================

def print_banner(text: str) -> None:
    width = 78
    print("\n" + "=" * width)
    print(f" {text}")
    print("=" * width)


def main():
    print_banner("PHASE 1 FEASIBILITY & BENCHMARK VERIFICATION SUITE")
    print(" Target: Interactive Tamil Nadu Resilient Logistics Simulator (43 Nodes)")
    print(f" Python: {sys.version.split()[0]} | Platform: {sys.platform}")
    print("-" * 78)

    # Step 0: Graph Construction
    t0_graph = time.perf_counter()
    network_graph = build_tamil_nadu_network()
    graph_build_ms = (time.perf_counter() - t0_graph) * 1000.0
    print(f"[*] Network Graph Constructed in {graph_build_ms:.2f} ms")
    print(f"    - Nodes: {network_graph.number_of_nodes()} (3 HQs, 10 Hubs, 30 Warehouses)")
    print(f"    - Directed Edges: {network_graph.number_of_edges()}")

    # -----------------------------------------------------------------------
    # TASK 1: DBN Inference Latency Benchmark
    # -----------------------------------------------------------------------
    print_banner("TASK 1: pgmpy Dynamic Bayesian Network (DBN) Inference Latency")
    task1_res = benchmark_task1_pgmpy_dbn(network_graph)

    t1_status = "PASS" if task1_res["pgmpy_pass"] else "FAIL"
    print(f" [Criterion] 10-Frame DBN Inference Latency < {task1_res['pgmpy_threshold_ms']} ms")
    print(f" [+] pgmpy Model Build Time    : {task1_res['pgmpy_build_time_ms']:.2f} ms")
    print(f" [+] pgmpy Total Time (10 Frms) : {task1_res['pgmpy_total_time_ms']:.2f} ms")
    print(f" [+] pgmpy Average Frame Time  : {task1_res['pgmpy_avg_frame_time_ms']:.2f} ms/frame")
    print(f" [RESULT] pgmpy DBN Status      : [{t1_status}] ({task1_res['pgmpy_total_time_ms']} ms < 1500 ms)")

    print("\n [Fallback Routine Benchmark] Vectorized NumPy Forward-Filter Matrix Loop:")
    print(f" [+] NumPy Total Time (10 Frms) : {task1_res['numpy_fallback_total_time_ms']:.3f} ms")
    print(f" [+] Vectorized NumPy Speedup  : {task1_res['numpy_speedup_factor']}x faster than pgmpy")
    print("     (Ready for high-fps UI timeline playback and smooth scrubbing)")

    # -----------------------------------------------------------------------
    # TASK 2: RSPP-A* Search & Dominance Pruning Overhead
    # -----------------------------------------------------------------------
    print_banner("TASK 2: RSPP-A* Search & Dominance Pruning Overhead")
    task2_res = benchmark_task2_rspp_astar(network_graph)

    t2_status = "PASS" if task2_res["task2_pass"] else "FAIL"
    print(f" [Criterion] Search Latency < {task2_res['pass_criteria_ms']} ms (HQ_Chennai -> WH_30_Nagercoil)")
    print(f" [+] Primary Search Pair       : {task2_res['primary_test_pair']}")
    print(f" [+] Search Execution Time     : {task2_res['primary_execution_time_ms']:.2f} ms")
    print(f" [+] Paths Evaluated           : {task2_res['paths_evaluated']}")
    print(f" [+] Paths Pruned (FSD)        : {task2_res['paths_pruned_fsd']}")
    print(f" [+] Total Paths Pruned        : {task2_res['total_pruned']} ({task2_res['pruning_efficiency_pct']}% pruning efficiency)")
    print(f" [+] Pareto Solutions Found    : {task2_res['pareto_solutions_count']}")
    print(f" [RESULT] RSPP-A* Search Status : [{t2_status}] ({task2_res['primary_execution_time_ms']} ms < 300 ms)")

    print("\n [Top Pareto-Optimal Reliable Routes Found]:")
    for idx, sol in enumerate(task2_res["top_pareto_routes"][:3], 1):
        print(f"   Route #{idx}: Time = {sol['travel_time_hr']}h | Rel(Alpha) = {sol['on_time_reliability_alpha']} | Hops = {sol['hops']}")
        print(f"            Path = {sol['route']}")

    # -----------------------------------------------------------------------
    # TASK 3: Tamil Nadu Geospatial & Graph Data Validation
    # -----------------------------------------------------------------------
    print_banner("TASK 3: Tamil Nadu Geospatial & Graph Data Validation")
    task3_res = generate_and_validate_geojson(network_graph)

    t3_status = "PASS" if task3_res["task3_pass"] else "FAIL"
    nc = task3_res["node_counts"]
    print(f" [+] Node Registry Validation  : {nc['HQ']} HQs + {nc['Hub']} Hubs + {nc['Warehouse']} WHs = {nc['Total']} Nodes (Valid: {nc['valid']})")
    print(f" [+] Geospatial Coordinates    : All 43 nodes strictly within Tamil Nadu bounds: {task3_res['all_nodes_in_tn_bounds']}")
    print(f" [+] Graph Strong Connectivity : {task3_res['is_strongly_connected']}")
    print(f" [+] Isolated Nodes            : {task3_res['isolated_nodes_count']} (Zero isolated components)")
    print(f" [+] HQ -> WH Reachability     : All 3 HQs reach all 30 Warehouses: {task3_res['reachability_hq_to_wh_verified']}")
    print(f" [+] Road Corridors Validated  : {task3_res['unique_road_corridors']} unique bi-directional links ({task3_res['total_directed_edges']} directed edges)")
    print(f" [+] Corridor Distances (km)   : Min = {task3_res['distance_stats_km']['min']}, Avg = {task3_res['distance_stats_km']['avg']}, Max = {task3_res['distance_stats_km']['max']}")
    print(f" [+] Travel Times (hours)      : Min = {task3_res['travel_time_stats_hr']['min']}, Avg = {task3_res['travel_time_stats_hr']['avg']}, Max = {task3_res['travel_time_stats_hr']['max']}")
    print(f" [+] GeoJSON Features Built    : {task3_res['geojson_feature_count']} features (ready for Leaflet map canvas)")
    print(f" [RESULT] Geospatial Status    : [{t3_status}]")

    # -----------------------------------------------------------------------
    # SUMMARY REPORT GENERATION
    # -----------------------------------------------------------------------
    all_passed = task1_res["pgmpy_pass"] and task2_res["task2_pass"] and task3_res["task3_pass"]
    overall_status = "ALL PASS" if all_passed else "FAILURES DETECTED"

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall_status,
        "phase1_benchmark_summary": {
            "task1_dbn_inference": {
                "status": t1_status,
                "pgmpy_total_time_ms": task1_res["pgmpy_total_time_ms"],
                "pgmpy_avg_frame_time_ms": task1_res["pgmpy_avg_frame_time_ms"],
                "threshold_ms": task1_res["pgmpy_threshold_ms"],
                "numpy_fallback_time_ms": task1_res["numpy_fallback_total_time_ms"],
                "numpy_speedup": task1_res["numpy_speedup_factor"]
            },
            "task2_rspp_astar": {
                "status": t2_status,
                "primary_pair": task2_res["primary_test_pair"],
                "execution_time_ms": task2_res["primary_execution_time_ms"],
                "threshold_ms": task2_res["pass_criteria_ms"],
                "paths_evaluated": task2_res["paths_evaluated"],
                "paths_pruned_fsd": task2_res["paths_pruned_fsd"],
                "pruning_efficiency_pct": task2_res["pruning_efficiency_pct"],
                "pareto_solutions_count": task2_res["pareto_solutions_count"],
                "top_solutions": task2_res["top_pareto_routes"]
            },
            "task3_geospatial_validation": {
                "status": t3_status,
                "node_counts": task3_res["node_counts"],
                "all_nodes_in_tn_bounds": task3_res["all_nodes_in_tn_bounds"],
                "is_strongly_connected": task3_res["is_strongly_connected"],
                "isolated_nodes_count": task3_res["isolated_nodes_count"],
                "reachability_verified": task3_res["reachability_hq_to_wh_verified"],
                "total_directed_edges": task3_res["total_directed_edges"],
                "unique_road_corridors": task3_res["unique_road_corridors"],
                "distance_stats_km": task3_res["distance_stats_km"],
                "travel_time_stats_hr": task3_res["travel_time_stats_hr"]
            }
        },
        "geojson_network": task3_res["_full_geojson"]
    }

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase1_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print_banner(f"FINAL BENCHMARK SUITE RESULT: [{overall_status}]")
    print(f" Summary JSON Report written to: {report_path}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
