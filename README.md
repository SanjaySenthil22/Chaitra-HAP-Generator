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

`Agra` is just an example — any of the 13 configured cities works the same
way (see Usage below). Produces `outputs/Agra_HAP_Draft.docx`. See **Setup**
below for what `<your-gcp-project>` needs and how to get ward-asset access.

## Setup

**Python packages** — `pip3 install -r requirements.txt` (earthengine-api,
anthropic, matplotlib, python-docx).

**pandoc** — converts the drafted markdown to `.docx`. Not a Python package;
install via `brew install pandoc` (macOS) or your system's package manager.

**Google Earth Engine** — the ward-level computation runs on GEE, and needs
two things, which are separate:
1. **A GCP project with the Earth Engine API enabled**, authenticated
   locally via `earthengine authenticate` (one-time, opens a browser). This
   is the compute identity that runs every `--project <id>` command below —
   any lab member can set up their own. To skip typing `--project` every
   run, set it once:
   ```bash
   export CHAITRA_GEE_PROJECT=<your-gcp-project-id>   # add to ~/.zshrc to persist
   ```
   (every script's `--project` flag falls back to this env var — see e.g.
   `chaitra_ward_pipeline.py` line 1324).
2. **Read access to the ward-boundary assets**, which live in CHAITRA's own
   GCP project (`projects/gee-piyushn44/assets/...`, see `CITY_CONFIGS` in
   `chaitra_ward_pipeline.py`, line 39). Request read access from the
   CHAITRA project lead for the Google account authenticated above. The
   compute project and the data project don't need to be the same one.

**Anthropic API key** — required only for the LLM drafting step
(`generate_hap.py`, or any run using web search). Get one at
[console.anthropic.com](https://console.anthropic.com) (pay-as-you-go, no
subscription):
```bash
export ANTHROPIC_API_KEY=sk-ant-...   # add to ~/.zshrc to persist
```
Cost is roughly $0.50–1.00 per city per run (Opus-tier tokens + a handful
of web searches for local context facts). Without a key, everything except
the drafting step still works — assemble the grounding data and prompt,
then draft by hand or paste the prompt into claude.ai.

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
```

**Without an Anthropic key**, replace `generate_hap.py`'s drafting step with
a manual one instead of running the full pipeline:
1. Open `outputs/<city>_hap_prompt.md` and copy its full contents.
2. Paste it as a single message into [claude.ai](https://claude.ai) (or any
   other capable chat LLM).
3. Copy the reply back out — the document only, no "Here's your HAP:"
   preamble or code-fence wrapper around it — and save it as
   `outputs/<city>_hap_draft.md`.

Then continue the pipeline as normal:
```bash
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
