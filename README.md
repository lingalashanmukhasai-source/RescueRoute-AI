# 🛡️ RescueRoute AI

### AI-Assisted Disaster-Safe Navigation Platform

RescueRoute AI is an intelligent disaster-aware navigation platform designed to help people make safer travel decisions during emergencies.

Unlike conventional navigation systems that primarily focus on distance and travel time, RescueRoute AI combines environmental conditions, disaster awareness, route intelligence, and nearby emergency facilities to generate an explainable safety assessment.

---

## 🚨 Problem

During floods, cyclones, earthquakes, wildfires, landslides, and extreme weather events, the fastest route is not always the safest route.

People may not know:

- Which routes are safer
- Whether environmental conditions are worsening
- Where nearby hospitals or shelters are located
- How disaster conditions can affect their journey
- Which route provides better access to emergency services

Existing navigation systems generally prioritize travel time and distance rather than disaster-specific safety.

---

## 💡 Solution

RescueRoute AI provides an AI-assisted safety layer on top of navigation.

The platform:

1. Detects the user's location
2. Accepts a destination
3. Identifies the selected disaster condition
4. Retrieves live environmental information
5. Checks disaster-awareness data
6. Calculates an explainable risk score
7. Generates a safety score
8. Provides route information
9. Displays nearby emergency facilities
10. Gives disaster-specific recommendations

---

## 🧠 Key Features

### 🗺️ Disaster-Aware Routing
Provides route information while considering disaster-related risk factors.

### 🤖 Explainable AI Risk Engine
Generates a risk score based on environmental and disaster-specific signals.

### 🌦️ Live Weather Intelligence
Uses current temperature, rainfall, wind, gusts, humidity, and visibility information.

### 🌍 Earthquake Awareness
Uses recent earthquake information to identify nearby seismic activity.

### 🚨 Disaster Awareness
Integrates disaster-event information from GDACS.

### 🏥 Emergency Facilities
Displays nearby:

- Hospitals
- Clinics
- Police stations
- Fire stations
- Shelters
- Ambulance stations

### 📍 GPS Location
Allows users to use their current location.

### 🧭 Route Intelligence
Provides route distance and estimated travel time.

### 👤 User Accounts
Users can create accounts and save previous risk analyses.

### 🚑 Emergency Mode
Provides quick access to location and emergency-facility information.

---

## 🏗️ System Architecture

```text
                 USER
                   │
                   ▼
        Location + Destination
                   │
                   ▼
        ┌─────────────────────┐
        │  RescueRoute AI     │
        │    Risk Engine      │
        └─────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Weather      Disaster     Routing
   Data         Data         Data
       │           │           │
       └───────────┼───────────┘
                   ▼
             Risk Analysis
                   │
          ┌────────┴────────┐
          ▼                 ▼
      Risk Score        Safety Score
          │                 │
          └────────┬────────┘
                   ▼
             Safer Route
                   │
                   ▼
        Emergency Facilities
