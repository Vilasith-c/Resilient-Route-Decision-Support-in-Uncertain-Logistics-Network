# ProbRoute

### Probabilistic Route Resilience for Uncertain Logistics Networks

ProbRoute is an uncertainty-aware logistics decision-support framework that evaluates delivery routes under changing operational conditions and recommends resilient alternatives using probabilistic reasoning.

---

## Overview

Logistics networks operate under uncertainty caused by factors such as traffic congestion, weather conditions, demand fluctuations, vehicle conditions, and operational disruptions. Traditional routing approaches primarily rely on fixed attributes such as distance or travel time and may therefore select routes that are efficient under normal conditions but unreliable when real-world conditions change.

ProbRoute addresses this limitation by combining a data-driven probabilistic reasoning layer with a physical logistics network. The system uses historical delivery data to model uncertainty, performs probabilistic inference when new evidence is observed, maps the resulting risk onto a logistics network containing 20 or more physical nodes, evaluates candidate routes, and recommends the route with the highest resilience under the current conditions.

---

## Problem Statement

Logistics networks operate under uncertainty due to factors such as traffic congestion, weather conditions, demand fluctuations, and operational disruptions. Traditional routing methods often rely on fixed conditions and may therefore select routes that are efficient in normal situations but unreliable under changing conditions. This project addresses the need to evaluate logistics routes probabilistically by considering uncertainty, delivery risk, and route reliability to support resilient logistics decisions.

---

## Project Objective

The objective of ProbRoute is to develop a probabilistic logistics decision-support system that:

- Models uncertainty affecting delivery operations.
- Learns relationships between logistics conditions and delivery outcomes from historical data.
- Performs probabilistic inference based on observed evidence.
- Represents a logistics infrastructure using a network of 20 or more physical nodes.
- Maps inferred risks onto logistics hubs and transportation connections.
- Evaluates candidate routes based on reliability and disruption exposure.
- Identifies vulnerable hubs and high-risk connections.
- Recommends the most resilient route under the current uncertain conditions.

---

# System Architecture at a Glance

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMAZON DELIVERY DATASET                             │
│                                                                             │
│  Weather | Traffic | Vehicle Condition | Multiple Deliveries | Festival    │
│  Location | Distance | Delivery Time                                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA PROCESSING LAYER                               │
│                                                                             │
│  Data Cleaning                                                              │
│  Feature Engineering                                                        │
│  Distance Calculation                                                       │
│  Variable Discretization                                                    │
│  Delivery Outcome Preparation                                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROBABILISTIC MODELING LAYER                             │
│                                                                             │
│                        PRIMARY MODEL:                                       │
│                         BAYESIAN NETWORK                                    │
│                                                                             │
│       Weather ───────┐                                                      │
│       Traffic ───────┤                                                      │
│       Vehicle ───────┼──────► Delivery Risk ──────► Delivery Outcome       │
│       Festival ──────┤                                                      │
│       Delivery Load ─┤                                                      │
│       Distance ──────┘                                                      │
│                                                                             │
│  Models probabilistic dependencies between uncertain logistics variables    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROBABILISTIC INFERENCE LAYER                           │
│                                                                             │
│                         CURRENT EVIDENCE                                    │
│                                                                             │
│          Weather | Traffic | Festival | Vehicle | Delivery Load             │
│                                   │                                         │
│                                   ▼                                         │
│                         BELIEF UPDATING                                     │
│                                   │                                         │
│                  ┌────────────────┴────────────────┐                        │
│                  ▼                                 ▼                        │
│           Delay Probability              On-Time Probability                │
│                                                                             │
│           Operational Risk               Congestion Risk                     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Probabilistic Risk Mapping
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHYSICAL LOGISTICS NETWORK LAYER                         │
│                                                                             │
│                       20+ PHYSICAL NODES                                    │
│                                                                             │
│        Warehouse → Regional Hubs → Transit Hubs → Delivery Zones            │
│                                                                             │
│              [Warehouse]                                                    │
│                   │                                                         │
│          ┌────────┼────────┐                                                │
│          ▼        ▼        ▼                                                │
│        [RH1]    [RH2]    [RH3]                                              │
│          │ \      │      / │                                                │
│          │  \     │     /  │                                                │
│        [TH1]───[TH2]───[TH3]                                                │
│          │       │       │                                                  │
│        [TH4]───[TH5]───[TH6]                                                │
│          │       │       │                                                  │
│        [TH7]───[TH8]───[TH9]                                                │
│          │       │       │                                                  │
│        [LH1]────[LH2]────[LH3]                                             │
│          │       │       │                                                  │
│        [DZ1]    [DZ2]    [DZ3]                                              │
│                                                                             │
│  Nodes = Physical logistics locations                                       │
│  Edges = Transportation connections                                         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK PROPAGATION LAYER                              │
│                                                                             │
│     Probabilistic Inference Results                                         │
│                    │                                                        │
│                    ▼                                                        │
│     Update Hub Risk and Edge Risk                                           │
│                    │                                                        │
│                    ▼                                                        │
│     Identify High-Risk Connections and Vulnerable Hubs                      │
│                    │                                                        │
│                    ▼                                                        │
│     Evaluate Risk Exposure Across Candidate Routes                          │
│                                                                             │
│  Example:                                                                   │
│  Weather Change → Traffic Risk → Hub Congestion → Route Delay Risk          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ROUTE RESILIENCE AND DECISION LAYER                       │
│                                                                             │
│              Route A        Route B        Route C                          │
│                 │              │              │                             │
│                 ▼              ▼              ▼                             │
│          Evaluate Risk   Evaluate Risk   Evaluate Risk                      │
│          Evaluate Time   Evaluate Time   Evaluate Time                      │
│          Evaluate        Evaluate        Evaluate                           │
│          Reliability     Reliability     Reliability                        │
│                 │              │              │                             │
│                 └──────────────┼──────────────┘                             │
│                                ▼                                            │
│                    COMPARE CANDIDATE ROUTES                                 │
│                                │                                            │
│                                ▼                                            │
│                   SELECT MOST RESILIENT ROUTE                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FINAL OUTPUT                                   │
│                                                                             │
│  Recommended Resilient Route                                                │
│  Route-Level Delay Probability                                              │
│  On-Time Delivery Probability                                               │
│  Route Reliability Score                                                    │
│  Vulnerable Hubs                                                            │
│  High-Risk Transportation Connections                                       │
│  Explanation of the Route Recommendation                                    │
└─────────────────────────────────────────────────────────────────────────────┘
