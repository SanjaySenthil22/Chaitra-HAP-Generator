# Findings from CHAITRA Source Code (`CHAITRA code copy.js`, 8,407 lines)

Read-only analysis of the Google Earth Engine App script behind chaitra.info.
Everything below is extracted from the code, with line references.

---

## 1. THE SHAPEFILE BLOCKER IS (PROBABLY) SOLVED

Agra's ward boundaries already exist as a GEE asset (line 52-58):

```
projects/gee-piyushn44/assets/Agra_Wards
```

- Projection used for area math: **EPSG:32643** (UTM 43N)
- City bbox: [77.95, 27.10, 78.10, 27.25], municipal area ~188 km²
- All 13 cities have assets under `projects/gee-piyushn44/assets/`
  (Varanasi, Bhubaneswar, Agra, Kolkata, Surat, Lucknow, Chennai, Jaipur,
  Ahmedabad, Mumbai, Hyderabad, Bangalore, Delhi) — lines 37-129.

**Caveat:** assets used by a public EE App are not necessarily readable from
your own Code Editor account. Test with
`print(ee.FeatureCollection('projects/gee-piyushn44/assets/Agra_Wards').limit(5))`.
If access is denied, the ask to Piyush shrinks from "send me the shapefile"
to "share read access on the Agra_Wards asset" (one click in the EE Asset
manager).

### Ward ID / name standardization (lines 1959-2019, `loadBoundaries`)
Every ward feature is normalized to:
- `WARD_NO` — integer, taken from the first existing of: `WARD_NO`,
  `ward_no`, `ward_lgd_c`, `id`, `system:index` (first numeric run parsed)
- `ward_name` — first of `ward_name`, `WARD_NAME`, `ward_lgd_n`, `name`,
  `NAME`, fallback `"Ward N"`; unicode dashes normalized
- `city`, `state` (from `cityStateMapping`, line 132)

This answers the "unknown ward ID field names" question that paused
`chaitra_gee_reconstruction.py`.

---

## 2. WHY THE EXPORT BUTTON "DOES NOTHING"

`exportWardStatistics()` (lines 7887-8066) ends in `Export.table.toDrive(...)`.

**`Export.table.toDrive` is a no-op inside a published Earth Engine App.**
Export creates a *task*, and tasks can only be submitted/run from the Code
Editor's Tasks tab, which doesn't exist in an App. The button runs fine,
the export just never materializes. This is a known EE platform limitation,
not a bug in CHAITRA's logic.

**Fix / workaround:** run this same script in the GEE Code Editor, select
Agra, wait for analysis to finish, click "Export Ward Data to Drive", then
open the **Tasks** tab and click **Run**. The CSV lands in Drive folder
`CHAITRA_Exports` as `CHAITRA_WardStats_Agra_<timestamp>.csv`.
(Alternative: swap the Export call for `exportData.getDownloadURL(...)`,
which does work in Apps.)

### Secondary export bug (matters even in the Code Editor)
The export joins only 5 result collections onto the wards
(lines 7901-7923): `lstWards`, `popHeatWards`, `coolRoofWards`,
`canopyGapWards`, `activityHeatWards`.

It never joins `heatRiskWards` or `informalHousingWards`, yet the
`selectors` list (lines 7927-7983) includes their columns:
`riskIndex`, `hazardIndex`, `exposureIndex`, `vulnerabilityIndex`,
`informalHousingScore`. Those columns will come out blank (or the task
errors). Two more `joinWardResults(...)` calls fix it. So the composite
Heat Risk Index — the headline number for HAP section 6 — is currently
missing from the export path.

---

## 3. THE EXPORT SCHEMA = THE HAP "WARD DATA" BLOCK

The CSV is designed for exactly our use case — it even prepends a
definitions row (lines 7988-8047). Per-ward columns:

| Group | Columns |
|---|---|
| Identifiers | `state`, `city`, `WARD_NO`, `ward_name` |
| Temperature (Landsat 30m daytime) | `LST_mean/min/max` (°C), `LST_hotspot` (deviation from city mean) |
| Urban heat island | `UHI_all_mean`, `UHI_all_stdDev` (°C vs cool-vegetation reference) |
| Population (WorldPop 100m, 2020) | `totalPop`, `popDensity` |
| Albedo (built areas) | `builtAlbedo_mean/min/max` |
| Supplemental inputs | `ntl_mean` (VIIRS), `nightLST_mean` (MODIS), `ndvi_mean`, `treeProb_mean`, `vegDeficit_mean`, `dwBuiltProb_mean`, `ghslDensity_mean`, `dimness_mean` |
| Population Heat Risk | `riskScore` (0-100), `popAtRisk` (count), `exposureRate` (%) |
| Cool Roof | `coolRoofPriorityScore`, `darkRoofArea_km2` (albedo<0.20), `potentialCooling_C`, `estimatedCost_Lakhs` |
| Tree Planting | `priority_score`, `currentCanopy_pct`, `canopyDeficit_ha`, `treesNeeded`, `totalCost_Lakhs` |
| 24-Hour Heat | `activityHeatScore`, `dayLST`, `nightLST`, `avgLST_24h` |
| Dense Housing | `informalHousingScore` |
| Composite (IPCC) | `riskIndex`, `hazardIndex`, `exposureIndex`, `vulnerabilityIndex` |
| Classification | `priority_level` (High/Medium/Low, percentile-based) |

This is richer than the placeholder demo data — it directly feeds HAP
sections 4 (hazard), 5 (exposure/vulnerability), 6 (ranking), 7
(interventions with exact quantities and costs).

---

## 4. CITY-WIDE STATS "FOR HEAT ACTION PLAN" — ALREADY IN THE CODE

The code computes city-level context explicitly labeled for HAPs
(lines 7028-7060, stored in `wardResults` at 7544-7570):

- `cityHeatStats` — city LST mean + P50/P90/P95/P99
- `heatExceedanceAreas` — km² of city above **40/45/50 °C** ("for Heat
  Action Plan triggers") — usable for HAP section 8 (alert thresholds
  context, though official IMD thresholds still need a human)
- `uhiStats` + `uhiExceedanceAreas` — city SUHI stats, `coolReference`
- `cityPopStats` — city population / resource metrics
- `scoringMatrix` (createScoringMatrix, line 5144) — cross-layer ward matrix

---

## 5. RESOURCE-PLANNING FRAMEWORK — FILLS PART OF THE "MISSING 5-7 PAGES"

`RESOURCE_SOURCES` (lines 181-461) and `RESOURCE_CONFIG` (lines 462-585)
define a fully cited resource model, computed per ward by four functions
(lines 599-887): `calculateEmergencyResources`, `calculateCoolRoofResources`,
`calculateTreeResources`, `calculateActivityResources`.

### Emergency response (per high-risk ward population)
- Cooling shelters: **1 per 15,000 (High) / 20,000 (Medium) / 30,000 (Low)**
  — source: Ahmedabad HAP + NDMA Cooling Centre Guidelines May 2025
- Vulnerable population: 22% of ward pop (Census 2011 basis)
- ORS: 5 packets/vulnerable person/5-day event @ ₹7; rehydration stations
  1 per 10,000
- Drinking water: 3 L/person/day (Sphere 2018)
- ASHA + Anganwadi workers: 1 per 1,000 each (NUHM/ICDS)
- Heat illness: 0.1-0.5% of vulnerable pop (NPCCHH 2024; Azhar et al. 2014);
  5% hospitalization; ambulance math from EMRI 108 trip capacity

### Cool roofs
- 60% of built area is roof; 70% dark/suitable; **₹150-230/m²**
  (matches README); government-building counts via URDPFI 2014 norms

### Tree planting (differs from README/demo assumptions!)
- Target canopy 20%; plantable fraction of deficit **20-30%** by density
- **400 trees per plantable hectare** (not 150/ha)
- **1.5× mortality buffer** (67% 3-yr survival; not +35%)
- **₹750/tree midpoint** (₹150-300 sapling + ₹230 MNREGA labor + ₹300
  3-yr maintenance; not ₹1,400/tree)
- Location split: 40% avenue / 25% parks / 15% Nagar Van / 20% institutional
- 3-year phasing: 50/30/20%, 8-month nursery lead time

### 24-hour activity zones
- Rehydration 1/15,000; misting 1/3km² (High); shade nets ₹15-25K/100m²

### Dense housing
- Community taps (1/150 people, ₹80K), toilet blocks, solar (₹12K/HH),
  roof insulation ₹3,750/home, shade pavilions (1/500 people, ₹2L),
  water tanks — informal areas modeled as +6.5°C hotter

**Implication for the "page count" question:** the interventions +
resource-planning sections can be much larger and fully data-grounded than
assumed — the code computes per-ward emergency logistics, not just cool
roofs and trees. UP-specific context is even included (36 confirmed heat
deaths 2024, highest state — HeatWatch/DTE Sep 2024, line 229-234).

### ⚠️ Corrections needed to `agra_demo_data.md` / README assumptions
| Item | README/demo said | Code actually says |
|---|---|---|
| Cooling shelters | 1 per 20K (high-risk) | 1 per 15K high / 20K med / 30K low |
| Saplings | 150/ha, +35% buffer | 400/plantable-ha, 1.5× buffer, plantable = 20-30% of deficit |
| Tree cost | ₹1,400/tree | ₹750/tree midpoint (with breakdown) |
| Cool roof | ₹150-230/m² | ✓ matches |

---

## 6. OTHER USEFUL DETAILS

- Analysis window: `2022-04-01` → `2024-07-31`, summer filter Apr-Jul
  (lines 14-16) — cite this in the HAP methodology appendix.
- Default city is Varanasi (line 13, triggered at line 8406); city switch
  re-runs `runAnalysis()` (line 6923).
- Extra per-ward metrics not in the README's 7-layer list: `heat_score`
  (displayed hotspot score), `uhi_built_score` ("Built Surface Heat —
  Intervention Zones", actionable for cool roof/pavement), min/max LST,
  potential cooling °C.
- Composite risk uses `(H×E×V)^(1/3)` with floor 0.05 — confirms README;
  informal housing is excluded from composite V by default
  (`{includeInformal: false}`, line 7537).
- Priority classifications are percentile-based per city (confirms README).

---

## 7. PATH TO REAL WARD DATA — ✅ DONE (July 2026)

Asset read access was verified, and the entire computation was ported to
Python: **`chaitra_ward_pipeline.py`**. It runs CHAITRA's exact methods
against the live assets and produces the ward CSV directly — no dashboard,
no export button, no Code Editor needed.

```
python3 chaitra_ward_pipeline.py --city Agra --project <your-gcp-project>
```

Outputs `<city>_ward_data.csv` (~75 columns/ward incl. Census 2011
attributes) + `<city>_city_stats.json` (city-wide HAP context). Works for
any of the 13 configured cities via `--city`; new cities only need an
asset path entry in `CITY_CONFIGS`.

### Two additional bugs found in CHAITRA's JS while porting

1. **Cool reference temperature silently defaults to 30°C** (JS line 2507):
   the code reads key `'LST_p20'` from a single-percentile reduceRegion,
   but EE returns the key `'LST'`. So the SUHI "cool vegetation baseline"
   is always the 30°C fallback. For Agra the true p20-of-cool-vegetation is
   ~40.7°C, meaning the dashboard's UHI magnitudes are inflated by ~10°C.
   The Python port fixes this (checks both keys). Worth telling Piyush.

2. **Two conflicting tree-costing models** in the same codebase — verified
   (July 2026) that BOTH are live, neither is commented out:
   - Layer/export columns (`treesNeeded`, `totalCost_Lakhs`, JS line
     4157-4166): 150 trees/ha of deficit, ×1.35 buffer, ₹1,400/tree.
     These feed the per-ward table/export values.
   - UI resource panels (`RESOURCE_CONFIG` line 462, called via
     `calculateTreeResources` at line 5879 to render the dashboard's
     "RESOURCE REQUIREMENTS" panel): 20-30% of deficit plantable,
     400 trees/plantable-ha, ×1.5 buffer, ₹750/tree.
   So the dashboard displays DIFFERENT tree numbers in the ward table vs
   the resource panel. The resource functions are commented "NEW SPEC" and
   carry full citations, suggesting RESOURCE_CONFIG is the intended newer
   model and the layer columns are stale. Our pipeline ports the
   layer/export model (matching CHAITRA's export). Confirm with Piyush;
   switching is a 3-constant change in calculate_tree_planting().

### Notes on real Agra output (first run)
- 91 wards, no blank columns. Summer daytime LST 42-47°C; 125 of 132 km²
  exceeds 40°C; ward hotspot deviations ±3°C.
- `tot_p` (Census 2011) and `totalPop` (WorldPop 2020) differ per ward —
  different years and methods; cite the source per number in the HAP.
- Ward tree canopy is near zero (<2% everywhere) — verified genuine in
  Dynamic World (Agra's built-up areas are tree-sparse) but it drives very
  large `treesNeeded`; sanity-check against the dashboard before quoting.
- A few wards have NaN `coolRoofPriorityScore` (below-P5 percentile
  normalization goes negative → fractional power → NaN). Same behavior
  exists in the JS; these wards are classified Low. Treat NaN as
  "ineligible/insufficient data" in the HAP prompt.

## §7 Canopy-deficit inflation bug (found 2026-08, fixed in our port)
CHAITRA's JS (line 4154) computes `canopyDeficit_ha = builtArea_ha × deficit`
where `deficit` is the NORMALISED shortfall `(target − current)/target`
(= 1.0 for a treeless ward) — so a treeless ward reports its entire built
area as "canopy deficit". Agra summed to 10,397 ha = 79% of the whole city,
impossible for a 20% canopy target. Our port now multiplies by
`TARGET_CANOPY_FRAC` to yield the true canopy-area gap (Agra: 2,079 ha =
15.7% of city; every ward ≤ its 20% cap). Saplings/costs scale down ~5×;
priority scores and classifications are unchanged (they use the normalised
deficit). Report upstream to Piyush alongside the SUHI reference bug (§5).

## §8 Ward-number extraction (found 2026-08, fixed)
The Varanasi asset's `ward_lgd_c` values (26xxx) are LGD administrative
codes, not municipal ward numbers — reviewers flagged them. The asset also
carries `sourcewa_1` (municipal ward number, pairs with the ward name) and
`NNVNS`. `load_boundaries` now prefers WARD_NO → ward_no → sourcewa_1 →
NNVNS before falling back to ward_lgd_c. Varanasi wards now number 1-90.
