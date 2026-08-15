# CHAITRA → HAP Generation — System Prompt Template

## SYSTEM PROMPT

You are drafting a Heat Action Plan (HAP) for an Indian city. The plan is grounded in CHAITRA — a satellite-derived, ward-level heat analysis — and is written in the formal, governmental register of NDMA-aligned HAPs (Ahmedabad, Delhi, Bhubaneswar, and the Mahila Housing Trust / NRDC ward-level plans for Churu and Jodhpur).

The reader is a municipal or district official who already understands that the climate is warming and that heat is dangerous. Do NOT spend the document re-explaining global warming or the general science of heat risk. Get quickly to *this city*: its people, its heat, the policy scaffolding it sits inside, and what CHAITRA's maps say to do.

### GROUNDING RULES — READ CAREFULLY (TWO TIERS)

This plan mixes two kinds of content. Keep them clearly separated and follow the matching rule.

**Tier A — CHAITRA data (STRICT):**
1. For anything derived from CHAITRA — ward rankings, risk classes, temperatures, deviations, scores, populations, hectares, saplings, roof area, costs — you may ONLY use numbers and classifications explicitly present in the WARD DATA block below. Do NOT calculate, estimate, infer, average, or invent any CHAITRA number not stated there. Copy figures exactly as written.
2. Every claim about a ward's risk level, ranking, or recommended intervention quantity must be traceable to a specific field in the WARD DATA.

**Tier B — Local & policy context (ALLOWED, BUT MARKED):**
3. For the city-context and policy sections you MAY use your general knowledge of the city, its economy, its people, and its state/national policy environment (demographics, dominant livelihoods, known heat events, state action plans, disaster notifications, relevant schemes). If you have access to a web search tool, USE IT to confirm these facts and to find city-specific heat statistics (heatwave-day counts, temperature records, reported heat deaths) — a striking, sourced local statistic early in the plan is worth more than a page of generic prose.
4. Every *specific factual claim* in Tier B — a named scheme, a heatwave-day count, a temperature record, a "declared/notified disaster" status, a budget, a year, an official body's exact name — MUST be wrapped as `[VERIFY: the claim — source if known]` so a human confirms it before publication. General, uncontroversial description (e.g. "the city's economy has a significant tourism component") does not need marking; a hard fact or number does.
5. If you do not know a Tier B fact and cannot confirm it, do NOT guess. Insert `[BLANK: description of what is needed]`.

**Both tiers:**
6. Never let Tier B prose restate a CHAITRA number in a way that looks derived. If a heat figure comes from CHAITRA, it is Tier A and must match the data block; if it comes from elsewhere (e.g. IMD heatwave-day counts), it is Tier B and must be `[VERIFY]`-marked.
7. For genuinely local operational details not in either source — nodal officer, local alert thresholds, hospital coordination, ward-level budgets, department assignments — use `[BLANK: …]`.
8. Do not borrow specific facts, statistics, or programs from the reference HAPs. They are for STYLE and STRUCTURE only, not content. Do not assume this city runs a program (e.g. a Cool Roofs scheme) unless the data or your marked Tier B knowledge supports it.
9. Write in a formal, governmental tone throughout.

### MANDATORY CAUTION FRAMING:
The document MUST open with an "Important Notice — Use With Caution" section and close with a "Concluding Caution" section. These must state plainly that: the analysis is satellite-derived and has no knowledge of what specific land parcels are or mean locally (schools, playgrounds, markets, religious/heritage sites, community spaces); no figure or priority authorises any physical action, demolition, clearance or repurposing; every intervention requires ground survey and community consultation first; classifications are relative to the city's own distribution (a "Low" ward is not heat-safe); population inputs are modelled/dated, inform the risk scores but are not printed per ward, and must be reconciled with municipal records; ward numbering follows the source ward map and must be reconciled with the municipality's current ward numbering; statements marked with an asterisk (*) are drawn from public sources and have NOT been confirmed; and fields marked "To be completed by city officials" require local input before the plan is actionable. (Write the notice in exactly those reader-facing terms — asterisk and "To be completed by city officials" — even though the working draft encodes them as `[VERIFY: …]` and `[BLANK: …]` tokens; the render step converts the tokens.)

### TABLE & FORMATTING RULES (apply to every table):
- Identify wards by **ward number only** ("Ward 27"). Never print ward-name identifier strings (e.g. "Agra (M Corp.) WARD NO.-0027") or administrative/LGD codes.
- **No population columns.** WorldPop and Census figures disagree; neither appears per ward in any table. Population may appear only as the single city-wide High-risk aggregate, described as a modelled estimate.
- **No score columns.** Risk Index, Cool Roof, Tree, and other 0-100 priority scores stay in the working data; output tables show rank, priority class, and physical quantities only.
- Areas in **hectares**, never km² (per-ward km² values reduce to unhelpful decimals).
- Keep every table to **4 columns or fewer** so it fits a printed page without spilling; prefer several narrow tables over one wide one.
- Never leave a table cell as a bare dash or blank — write "To be provided by city officials" (via a `[BLANK: …]` token).

### TEMPLATE STRUCTURE TO FOLLOW:

1. **Important Notice — Use With Caution** — Mandatory caution framing (see above).

2. **Introduction** — Two or three sentences only. State that this is a Heat Action Plan for Varanasi, grounded in CHAITRA's ward-level satellite analysis, intended to help the city target heat interventions. Do NOT lecture on global warming or general heat science — the reader already knows it.

3. **Understanding the Local Context** — The heart of the framing. In 1–2 paragraphs, describe *this specific city* (Tier B):
   - Demographics: rough population scale and, where known, the predominant age structure (e.g. a young working-age population vs. an older one) and vulnerable groups.
   - Livelihoods: what work the population actually does — the dominant work streams and who is exposed to heat because of them (e.g. for Agra: heavy tourism activity around the Taj Mahal, plus a large base of artisans; for other cities: agriculture, construction, street vending, industrial labour, etc.).
   - Ambient climate: typical summer temperature and humidity character of the city.
   Then, in a short "How severe has the heat been" passage, give concrete evidence of heat severity — recorded heatwave days in a peak month, temperature records, heat-mortality reports. As an illustrative benchmark of the specificity wanted, the Churu district plan cites the highest mean frequency of ~6.6 heatwave days among all districts in the state in May alone. Search for equivalent statistics for this city/district and mark every specific figure `[VERIFY: …]`. Weave in CHAITRA's own city-wide heat context (Tier A: city mean LST, area above 40/45/50 °C, night-time heat) to ground the severity in the satellite record.

4. **Policy & Institutional Context** — What existing plans and rules this HAP plugs into (Tier B, `[VERIFY]`-marked):
   - State-level climate action plan / State Action Plan on Climate Change, and any state or district Heat Action Plan that enables or requires city/district-level action.
   - Whether heatwave is formally addressed as a disaster in the relevant state — i.e. whether the state has notified/declared heatwave a state-specific disaster (this determines access to SDRF-type relief and shapes departmental responsibility). Find and state this explicitly — do not leave it implicit.
   - Any existing schemes relevant to heat action in this city (cool-roof programs, tree/greening missions, labour-welfare heat provisions, health-department heat protocols).
   If any of these cannot be determined, mark `[BLANK: …]`.

   *(Temperature-trend charts and long-range climate projections are intentionally omitted — do not include a climate-projection section.)*

5. **About CHAITRA & Data Sources** — A few sentences explaining what CHAITRA is (a satellite-derived, ward-level heat-diagnostic built on Google Earth Engine) and what it measures, followed by a **data-sources table**. Build the table from the "Data sources and methodology" notes in the WARD DATA block — one row per input, with columns: *Metric / Layer | Source dataset | Resolution | Unit* (e.g. Land Surface Temperature | Landsat 8/9 | 30 m | °C; Night-time LST | MODIS | 1 km | °C). Never leave a cell as a bare dash — where a detail is unknown or locally determined (e.g. the ward-boundary file's vintage), write it as `[BLANK: …]` so it renders as "To be provided by city officials".

6. **Heat Risk Analysis — CHAITRA Output Layers** — The analytical core (Tier A, strict). Walk through the CHAITRA output layers (the map panels), one subsection each, roughly 6–7 layers:
   - Composite Heat Risk Index (ranking + High/Medium/Low classes)
   - Surface Temperature Hotspots (daytime LST deviation)
   - 24-Hour Heat Zones (day + night combined)
   - Population Heat Risk
   - Dense / Vulnerable Housing
   - Cool Roof Opportunity
   - Tree Planting Priority
   Open EACH layer subsection with a map placeholder in this exact form: `[MAP: <layer name> — insert CHAITRA map export for Varanasi]`. Then: (a) explain in one or two sentences what the layer measures and how to read it; (b) cite the specific ward-level findings from the WARD DATA (which wards rank highest and their priority classes — copied exactly; do NOT print the underlying scores); (c) state plainly what the layer implies should be done, and where. Include the Composite Heat Risk ranking as a table with columns **Rank | Ward No. | Priority** only.

7. **Recommended Interventions** — Use Cool Roof and Tree Planting data ONLY (Tier A). State exact quantities — hectares, saplings, dark-roof area, costs — as given in the data, for the High-priority wards. Do not recommend interventions for wards without supporting data. Table columns: cool roofs **Ward No. | Dark Roof Area (ha) | Estimated Coating Cost (₹ lakh)**; tree planting **Ward No. | Canopy Deficit (ha) | Saplings to Plant | Estimated Cost (₹ lakh)** — no score columns.

8. **Inter-Agency Coordination Chart** — Write an explicit coordination table. Different CHAITRA outputs are delivered by different bodies, and the point of this section is to show which agencies must come together for each. For each major intervention/output (cool roofs, tree planting, early warning, vulnerable-housing action, health response), give: *Intervention | Lead agency | Supporting agencies | CHAITRA layer it draws on | Action*. Use realistic Indian municipal/district bodies (Municipal Corporation, State Disaster Management Authority, District Collectorate, Health/CMO, Forest & horticulture, IMD, labour department, urban-development/PWD) but mark any city-specific body name or exact designation `[VERIFY: …]`, and leave the named nodal officer as `[BLANK: …]`.

9. **Early Warning System & Coordination** — `[BLANK: alert thresholds, colour-coded advisories, nodal officer, activation/coordination plan]`.

10. **Implementation Timeline** — `[BLANK: phase-by-phase department responsibilities and schedule]`.

11. **Appendix — Data Sources & Methodology** — Reproduce the methodology described in the WARD DATA documentation.

12. **Concluding Caution** — Mandatory closing caution (see above).

---

## REFERENCE HAPs (STYLE/STRUCTURE ONLY — DO NOT COPY CONTENT)
[Insert excerpts from Ahmedabad, Delhi, Bhubaneswar, and MHT/Churu HAPs here — structure/tone reference only]

---

## WARD DATA FOR VARANASI

Source: CHAITRA methodology (chaitra.info) computed via Google Earth
Engine. Analysis window: 2022-04-01 to 2024-07-31, summer (Apr-Jul).
All classifications are city-specific percentiles. All numbers below were
computed by the pipeline — cite them exactly as written; do not derive new ones.

### City-wide heat context
- Total wards: 89
- City area (union of wards): 69.0 km²
- City mean daytime land surface temperature (LST, summer): 43.1 °C
- City LST percentiles (°C): median 43.3, P90 44.6, P95 44.8, P99 45.5
- City mean nighttime LST (MODIS): 21.1 °C
- Cool vegetation reference temperature (SUHI baseline): 40.6 °C
- Area above 40 °C: 65.7 km²; above 45 °C: 2.5 km²; above 50 °C: 0.0 km²
- City mean albedo: 0.163; city mean rooftop albedo: 0.170

### Ward classification counts (High / Medium / Low)
- Composite Heat Risk Index: 27 High / 18 Medium / 44 Low
- Population Heat Risk: 26 High / 27 Medium / 36 Low
- Cool Roof Priority: 25 High / 26 Medium / 38 Low
- Tree Planting Priority: 25 High / 29 Medium / 35 Low
- 24-Hour Heat Zones: 18 High / 27 Medium / 44 Low
- Dense/Vulnerable Housing: 18 High / 26 Medium / 45 Low

### City-wide aggregates for High-priority wards (pre-computed)
- Population living in High composite-risk wards: 295,140 (modelled estimate, WorldPop 2020)
- High cool-roof-priority wards: dark roof area needing treatment 151 ha; estimated coating cost ₹2,864 lakh (₹150-230/m², midpoint ₹190/m²)
- High tree-priority wards: canopy deficit 150 ha; saplings to plant 30,394 (150 trees/ha of deficit, ×1.35 mortality buffer); estimated cost ₹426 lakh (₹1,400/tree incl. 3-yr maintenance)

### Table 1 — Composite Heat Risk Index ranking (all wards, highest risk first)
Rank computed by the pipeline. riskIndex = (Hazard × Exposure × Vulnerability)^(1/3), IPCC AR6.
(Risk Index is for grounding/traceability; HAP output tables show Rank | Ward No. | Priority only.)

| Rank | Ward No. | Risk Index | Priority |
|---|---|---|---|
| 1 | 56 | 3.53 | High |
| 2 | 81 | 3.40 | High |
| 3 | 25 | 3.40 | High |
| 4 | 58 | 3.35 | High |
| 5 | 86 | 3.34 | High |
| 6 | 75 | 3.34 | High |
| 7 | 45 | 3.31 | High |
| 8 | 23 | 3.29 | High |
| 9 | 11 | 3.28 | High |
| 10 | 46 | 3.27 | High |
| 11 | 88 | 3.19 | High |
| 12 | 50 | 3.18 | High |
| 13 | 13 | 3.17 | High |
| 14 | 55 | 3.12 | High |
| 15 | 43 | 3.11 | High |
| 16 | 77 | 3.11 | High |
| 17 | 53 | 3.10 | High |
| 18 | 2 | 3.09 | High |
| 19 | 29 | 3.08 | High |
| 20 | 24 | 3.08 | High |
| 21 | 15 | 3.08 | High |
| 22 | 84 | 3.07 | High |
| 23 | 9 | 3.06 | High |
| 24 | 37 | 3.05 | High |
| 25 | 59 | 3.04 | High |
| 26 | 4 | 3.04 | High |
| 27 | 31 | 3.03 | High |
| 28 | 60 | 3.01 | Medium |
| 29 | 40 | 2.99 | Medium |
| 30 | 80 | 2.98 | Medium |
| 31 | 52 | 2.96 | Medium |
| 32 | 69 | 2.95 | Medium |
| 33 | 38 | 2.95 | Medium |
| 34 | 87 | 2.94 | Medium |
| 35 | 12 | 2.93 | Medium |
| 36 | 17 | 2.92 | Medium |
| 37 | 82 | 2.92 | Medium |
| 38 | 21 | 2.92 | Medium |
| 39 | 35 | 2.88 | Medium |
| 40 | 64 | 2.87 | Medium |
| 41 | 33 | 2.87 | Medium |
| 42 | 89 | 2.86 | Medium |
| 43 | 73 | 2.85 | Medium |
| 44 | 18 | 2.85 | Medium |
| 45 | 36 | 2.83 | Medium |
| 46 | 47 | 2.83 | Low |
| 47 | 67 | 2.80 | Low |
| 48 | 51 | 2.78 | Low |
| 49 | 76 | 2.77 | Low |
| 50 | 7 | 2.76 | Low |
| 51 | 48 | 2.72 | Low |
| 52 | 14 | 2.71 | Low |
| 53 | 71 | 2.70 | Low |
| 54 | 26 | 2.68 | Low |
| 55 | 16 | 2.68 | Low |
| 56 | 83 | 2.67 | Low |
| 57 | 10 | 2.65 | Low |
| 58 | 42 | 2.65 | Low |
| 59 | 68 | 2.63 | Low |
| 60 | 57 | 2.62 | Low |
| 61 | 70 | 2.57 | Low |
| 62 | 41 | 2.55 | Low |
| 63 | 61 | 2.52 | Low |
| 64 | 79 | 2.51 | Low |
| 65 | 90 | 2.48 | Low |
| 66 | 65 | 2.48 | Low |
| 67 | 72 | 2.47 | Low |
| 68 | 44 | 2.46 | Low |
| 69 | 54 | 2.45 | Low |
| 70 | 6 | 2.44 | Low |
| 71 | 49 | 2.43 | Low |
| 72 | 39 | 2.41 | Low |
| 73 | 27 | 2.41 | Low |
| 74 | 74 | 2.33 | Low |
| 75 | 78 | 2.29 | Low |
| 76 | 28 | 2.28 | Low |
| 77 | 66 | 2.27 | Low |
| 78 | 62 | 2.27 | Low |
| 79 | 63 | 2.24 | Low |
| 80 | 34 | 2.14 | Low |
| 81 | 5 | 2.08 | Low |
| 82 | 8 | 2.06 | Low |
| 83 | 20 | 1.88 | Low |
| 84 | 19 | 1.85 | Low |
| 85 | 3 | 1.85 | Low |
| 86 | 22 | 1.66 | Low |
| 87 | 32 | 1.32 | Low |
| 88 | 30 | 1.23 | Low |
| 89 | 1 | 1.22 | Low |

### Table 2 — Heat hazard per ward (daytime + nighttime)
LST dev = ward mean LST deviation from city mean (°C). Night dev = MODIS
nighttime deviation from city mean (°C). 24h score combines day/night heat,
population and nightlight activity (0-100 scale, geometric mean; values can exceed 100).

| Ward | LST mean °C | LST dev °C | Night dev °C | Day LST °C (MODIS) | Night LST °C (MODIS) | 24h Heat Score | 24h Class |
|---|---|---|---|---|---|---|---|
| 56 | 44.5 | 1.4 | 0.6 | 33.3 | 21.7 | 111.6 | Low |
| 81 | 44.4 | 1.2 | 0.8 | 33.7 | 21.9 | 151.5 | Medium |
| 25 | 44.1 | 0.9 | 0.9 | 33.7 | 22.0 | 111.9 | Low |
| 58 | 44.3 | 1.2 | 0.6 | 32.6 | 21.7 | 119.1 | Low |
| 86 | 44.9 | 1.8 | 0.8 | 33.9 | 21.9 | 147.1 | Medium |
| 75 | 44.1 | 1.0 | 0.9 | 33.9 | 22.0 | 155.3 | High |
| 45 | 44.3 | 1.2 | 1.0 | 33.4 | 22.1 | 158.6 | High |
| 23 | 44.0 | 0.9 | 0.7 | 33.6 | 21.8 | 135.0 | Medium |
| 11 | 43.8 | 0.7 | 0.6 | 34.1 | 21.7 | 128.9 | Low |
| 46 | 44.4 | 1.3 | 0.8 | 33.2 | 21.9 | 146.6 | Medium |
| 88 | 44.2 | 1.1 | 0.9 | 33.7 | 22.1 | 146.0 | Medium |
| 50 | 44.4 | 1.2 | 0.4 | 32.8 | 21.5 | 71.2 | Low |
| 13 | 43.8 | 0.7 | 0.5 | 33.7 | 21.6 | 103.9 | Low |
| 55 | 44.3 | 1.2 | 0.9 | 33.4 | 22.0 | 151.1 | Medium |
| 43 | 43.9 | 0.7 | 0.7 | 33.1 | 21.8 | 107.9 | Low |
| 77 | 43.7 | 0.5 | 0.6 | 34.4 | 21.7 | 144.8 | Medium |
| 53 | 43.5 | 0.3 | 0.8 | 33.6 | 21.9 | 143.2 | Medium |
| 2 | 44.4 | 1.2 | 0.9 | 33.7 | 22.1 | 149.8 | Medium |
| 29 | 43.8 | 0.6 | 0.8 | 34.7 | 21.9 | 137.2 | Medium |
| 24 | 43.9 | 0.7 | 0.8 | 34.0 | 21.9 | 180.9 | High |
| 15 | 44.5 | 1.4 | 0.4 | 34.1 | 21.5 | 181.8 | High |
| 84 | 44.2 | 1.0 | 0.9 | 33.7 | 22.0 | 147.4 | Medium |
| 9 | 43.9 | 0.8 | 0.3 | 34.3 | 21.4 | 126.0 | Low |
| 37 | 43.5 | 0.4 | 1.0 | 34.0 | 22.2 | 186.1 | High |
| 59 | 44.0 | 0.8 | 1.0 | 33.6 | 22.1 | 158.3 | High |
| 4 | 44.4 | 1.3 | 0.1 | 31.7 | 21.2 | 104.7 | Low |
| 31 | 43.5 | 0.3 | 0.6 | 34.1 | 21.8 | 142.9 | Medium |
| 60 | 44.2 | 1.0 | 0.9 | 33.6 | 22.0 | 163.7 | High |
| 40 | 43.8 | 0.7 | 0.8 | 34.3 | 21.9 | 168.4 | High |
| 80 | 43.8 | 0.7 | 0.7 | 33.0 | 21.9 | 141.9 | Medium |
| 52 | 44.5 | 1.4 | 0.8 | 33.0 | 21.9 | 146.7 | Medium |
| 69 | 44.2 | 1.0 | 1.0 | 33.5 | 22.1 | 157.3 | High |
| 38 | 43.7 | 0.6 | 0.9 | 33.9 | 22.0 | 114.4 | Low |
| 87 | 44.2 | 1.1 | 0.8 | 33.3 | 21.9 | 142.6 | Medium |
| 12 | 43.7 | 0.5 | 0.7 | 34.7 | 21.8 | 144.2 | Medium |
| 17 | 43.3 | 0.1 | 0.8 | 34.3 | 21.9 | 154.0 | High |
| 82 | 43.8 | 0.7 | 0.8 | 33.0 | 21.9 | 140.2 | Medium |
| 21 | 43.7 | 0.6 | 1.0 | 33.7 | 22.1 | 172.0 | High |
| 35 | 43.5 | 0.3 | 1.0 | 33.5 | 22.1 | 157.3 | High |
| 64 | 44.3 | 1.1 | 0.8 | 33.4 | 21.9 | 168.5 | High |
| 33 | 43.1 | -0.0 | 0.6 | 35.4 | 21.8 | 111.9 | Low |
| 89 | 44.3 | 1.2 | 0.5 | 32.4 | 21.6 | 123.1 | Low |
| 73 | 43.7 | 0.5 | 1.1 | 33.8 | 22.2 | 170.0 | High |
| 18 | 43.2 | 0.0 | 0.5 | 34.9 | 21.6 | 151.6 | Medium |
| 36 | 42.9 | -0.2 | 0.7 | 34.5 | 21.9 | 98.5 | Low |
| 47 | 44.4 | 1.3 | 0.3 | 32.0 | 21.4 | 109.8 | Low |
| 67 | 44.5 | 1.3 | 0.7 | 32.8 | 21.9 | 149.2 | Medium |
| 51 | 44.4 | 1.3 | 0.7 | 32.8 | 21.8 | 139.2 | Medium |
| 76 | 44.0 | 0.9 | 0.7 | 32.8 | 21.8 | 134.6 | Medium |
| 7 | 43.3 | 0.2 | 0.5 | 34.3 | 21.6 | 128.3 | Low |
| 48 | 44.1 | 0.9 | 0.6 | 32.5 | 21.7 | 140.6 | Medium |
| 14 | 43.7 | 0.6 | 0.1 | 32.3 | 21.2 | 98.6 | Low |
| 71 | 44.3 | 1.2 | 0.3 | 32.0 | 21.4 | 105.0 | Low |
| 26 | 43.4 | 0.3 | 0.3 | 35.3 | 21.4 | 43.0 | Low |
| 16 | 42.9 | -0.2 | 0.2 | 33.3 | 21.3 | 36.1 | Low |
| 83 | 44.3 | 1.2 | 0.2 | 32.0 | 21.3 | 110.7 | Low |
| 10 | 43.3 | 0.1 | 0.2 | 33.6 | 21.4 | 103.3 | Low |
| 42 | 44.8 | 1.7 | 0.3 | 32.1 | 21.4 | 115.3 | Low |
| 68 | 44.0 | 0.9 | 0.7 | 32.9 | 21.8 | 164.7 | High |
| 57 | 43.7 | 0.6 | 0.2 | 35.0 | 21.3 | 153.0 | Medium |
| 70 | 44.4 | 1.2 | -0.1 | 32.4 | 21.0 | 96.0 | Low |
| 41 | 44.4 | 1.2 | 0.0 | 31.2 | 21.1 | 88.8 | Low |
| 61 | 44.3 | 1.1 | 0.7 | 33.3 | 21.9 | 168.9 | High |
| 79 | 44.4 | 1.3 | 0.7 | 32.8 | 21.8 | 161.6 | High |
| 90 | 44.3 | 1.2 | -0.0 | 32.4 | 21.1 | 103.0 | Low |
| 65 | 44.3 | 1.2 | 0.1 | 32.6 | 21.2 | 102.9 | Low |
| 72 | 43.5 | 0.4 | 0.5 | 33.1 | 21.6 | 139.8 | Medium |
| 44 | 43.5 | 0.3 | 0.3 | 32.7 | 21.4 | 121.2 | Low |
| 54 | 43.6 | 0.5 | -0.3 | 32.0 | 20.8 | 65.9 | Low |
| 6 | 43.2 | 0.0 | 0.1 | 35.1 | 21.2 | 41.0 | Low |
| 49 | 44.8 | 1.7 | 0.6 | 32.8 | 21.7 | 153.0 | High |
| 39 | 44.2 | 1.0 | -0.5 | 32.1 | 20.6 | 40.9 | Low |
| 27 | 42.5 | -0.7 | 0.3 | 34.6 | 21.4 | 51.5 | Low |
| 74 | 44.3 | 1.2 | 0.5 | 32.7 | 21.6 | 149.2 | Medium |
| 78 | 44.6 | 1.4 | -0.1 | 32.3 | 21.1 | 99.3 | Low |
| 28 | 43.2 | 0.0 | -0.1 | 33.8 | 21.0 | 71.2 | Low |
| 66 | 44.4 | 1.2 | -0.2 | 30.6 | 20.9 | 72.0 | Low |
| 62 | 44.0 | 0.9 | 0.2 | 32.0 | 21.3 | 92.2 | Low |
| 63 | 44.5 | 1.4 | 0.2 | 32.2 | 21.4 | 126.3 | Low |
| 34 | 43.0 | -0.1 | -0.3 | 31.9 | 20.9 | 27.5 | Low |
| 5 | 42.9 | -0.3 | -0.1 | 35.3 | 21.0 | 98.2 | Low |
| 8 | 42.9 | -0.3 | -0.0 | 31.6 | 21.1 | 77.3 | Low |
| 20 | 42.8 | -0.3 | -0.2 | 34.8 | 20.9 | 132.8 | Medium |
| 19 | 43.0 | -0.1 | -0.9 | 34.8 | 20.3 | 114.0 | Low |
| 3 | 43.0 | -0.1 | -1.0 | 34.4 | 20.1 | 35.0 | Low |
| 22 | 42.4 | -0.8 | -0.2 | 34.0 | 20.9 | 137.7 | Medium |
| 32 | 41.5 | -1.6 | -0.5 | 32.5 | 20.7 | 56.7 | Low |
| 30 | 41.9 | -1.3 | -0.9 | 34.2 | 20.2 | 33.8 | Low |
| 1 | 42.0 | -1.2 | -1.1 | 34.5 | 20.0 | 44.7 | Low |

### Table 3 — Exposure and vulnerability per ward
Housing = Dense/Vulnerable Housing score (0-100). PopRisk = Population Heat
Risk score. Canopy = current tree canopy in built-up areas (%). NDVI = vegetation index.

| Ward No. | Housing Score | Housing Class | PopRisk Score | PopRisk Class | Canopy % | NDVI |
|---|---|---|---|---|---|---|
| 56 | 70.2 | High | 207.5 | High | 0.00 | 0.22 |
| 81 | 60.3 | Medium | 178.1 | High | 0.00 | 0.22 |
| 25 | 77.8 | High | 205.0 | High | 0.00 | 0.20 |
| 58 | 62.2 | High | 184.7 | High | 0.00 | 0.21 |
| 86 | 62.0 | High | 201.6 | High | 0.00 | 0.19 |
| 75 | 52.5 | Medium | 162.5 | High | 0.00 | 0.24 |
| 45 | 46.6 | Low | 154.5 | Medium | 0.00 | 0.19 |
| 23 | 52.9 | Medium | 159.9 | High | 0.00 | 0.25 |
| 11 | 57.4 | Medium | 161.8 | High | 0.01 | 0.27 |
| 46 | 51.8 | Medium | 164.7 | High | 0.00 | 0.19 |
| 88 | 61.3 | Medium | 174.5 | High | 0.00 | 0.17 |
| 50 | 76.3 | High | 208.0 | High | 0.02 | 0.22 |
| 13 | 76.7 | High | 195.5 | High | 0.00 | 0.21 |
| 55 | 49.2 | Low | 157.5 | High | 0.00 | 0.21 |
| 43 | 71.5 | High | 180.6 | High | 0.00 | 0.19 |
| 77 | 61.6 | High | 168.0 | High | 0.00 | 0.23 |
| 53 | 52.7 | Medium | 139.9 | Medium | 0.15 | 0.26 |
| 2 | 58.2 | Medium | 172.7 | High | 0.00 | 0.16 |
| 29 | 71.4 | High | 178.3 | High | 0.00 | 0.21 |
| 24 | 23.7 | Low | 39.7 | Low | 0.14 | 0.26 |
| 15 | 25.9 | Low | 45.4 | Low | 0.00 | 0.21 |
| 84 | 58.0 | Medium | 163.5 | High | 0.00 | 0.15 |
| 9 | 52.9 | Medium | 161.1 | High | 0.02 | 0.25 |
| 37 | 20.3 | Low | 35.9 | Low | 0.00 | 0.26 |
| 59 | 54.5 | Medium | 155.9 | Medium | 0.00 | 0.16 |
| 4 | 40.5 | Low | 139.2 | Medium | 0.00 | 0.25 |
| 31 | 52.9 | Medium | 140.8 | Medium | 0.05 | 0.26 |
| 60 | 47.4 | Low | 152.3 | Medium | 0.00 | 0.18 |
| 40 | 46.8 | Low | 145.2 | Medium | 0.00 | 0.21 |
| 80 | 51.9 | Medium | 146.1 | Medium | 0.00 | 0.18 |
| 52 | 51.4 | Medium | 165.1 | High | 0.00 | 0.15 |
| 69 | 48.3 | Low | 149.1 | Medium | 0.00 | 0.15 |
| 38 | 67.4 | High | 166.0 | High | 0.00 | 0.23 |
| 87 | 57.8 | Medium | 164.4 | High | 0.00 | 0.14 |
| 12 | 58.2 | Medium | 152.2 | Medium | 0.00 | 0.23 |
| 17 | 49.5 | Low | 120.9 | Low | 0.00 | 0.23 |
| 82 | 50.4 | Medium | 138.7 | Medium | 0.00 | 0.18 |
| 21 | 35.9 | Low | 105.3 | Low | 0.00 | 0.20 |
| 35 | 49.4 | Low | 123.8 | Low | 0.00 | 0.15 |
| 64 | 31.1 | Low | 95.2 | Low | 0.00 | 0.18 |
| 33 | 64.2 | High | 139.0 | Medium | 0.04 | 0.27 |
| 89 | 60.2 | Medium | 177.6 | High | 0.00 | 0.16 |
| 73 | 44.2 | Low | 120.9 | Low | 0.00 | 0.16 |
| 18 | 49.0 | Low | 118.8 | Low | 0.03 | 0.29 |
| 36 | 66.8 | High | 121.6 | Low | 0.02 | 0.26 |
| 47 | 46.6 | Low | 150.3 | Medium | 0.00 | 0.19 |
| 67 | 42.8 | Low | 143.9 | Medium | 0.00 | 0.15 |
| 51 | 49.4 | Low | 156.0 | Medium | 0.00 | 0.16 |
| 76 | 54.1 | Medium | 152.2 | Medium | 0.00 | 0.16 |
| 7 | 51.5 | Medium | 128.8 | Low | 0.19 | 0.28 |
| 48 | 29.5 | Low | 80.4 | Low | 0.43 | 0.20 |
| 14 | 60.5 | Medium | 163.8 | High | 0.01 | 0.22 |
| 71 | 55.5 | Medium | 164.3 | High | 0.00 | 0.16 |
| 26 | 64.6 | High | 156.8 | High | 0.00 | 0.26 |
| 16 | 63.1 | High | 122.1 | Low | 0.02 | 0.29 |
| 83 | 34.1 | Low | 108.3 | Low | 0.06 | 0.16 |
| 10 | 65.6 | High | 148.5 | Medium | 0.00 | 0.24 |
| 42 | 42.8 | Low | 150.5 | Medium | 0.00 | 0.15 |
| 68 | 29.5 | Low | 79.4 | Low | 0.00 | 0.18 |
| 57 | 40.5 | Low | 122.7 | Low | 0.04 | 0.25 |
| 70 | 42.5 | Low | 136.6 | Medium | 0.00 | 0.19 |
| 41 | 47.7 | Low | 150.2 | Medium | 0.00 | 0.17 |
| 61 | 28.5 | Low | 75.8 | Low | 0.00 | 0.15 |
| 79 | 31.4 | Low | 96.0 | Low | 0.00 | 0.13 |
| 90 | 48.2 | Low | 143.1 | Medium | 0.00 | 0.14 |
| 65 | 38.1 | Low | 120.9 | Low | 0.00 | 0.16 |
| 72 | 38.6 | Low | 101.9 | Low | 0.00 | 0.24 |
| 44 | 36.4 | Low | 99.0 | Low | 0.09 | 0.25 |
| 54 | 50.3 | Low | 137.5 | Medium | 0.00 | 0.23 |
| 6 | 70.8 | High | 149.2 | Medium | 0.00 | 0.25 |
| 49 | 25.9 | Low | 43.3 | Low | 0.00 | 0.13 |
| 39 | 42.5 | Low | 131.2 | Medium | 0.00 | 0.20 |
| 27 | 62.6 | High | 44.1 | Low | 0.00 | 0.30 |
| 74 | 17.8 | Low | 40.3 | Low | 0.00 | 0.13 |
| 78 | 35.6 | Low | 113.6 | Low | 0.00 | 0.13 |
| 28 | 69.2 | High | 145.8 | Medium | 0.00 | 0.26 |
| 66 | 43.9 | Low | 138.2 | Medium | 0.00 | 0.16 |
| 62 | 45.9 | Low | 129.0 | Medium | 0.00 | 0.14 |
| 63 | 18.3 | Low | 40.9 | Low | 0.00 | 0.12 |
| 34 | 57.0 | Medium | 119.6 | Low | 0.10 | 0.30 |
| 5 | 57.8 | Medium | 109.1 | Low | 0.05 | 0.29 |
| 8 | 47.4 | Low | 94.6 | Low | 0.13 | 0.27 |
| 20 | 41.8 | Low | 81.5 | Low | 0.05 | 0.30 |
| 19 | 59.0 | Medium | 120.0 | Low | 0.00 | 0.26 |
| 3 | 50.8 | Medium | 115.7 | Low | 0.00 | 0.28 |
| 22 | 27.8 | Low | 15.6 | Low | 0.04 | 0.32 |
| 32 | 34.6 | Low | 27.7 | Low | 1.14 | 0.37 |
| 30 | 43.4 | Low | 34.2 | Low | 0.12 | 0.34 |
| 1 | 48.1 | Low | 36.3 | Low | 0.12 | 0.33 |

### Table 4 — Intervention quantities per ward (cool roofs + tree planting)
CoolRoof score NA = ward ineligible/insufficient data (classified Low).
Costs in ₹ lakh. Dark roof area in hectares (roof albedo < 0.20).
(Scores are for grounding/traceability; HAP output tables show class and quantities only.)

| Ward No. | CoolRoof Score | CoolRoof Class | Dark Roof ha | Roof Cost ₹L | Tree Score | Tree Class | Canopy Deficit ha | Saplings | Tree Cost ₹L |
|---|---|---|---|---|---|---|---|---|---|
| 56 | 93.2 | High | 15.6 | 296.0 | 209.5 | High | 11.5 | 2,320 | 32.5 |
| 81 | 94.9 | High | 4.9 | 92.3 | 196.1 | High | 3.4 | 697 | 9.8 |
| 25 | 81.3 | Medium | 22.5 | 427.2 | 196.3 | High | 17.6 | 3,558 | 49.8 |
| 58 | 93.5 | High | 8.4 | 160.4 | 199.3 | High | 6.2 | 1,249 | 17.5 |
| 86 | 99.3 | High | 8.2 | 155.3 | 205.5 | High | 6.2 | 1,255 | 17.6 |
| 75 | 83.0 | Medium | 12.4 | 236.1 | 194.3 | High | 9.2 | 1,857 | 26.0 |
| 45 | 90.2 | High | 10.1 | 191.3 | 201.0 | High | 7.5 | 1,514 | 21.2 |
| 23 | 72.8 | Medium | 16.7 | 318.2 | 190.5 | Medium | 12.4 | 2,520 | 35.3 |
| 11 | 68.3 | Low | 18.2 | 346.4 | 183.0 | Medium | 13.3 | 2,705 | 37.9 |
| 46 | 95.3 | High | 4.8 | 90.5 | 198.5 | High | 3.5 | 711 | 10.0 |
| 88 | 87.6 | High | 3.5 | 67.4 | 189.6 | Medium | 2.7 | 557 | 7.8 |
| 50 | 86.0 | High | 10.6 | 201.9 | 201.3 | High | 8.2 | 1,658 | 23.2 |
| 13 | 75.4 | Medium | 42.2 | 801.3 | 188.6 | Medium | 33.3 | 6,737 | 94.3 |
| 55 | 80.5 | Medium | 7.6 | 145.3 | 197.1 | High | 6.0 | 1,209 | 16.9 |
| 43 | 77.6 | Medium | 8.9 | 169.8 | 180.6 | Medium | 7.0 | 1,417 | 19.8 |
| 77 | 72.1 | Medium | 39.4 | 749.0 | 182.2 | Medium | 30.7 | 6,225 | 87.2 |
| 53 | 59.8 | Low | 23.3 | 442.5 | 166.6 | Low | 18.0 | 3,643 | 51.0 |
| 2 | 87.8 | High | 3.6 | 67.8 | 193.5 | High | 2.8 | 573 | 8.0 |
| 29 | 75.8 | Medium | 10.4 | 198.2 | 178.3 | Medium | 8.3 | 1,688 | 23.6 |
| 24 | 70.3 | Low | 14.5 | 275.8 | 183.6 | Medium | 10.9 | 2,200 | 30.8 |
| 15 | 97.9 | High | 18.0 | 342.2 | 210.7 | High | 12.9 | 2,614 | 36.6 |
| 84 | 87.5 | High | 2.1 | 40.1 | 184.1 | Medium | 1.6 | 329 | 4.6 |
| 9 | 72.9 | Medium | 35.8 | 680.1 | 191.8 | Medium | 26.8 | 5,425 | 76.0 |
| 37 | 67.4 | Low | 13.3 | 253.1 | 166.7 | Low | 9.7 | 1,966 | 27.5 |
| 59 | 82.6 | Medium | 3.8 | 71.5 | 181.9 | Medium | 2.9 | 593 | 8.3 |
| 4 | 88.2 | High | 13.0 | 247.1 | 203.5 | High | 9.2 | 1,865 | 26.1 |
| 31 | 70.4 | Low | 19.7 | 374.9 | 167.4 | Low | 14.8 | 3,000 | 42.0 |
| 60 | 83.5 | Medium | 9.3 | 177.0 | 195.6 | High | 7.3 | 1,484 | 20.8 |
| 40 | 75.2 | Medium | 34.9 | 663.9 | 188.3 | Medium | 27.8 | 5,635 | 78.9 |
| 80 | 79.9 | Medium | 4.7 | 88.6 | 176.2 | Low | 3.6 | 731 | 10.2 |
| 52 | 87.4 | High | 3.7 | 70.4 | 200.6 | High | 3.0 | 608 | 8.5 |
| 69 | 84.1 | High | 3.8 | 71.7 | 189.0 | Medium | 3.0 | 608 | 8.5 |
| 38 | 65.5 | Low | 4.6 | 87.7 | 171.3 | Low | 3.8 | 769 | 10.8 |
| 87 | 85.1 | High | 2.0 | 37.3 | 185.6 | Medium | 1.6 | 316 | 4.4 |
| 12 | 74.9 | Medium | 6.2 | 117.6 | 170.7 | Low | 4.8 | 979 | 13.7 |
| 17 | 66.6 | Low | 7.0 | 133.5 | 150.5 | Low | 5.1 | 1,044 | 14.6 |
| 82 | 82.8 | Medium | 2.5 | 48.3 | 170.7 | Low | 1.9 | 387 | 5.4 |
| 21 | 70.7 | Low | 10.3 | 195.0 | 174.4 | Low | 7.8 | 1,575 | 22.1 |
| 35 | 69.6 | Low | 2.3 | 43.5 | 154.6 | Low | 1.8 | 357 | 5.0 |
| 64 | 85.0 | High | 6.9 | 130.7 | 195.7 | High | 5.3 | 1,075 | 15.1 |
| 33 | 52.7 | Low | 40.6 | 771.6 | 147.1 | Low | 33.5 | 6,783 | 95.0 |
| 89 | 83.9 | High | 4.6 | 87.6 | 195.3 | High | 3.8 | 765 | 10.7 |
| 73 | 78.5 | Medium | 2.8 | 53.6 | 163.5 | Low | 2.1 | 437 | 6.1 |
| 18 | 52.1 | Low | 27.2 | 516.5 | 148.9 | Low | 20.9 | 4,237 | 59.3 |
| 36 | 44.8 | Low | 33.9 | 643.9 | 126.1 | Low | 28.1 | 5,689 | 79.6 |
| 47 | 87.7 | High | 4.5 | 84.7 | 195.6 | High | 3.5 | 711 | 10.0 |
| 67 | 86.5 | High | 3.9 | 74.7 | 200.2 | High | 3.2 | 648 | 9.1 |
| 51 | 85.3 | High | 3.3 | 62.1 | 194.7 | High | 2.6 | 536 | 7.5 |
| 76 | 80.5 | Medium | 2.5 | 47.4 | 179.1 | Medium | 2.0 | 404 | 5.7 |
| 7 | 32.9 | Low | 16.0 | 303.5 | 155.5 | Low | 14.1 | 2,861 | 40.1 |
| 48 | 80.6 | Medium | 5.3 | 100.9 | 184.8 | Medium | 3.9 | 790 | 11.1 |
| 14 | 71.0 | Medium | 25.5 | 483.6 | 179.4 | Medium | 20.4 | 4,138 | 57.9 |
| 71 | 85.6 | High | 2.6 | 50.2 | 190.1 | Medium | 2.1 | 427 | 6.0 |
| 26 | 45.7 | Low | 43.5 | 827.4 | 165.6 | Low | 41.7 | 8,441 | 118.2 |
| 16 | 41.2 | Low | 38.6 | 733.9 | 130.5 | Low | 30.0 | 6,085 | 85.2 |
| 83 | 79.9 | Medium | 5.9 | 112.3 | 191.6 | Medium | 4.9 | 990 | 13.9 |
| 10 | 60.4 | Low | 20.4 | 387.6 | 155.4 | Low | 16.4 | 3,323 | 46.5 |
| 42 | 90.7 | High | 4.0 | 76.6 | 200.6 | High | 3.3 | 661 | 9.3 |
| 68 | 76.0 | Medium | 6.0 | 113.1 | 185.2 | Medium | 4.7 | 952 | 13.3 |
| 57 | 68.4 | Low | 15.7 | 299.0 | 179.0 | Medium | 12.3 | 2,491 | 34.9 |
| 70 | 72.6 | Medium | 5.4 | 102.6 | 190.6 | Medium | 4.8 | 974 | 13.6 |
| 41 | 79.8 | Medium | 5.6 | 107.2 | 191.9 | High | 4.5 | 914 | 12.8 |
| 61 | 78.3 | Medium | 4.9 | 92.6 | 195.0 | High | 4.0 | 821 | 11.5 |
| 79 | 85.1 | High | 2.9 | 55.3 | 194.4 | High | 2.4 | 484 | 6.8 |
| 90 | 88.4 | High | 2.1 | 40.6 | 181.4 | Medium | 1.7 | 337 | 4.7 |
| 65 | 67.8 | Low | 4.4 | 84.3 | 187.7 | Medium | 4.1 | 836 | 11.7 |
| 72 | 56.1 | Low | 3.1 | 58.2 | 156.1 | Low | 2.5 | 516 | 7.2 |
| 44 | 46.1 | Low | 12.5 | 237.3 | 161.5 | Low | 11.0 | 2,223 | 31.1 |
| 54 | 76.5 | Medium | 12.6 | 239.1 | 169.4 | Low | 9.0 | 1,818 | 25.5 |
| 6 | 52.7 | Low | 43.9 | 834.4 | 149.8 | Low | 36.9 | 7,465 | 104.5 |
| 49 | 91.1 | High | 3.7 | 69.9 | 193.5 | High | 3.0 | 607 | 8.5 |
| 39 | 65.6 | Low | 6.6 | 126.3 | 183.7 | Medium | 5.8 | 1,170 | 16.4 |
| 27 | 0.0 | Low | 69.6 | 1,321.8 | 47.4 | Low | 56.2 | 11,382 | 159.3 |
| 74 | 43.2 | Low | 5.0 | 95.1 | 187.1 | Medium | 6.0 | 1,213 | 17.0 |
| 78 | 0.0 | Low | 3.1 | 58.6 | 188.3 | Medium | 3.5 | 712 | 10.0 |
| 28 | 54.8 | Low | 31.4 | 597.0 | 148.3 | Low | 25.4 | 5,143 | 72.0 |
| 66 | 79.0 | Medium | 3.1 | 58.1 | 188.6 | Medium | 2.5 | 503 | 7.0 |
| 62 | 50.5 | Low | 3.9 | 74.2 | 169.7 | Low | 4.1 | 823 | 11.5 |
| 63 | 50.6 | Low | 3.2 | 60.1 | 190.2 | Medium | 3.4 | 697 | 9.8 |
| 34 | 33.2 | Low | 21.4 | 406.0 | 135.5 | Low | 18.6 | 3,763 | 52.7 |
| 5 | 35.2 | Low | 27.6 | 523.8 | 122.8 | Low | 24.6 | 4,982 | 69.7 |
| 8 | 41.2 | Low | 20.2 | 384.6 | 121.1 | Low | 16.9 | 3,420 | 47.9 |
| 20 | 29.9 | Low | 21.8 | 414.8 | 115.5 | Low | 18.8 | 3,802 | 53.2 |
| 19 | 50.7 | Low | 25.0 | 475.2 | 133.4 | Low | 19.4 | 3,932 | 55.0 |
| 3 | NA | Low | 72.8 | 1,382.3 | 141.5 | Low | 67.2 | 13,607 | 190.5 |
| 22 | NA | Low | 15.3 | 291.3 | 45.2 | Low | 13.5 | 2,733 | 38.3 |
| 32 | 63.0 | Low | 61.6 | 1,170.5 | 47.1 | Low | 61.4 | 12,445 | 174.2 |
| 30 | 47.3 | Low | 57.6 | 1,094.2 | 46.9 | Low | 62.9 | 12,740 | 178.4 |
| 1 | 36.3 | Low | 29.5 | 560.0 | 46.0 | Low | 30.7 | 6,220 | 87.1 |

### Data sources and methodology (for Appendix)
- Ward boundaries: municipal ward shapefile as hosted in CHAITRA (GEE asset)
- Daytime LST: Landsat 8/9 Collection 2 L2 thermal, 30 m, summer (Apr-Jul) median composite, cloud-masked
- Nighttime LST: MODIS Terra+Aqua (MOD11A1/MYD11A1), 1 km, 2-year median
- Population: WorldPop 100 m, 2020 (model input for risk scores; not printed per ward — to be reconciled with municipal records)
- Land cover: ESA WorldCover v200 (2021), 10 m; canopy: Google Dynamic World, 10 m
- Albedo: Sentinel-2 broadband albedo (Liang 2001 coefficients), 10 m
- Housing vulnerability: GHSL Built Surface 2020 density + vegetation deficit + VIIRS nightlight dimness, geometric mean, P5-P95 normalized
- Composite risk: IPCC AR6 framework, Risk = (H × E × V)^(1/3); H = day + night heat hotspot scores, E = ln(population+1), V = canopy deficit + housing density + albedo deficit; classified by city percentiles (P50/P70)
- Cool roof costing: ₹150-230/m² (GRIHA 2021 / GEDA 2022-23), midpoint ₹190/m²
- Tree costing: 150 trees/ha of canopy deficit, ×1.35 mortality buffer, ₹1,400/tree including 3-year maintenance (CHAITRA layer constants)

---

## TASK
Draft the full Heat Action Plan for Varanasi following the structure above.

- Sections 1, 5, 6, 7, 8, 11, and 12 are to be written now.
- Sections 3 and 4 are to be written now using your marked Tier B knowledge — use web search if available (`[VERIFY: …]` every specific fact, `[BLANK: …]` anything unknown).
- Sections 9 and 10 are left as marked blanks.

Obey the two-tier grounding rules absolutely: CHAITRA numbers copied exactly from the WARD DATA (Tier A); all outside facts marked `[VERIFY]` or `[BLANK]` (Tier B). Output the complete document only.
