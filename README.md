# TERRA — Planetary Digital Twin

> **An experimental 3D Earth-system digital twin interface connecting observations, physics, simulation and artificial intelligence.**

![TERRA](https://img.shields.io/badge/TERRA-Earth--System%20Digital%20Twin-63d9ff)
![Status](https://img.shields.io/badge/status-prototype-orange)
![3D](https://img.shields.io/badge/3D-Three.js-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

TERRA is an experimental software platform exploring the concept of a planetary digital twin.

The central idea is to represent Earth as a connected system rather than as a collection of isolated scientific models.

TERRA is designed around the convergence of:

- Earth observations
- Satellite observations
- Numerical physics models
- Reanalysis datasets
- Earth-system simulations
- Artificial intelligence
- Data assimilation
- Uncertainty analysis
- Interactive 3D visualisation

The current version is a **3D software prototype**.

It is not yet a complete scientific digital twin and does not currently produce operational scientific forecasts.

---

# Current Version

## TERRA v2 — Interactive 3D Prototype

The current version introduces an interactive three-dimensional Earth environment.

The previous version used a conceptual 2D/SVG representation of the Earth system.

TERRA v2 replaces that representation with a WebGL-based 3D Earth.

### Current capabilities

- Interactive 3D Earth
- Earth rotation
- Camera orbit controls
- Zoom
- Satellite objects
- Atmospheric shell
- Observation points
- Wind-particle visualisation
- Ocean layer
- Star field
- Sun/light source
- Earth-system HUD
- Observation-layer controls
- Scenario console
- Model comparison interface
- AI analysis interface
- Temporal slider
- Responsive interface
- Reduced-motion accessibility support

---

# Architecture

The long-term TERRA architecture is designed around five major layers.

```text
                         TERRA
                           │
                           ▼
                 ┌───────────────────┐
                 │   3D INTERFACE    │
                 │    Earth State    │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │   EARTH STATE     │
                 │   DATA LAYER      │
                 └─────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Observations    Reanalysis     Models
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ DATA ASSIMILATION │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ AI / INTELLIGENCE │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ SCENARIO ENGINE   │
                 └───────────────────┘