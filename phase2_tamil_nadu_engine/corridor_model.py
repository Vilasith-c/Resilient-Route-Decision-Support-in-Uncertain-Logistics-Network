"""
corridor_model.py — Pipeline Stage 2: Path-Centric Uncertainty Modeling
========================================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Technique: Adapted SPOTAR / PACE path-centric dependency model (Andonov & Yang; PRD 1 §3.2, PRD 5 §4)

Academic Context (Con-Fix #1):
  - Chen et al. (2012) assumed link delays are mutually independent.
  - Under real disruptions (cyclones, monsoon floods, regional strikes), adjacent
    links in the same transportation artery experience correlated shocks.
  - Implementation Scope & Precision Note:
    This is an adapted, lightweight operationalization of the path-centric dependency
    concept from SPOTAR/PACE (Andonov & Yang), using structural highway grouping and a
    convex-combination blended exposure formulation:
        exp_correlated = max(exp_edge, 0.70 * exp_edge + 0.30 * exp_macro)
    rather than a full joint distribution learned from empirical GPS trajectory logs.
    This demonstrates the removal of Chen et al.'s edge-independence assumption
    within the computational budget of an interactive simulator.

National Highway Verification (Post-2010 MoRTH Renumbering):
  - NH 48  : Delhi-Chennai corridor (Hosur - Krishnagiri - Vellore - Sriperumbudur - Chennai)
  - NH 44  : North-South trunk (Salem - Namakkal - Dindigul - Madurai - Tirunelveli - Kanyakumari)
  - NH 544 : Western Industrial corridor (Salem - Erode - Tiruppur - Coimbatore; formerly NH 47)
  - NH 32  : East Coast Road / Coastal corridor (Chennai - Cuddalore - Chidambaram - Nagapattinam)
  - NH 38  : Central-South Port trunk (Vellore - Trichy - Madurai - Thoothukudi)
  - NH 83  : Transverse agricultural connector (Coimbatore - Pollachi - Dindigul - Thanjavur)
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import networkx as nx

# ---------------------------------------------------------------------------
# 8 Strategic Logistics Arteries (Macro Corridors) of Tamil Nadu
# ---------------------------------------------------------------------------
TAMIL_NADU_CORRIDORS: Dict[str, Dict[str, Any]] = {
    "corridor_nh48_northern_industrial": {
        "name": "NH48 Northern Industrial Corridor",
        "description": "Chennai - Tiruvallur - Sriperumbudur - Arakkonam - Vellore - Ranipet",
        "base_risk": "Medium",
        "skewnorm_params": {"a": 4.5, "loc": 12.0, "scale": 9.0},
    },
    "corridor_nh44_central_artery": {
        "name": "NH44 North-South Central Spine",
        "description": "Vellore - Ambur - Tirupattur - Salem - Namakkal - Dindigul - Madurai",
        "base_risk": "Low",
        "skewnorm_params": {"a": 3.8, "loc": 10.0, "scale": 7.5},
    },
    "corridor_nh544_western_industrial": {
        "name": "NH544 Western Industrial Corridor",
        "description": "Salem - Mettur - Erode - Bhavani - Perundurai - Tiruppur - Coimbatore",
        "base_risk": "Low",
        "skewnorm_params": {"a": 3.5, "loc": 9.0, "scale": 7.0},
    },
    "corridor_nh32_east_coast": {
        "name": "NH32 / ECR East Coast Maritime Corridor",
        "description": "Chennai - Cuddalore - Villupuram - Panruti - Chidambaram - Nagapattinam",
        "base_risk": "High",  # Prone to coastal cyclones and northeast monsoon inundation
        "skewnorm_params": {"a": 6.5, "loc": 18.0, "scale": 14.0},
    },
    "corridor_cauvery_delta_agri": {
        "name": "Cauvery Delta Agricultural Corridor",
        "description": "Tiruchirappalli - Thanjavur - Kumbakonam - Mayiladuthurai",
        "base_risk": "Medium",
        "skewnorm_params": {"a": 4.2, "loc": 11.0, "scale": 8.5},
    },
    "corridor_nh44_southern_trunk": {
        "name": "NH44 Deep South Freight Trunk",
        "description": "Madurai - Virudhunagar - Kovilpatti - Tirunelveli - Nagercoil",
        "base_risk": "Low",
        "skewnorm_params": {"a": 3.6, "loc": 10.0, "scale": 7.0},
    },
    "corridor_maritime_express": {
        "name": "Thoothukudi Port Maritime Link",
        "description": "Composite freight corridor connecting Tiruchirappalli to Thoothukudi port, encompassing NH 38/138 and regional arterial connectors",
        "base_risk": "Medium",
        "skewnorm_params": {"a": 4.8, "loc": 13.0, "scale": 9.5},
    },
    "corridor_western_ghats_agri": {
        "name": "Western Ghats Agricultural & Hill Foothill Corridor",
        "description": "Coimbatore - Pollachi - Udumalaipettai - Palani - Batlagundu - Tenkasi",
        "base_risk": "Medium",  # Prone to landslides and heavy rain
        "skewnorm_params": {"a": 5.2, "loc": 14.0, "scale": 10.5},
    },
}


def assign_edges_to_corridors(graph: nx.DiGraph) -> Dict[str, List[Tuple[str, str]]]:
    """
    Maps all graph edges to their primary macro corridor based on geographical
    and arterial topology. Sets the 'corridor_id' attribute on each edge in G.
    """
    corridor_membership: Dict[str, List[Tuple[str, str]]] = {
        cid: [] for cid in TAMIL_NADU_CORRIDORS.keys()
    }

    def match_corridor(u: str, v: str) -> str:
        nodes = {u, v}

        # 1. Northern Industrial (NH48)
        if nodes.intersection({"HQ_Chennai", "Hub_Tiruvallur", "WH_01_Gummidipoondi", "WH_02_Sriperumbudur", "WH_03_Arakkonam"}):
            if not nodes.intersection({"Hub_Cuddalore", "WH_24_Villupuram"}):
                return "corridor_nh48_northern_industrial"
        if nodes.issubset({"Hub_Tiruvallur", "Hub_Vellore", "WH_04_Ranipet", "WH_03_Arakkonam"}):
            return "corridor_nh48_northern_industrial"

        # 2. East Coast (NH32)
        if nodes.intersection({"Hub_Cuddalore", "WH_22_Panruti", "WH_23_Chidambaram", "WH_24_Villupuram", "WH_21_Nagapattinam"}):
            return "corridor_nh32_east_coast"
        if ("HQ_Chennai", "Hub_Cuddalore") == (u, v) or ("Hub_Cuddalore", "HQ_Chennai") == (u, v):
            return "corridor_nh32_east_coast"

        # 3. Western Industrial (NH544)
        if nodes.intersection({"Hub_Erode", "WH_10_Bhavani", "WH_11_Perundurai", "WH_12_Tiruppur", "WH_08_Mettur"}):
            return "corridor_nh544_western_industrial"
        if nodes.issubset({"HQ_Coimbatore", "Hub_Erode"}) or nodes.issubset({"Hub_Salem", "Hub_Erode"}):
            return "corridor_nh544_western_industrial"

        # 4. Western Ghats
        if nodes.intersection({"WH_13_Pollachi", "WH_14_Udumalaipettai", "WH_15_Mettupalayam", "WH_25_Palani", "WH_26_Batlagundu", "WH_29_Tenkasi"}):
            return "corridor_western_ghats_agri"

        # 5. Cauvery Delta
        if nodes.intersection({"Hub_Thanjavur", "WH_19_Kumbakonam", "WH_20_Mayiladuthurai", "WH_18_Pudukkottai"}):
            return "corridor_cauvery_delta_agri"

        # 6. Maritime Express (Thoothukudi)
        if nodes.intersection({"Hub_Thoothukudi", "Hub_Tuticorin"}):
            return "corridor_maritime_express"

        # 7. Southern Trunk (NH44 South)
        if nodes.intersection({"Hub_Tirunelveli", "WH_27_Virudhunagar", "WH_28_Kovilpatti", "WH_30_Nagercoil"}):
            return "corridor_nh44_southern_trunk"

        # 8. Central Artery (NH44 Central Spine)
        return "corridor_nh44_central_artery"

    for u, v, data in graph.edges(data=True):
        cid = match_corridor(u, v)
        data["corridor_id"] = cid
        data["corridor_name"] = TAMIL_NADU_CORRIDORS[cid]["name"]
        corridor_membership[cid].append((u, v))

    return corridor_membership
