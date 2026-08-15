# DEMO/PLACEHOLDER DATA — AGRA
## ⚠️ THIS IS FABRICATED TEST DATA — NOT REAL CHAITRA OUTPUT
## Used only to test whether the LLM prompt structure produces a usable HAP draft.
## Real data will be computed directly from CHAITRA's source code (we have the full script).
## Ward values are invented, but all derived quantities (shelters, saplings, costs)
## now follow CHAITRA's actual formulas and constants (RESOURCE_CONFIG in the source code).

City: Agra
Total Wards: 100 (placeholder count)
City Population: ~2,000,000 (placeholder)

---

### Ward 14 — "Kamla Nagar area" (placeholder name)
- Population: 28,500
- Composite Heat Risk Index: 78.3 (High Risk — top 30%)
- Surface Temp Deviation (daytime): +2.9°C from city average
- Nighttime Heat Zone Score: 71.2 (High Risk)
- Housing Vulnerability: Dense (82nd percentile) — low-rise, low vegetation, high building density
- Land Use: 8% vegetation, 71% built-up, 0% water
- Cool Roof Priority Score: 84.1 (High Priority)
  - Dark roof area needing treatment: 12.4 hectares
  - Estimated coating cost: ₹150-230/m² → ₹1.86–2.85 crore total
- Tree Planting Priority Score: 76.5 (High Priority)
  - Canopy deficit: 12% (target 20%, current 8%) → deficit area 6.2 hectares
  - Plantable area: 1.24 hectares (20% of deficit area — dense ward)
  - Saplings needed: 744 (400/plantable hectare × 1.5 mortality buffer)
  - Estimated cost: ₹5.6 lakh (₹750/tree: sapling + planting labor + 3-yr maintenance)

### Ward 31 — "Shahganj area" (placeholder name)
- Population: 41,200
- Composite Heat Risk Index: 85.7 (High Risk — top 10%)
- Surface Temp Deviation (daytime): +3.4°C from city average
- Nighttime Heat Zone Score: 79.8 (High Risk — commercial/market zone)
- Housing Vulnerability: Very Dense (94th percentile)
- Land Use: 4% vegetation, 81% built-up, 0% water
- Cool Roof Priority Score: 91.2 (High Priority)
  - Dark roof area needing treatment: 18.9 hectares
  - Estimated coating cost: ₹2.83–4.35 crore total
- Tree Planting Priority Score: 88.0 (High Priority)
  - Canopy deficit: 16% → deficit area 9.1 hectares
  - Plantable area: 1.82 hectares (20% of deficit area — very dense ward)
  - Saplings needed: 1,092 (400/plantable hectare × 1.5 mortality buffer)
  - Estimated cost: ₹8.2 lakh (₹750/tree)

### Ward 52 — "Taj Ganj area" (placeholder name)
- Population: 19,800
- Composite Heat Risk Index: 45.2 (Medium Risk)
- Surface Temp Deviation (daytime): +0.8°C from city average
- Nighttime Heat Zone Score: 38.6 (Low-Medium Risk)
- Housing Vulnerability: Moderate (58th percentile)
- Land Use: 22% vegetation, 55% built-up, 3% water
- Cool Roof Priority Score: 41.0 (Medium Priority)
- Tree Planting Priority Score: 35.2 (Low-Medium Priority — canopy already near target)

### Ward 67 — "Riverside area" (placeholder name)
- Population: 12,400
- Composite Heat Risk Index: 22.1 (Low Risk)
- Surface Temp Deviation (daytime): -1.8°C from city average
- Nighttime Heat Zone Score: 19.4 (Low Risk)
- Housing Vulnerability: Sparse (30th percentile)
- Land Use: 38% vegetation, 30% built-up, 15% water
- Cool Roof Priority Score: 15.6 (Low Priority)
- Tree Planting Priority Score: 12.0 (Low Priority — canopy already adequate)

---

### City-Wide Resource Summary (placeholder)
- Cooling shelters needed (1 per 15K population in high-risk wards, rounded up per ward): 5 (Ward 14: 2, Ward 31: 3)
- Total estimated cool roof investment (high-risk wards only): ₹4.70–7.20 crore
- Total estimated tree planting investment (high-risk wards only): ₹13.8 lakh
- Total saplings needed (high-risk wards only): 1,836
