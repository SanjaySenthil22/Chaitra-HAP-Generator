# CHAITRA HAP Generator

Generates a ward-level Heat Action Plan (HAP) for an Indian city from
[CHAITRA](https://chaitra.info)'s satellite-derived heat analysis. Given a
city, the pipeline computes ward-by-ward heat risk, vulnerability, and
intervention data on Google Earth Engine, drafts a full HAP document with an
LLM grounded strictly in that data (the model narrates, it never calculates
or invents a number), mechanically verifies every figure in the draft against
the source data, renders the seven CHAITRA layers as ward maps, and produces
a finished, reviewable Word document.


## Quickstart

```bash
pip3 install -r requirements.txt
brew install pandoc              # or: apt install pandoc
earthengine authenticate         # one-time, opens a browser

export ANTHROPIC_API_KEY=sk-ant-...
python3 generate_hap.py --city Agra --project <your-gcp-project>
```

Produces `outputs/Agra_HAP_Draft.docx`. See **Setup** below for what
`<your-gcp-project>` needs and how to get ward-asset access.

## Setup

There are no credential files anywhere in this repo (no `.env`, no config
with a key field) — every credential is either a shell environment variable
or a one-time browser login. Checklist for a first-time setup:

1. **Python packages** — `pip3 install -r requirements.txt` (earthengine-api,
   anthropic, matplotlib, python-docx).

2. **pandoc** — converts the drafted markdown to `.docx`. Not a Python
   package; install via `brew install pandoc` (macOS) or your system's
   package manager.

3. **Earth Engine login** — run `earthengine authenticate` once. It opens a
   browser, you sign in with your Google account, and the resulting token is
   cached by the `earthengine-api` library itself (`~/.config/earthengine/`)
   — nothing in this repo to edit.

4. **Your own GCP project**, with the Earth Engine API enabled, tied to the
   account you just authenticated. This is the *compute* identity — any lab
   member can create their own. Pass its ID via `--project <id>` on the
   command line each time, **or** set it once so you never have to type it:
   ```bash
   export CHAITRA_GEE_PROJECT=<your-gcp-project-id>   # add to ~/.zshrc to persist
   ```
   (every script's `--project` flag defaults to this env var if set —
   see e.g. `chaitra_ward_pipeline.py` line 1324).

5. **Read access to the ward-boundary assets** — these live in CHAITRA's own
   GCP project (`projects/gee-piyushn44/assets/...`, listed in
   `CITY_CONFIGS` near the top of `chaitra_ward_pipeline.py`, currently line
   39). This is *data* access, separate from #4's compute project. Email the
   CHAITRA project lead and ask them to grant read access to the ward assets
   for the Google account you authenticated in step 3. Nothing to configure
   locally once granted — Earth Engine checks it server-side.

6. **Anthropic API key** — required only for the LLM drafting step
   (`generate_hap.py`, or any run using web search). Get one at
   [console.anthropic.com](https://console.anthropic.com) (pay-as-you-go, no
   subscription), then:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...   # add to ~/.zshrc to persist
   ```
   Cost is roughly $0.50–1.00 per city per run (Opus-tier tokens + a handful
   of web searches for local context facts). Without a key, everything
   except the drafting step still works — you can assemble the grounding
   data and prompt, then draft by hand or paste the prompt into claude.ai.

**Adding a new city later:** the only file you ever need to hand-edit is
`CITY_CONFIGS` in `chaitra_ward_pipeline.py` — add one line with the city's
ward-asset path, UTM zone, and area:
```python
'NewCity': {'assetPath': 'projects/gee-piyushn44/assets/NewCity_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 123},
```
Everything downstream (prompt, verification, maps, docx) is city-agnostic.

## Usage

**Full pipeline, one command** (needs an Anthropic key):
```bash
python3 generate_hap.py --city <City> --project <your-gcp-project>
```
`--project` is only required the first time for a city (to compute its ward
data); once `outputs/<city>_ward_data.csv` exists, omit it.

**Step by step** (useful without an API key, or to inspect intermediate
output):
```bash
python3 chaitra_ward_pipeline.py --city <City> --project <your-gcp-project>
python3 assemble_hap_prompt.py --city <City>       # builds the grounding data + LLM prompt
# draft outputs/<city>_hap_draft.md by hand, or via outputs/<city>_hap_prompt.md in claude.ai
python3 verify_hap_numbers.py --draft outputs/<city>_hap_draft.md --data outputs/<city>_hap_data.md
python3 make_hap_maps.py --city <City> --project <your-gcp-project> --insert
python3 render_hap_docx.py --city <City>
```

**Adding a new city:** add its ward-asset path to `CITY_CONFIGS` in
`chaitra_ward_pipeline.py`; everything else is city-agnostic. 13 cities are
already configured (Agra, Varanasi, Bhubaneswar, Kolkata, Surat, Lucknow,
Chennai, Jaipur, Ahmedabad, Mumbai, Hyderabad, Bangalore, Delhi) — most are
untested end-to-end.

## Repository Layout

Source (edit these):
- `chaitra_ward_pipeline.py` — the pipeline: Python port of CHAITRA's
  computation methods. Produces ward CSV + city stats JSON for any city.
- `assemble_hap_prompt.py` — builds the grounding data block + full LLM
  prompt from pipeline outputs (rankings/aggregates pre-computed in code,
  so the LLM only narrates, never calculates)
- `generate_hap.py` — one-command orchestrator: pipeline → prompt →
  Claude API draft (web search on by default) → verification (one
  corrective retry) → maps → Word doc. Requires `ANTHROPIC_API_KEY`.
- `render_hap_docx.py` — converts the verified working draft to the
  reader-facing Word doc: substitutes `[EARLY_WARNING_TEMPLATE]` with the
  fixed IMD-aligned block in `hap_early_warning_template.md` (identical for
  every city), normalizes list formatting so bullets can't silently merge
  in the render, converts `[VERIFY: …]` → trailing `*` (legend appended)
  and `[BLANK: …]` → "To be completed by city officials — …", then pandoc,
  then adds gridlines + header shading to every table via python-docx.
- `hap_early_warning_template.md` — the standard IMD four-colour heat
  alert scheme + activation protocol, identical across every HAP; only
  local numeric thresholds and contact names are left as fill-ins (these
  genuinely vary by district under IMD's system).
- `make_hap_maps.py` — renders the 7 CHAITRA layers as ward-choropleth
  PNGs (ward polygons from the GEE asset, colors from the pipeline CSV —
  fully deterministic, no LLM involvement) and inserts them at the draft's
  `[MAP: ...]` placeholders. Auto-regenerates if the ward CSV is newer than
  a saved map. Needs Earth Engine access, not the Anthropic key.
- `verify_hap_numbers.py` — checks every number in a draft against the
  data file the LLM was given; exits nonzero on any ungrounded number.
  Numbers inside `[VERIFY: …]`, `[BLANK: …]`, and `[MAP: …]` spans are
  exempt (Tier B facts awaiting human confirmation) — an unmarked outside
  number still fails, which mechanically enforces the marking rule.
- `chaitra_hap_prompt_template.md` — the LLM rulebook: two-tier grounding
  rules (Tier A: CHAITRA numbers copied exactly; Tier B: city/policy
  context, every fact `[VERIFY]`-marked for human confirmation, and
  time-sensitive facts like disaster-notification status must always be
  freshly researched, never answered from memory), mandatory caution
  notices, 12-section structure modelled on the MHT/NRDC Churu HAP. This
  is the file to edit to change what a HAP contains; the assembler reads
  it every run.
- `CHAITRA code copy.js` — full source of the chaitra.info GEE App
  (read-only reference; do not edit)
- `chaitra_code_findings.md` — technical deep-dive on the source code:
  asset paths, export schema, resource-planning formulas, and bugs found
  (with fixes) while porting it to Python.

Generated (regenerable from the source files above — safe to delete):
- `outputs/<city>_ward_data.csv`, `<city>_city_stats.json` — pipeline data
- `outputs/<city>_hap_data.md`, `<city>_hap_prompt.md` — assembled prompt
- `outputs/<city>_hap_draft.md` — verified working draft (machine markup)
- `outputs/<city>_hap_render.md`, `<City>_HAP_Draft.docx` — reader-facing output
- `outputs/maps/<city>_<layer>.png` — the 7 rendered ward maps

Archive:
- `archive/agra_demo_data.md` — original fabricated test data from before
  real pipeline output existed; kept for provenance only.

## CHAITRA's 7 Output Layers

Quick orientation — see `chaitra_code_findings.md` for exact formulas and
constants:

1. **Composite Heat Risk Index** — IPCC AR6 framework, Risk = (Hazard ×
   Exposure × Vulnerability)^(1/3). The headline ranking.
2. **Surface Temperature Hotspots** — daytime LST deviation from city mean.
3. **24-Hour Heat Zones** — day + night heat combined with population and
   nighttime commercial activity.
4. **Population Heat Risk** — heat hazard weighted by resident population.
5. **Dense / Vulnerable Housing** — built density + vegetation deficit +
   nightlight dimness; a satellite proxy for informal settlement.
6. **Cool Roof Opportunity** — temperature + built fraction + roof-albedo
   deficit; includes dark-roof area and coating cost estimates.
7. **Tree Planting Priority** — canopy deficit from a 20% target + exposed
   population + heat intensity; includes hectares, sapling counts, and cost.

All High/Medium/Low classifications use city-specific percentiles, not
fixed thresholds — a "High" ward in one city is not comparable in absolute
terms to a "High" ward in another.

## Known Limitations / Open Questions

- Only Agra and Varanasi have been run end-to-end and reviewed; the other
  11 configured cities are untested (different ward-asset schemas are
  likely — see the `has_census` / column-skipping handling in
  `chaitra_ward_pipeline.py` for how Varanasi's schema differences were
  handled).
- `chaitra_code_findings.md` §7–8 document two bugs found and fixed in
  CHAITRA's own source formulas (canopy-deficit inflation, ward-number
  field selection) while porting it to Python — worth reporting upstream.
