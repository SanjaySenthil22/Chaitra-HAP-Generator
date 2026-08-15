"""
HAP Prompt Assembly
===================
Takes the ward CSV + city stats JSON produced by chaitra_ward_pipeline.py and
builds the grounding data block + full LLM prompt for HAP generation, using
chaitra_hap_prompt_template.md.

Design principle: the LLM must never calculate. So everything the HAP needs —
rankings, high-priority-ward aggregates, classification counts — is computed
HERE (deterministic code) and handed to the LLM as citable facts.

Usage:
    python3 assemble_hap_prompt.py --city Agra
Outputs:
    <city>_hap_data.md    — the WARD DATA block (also used by the verifier)
    <city>_hap_prompt.md  — full prompt: template + ward data
"""

import argparse
import csv
import json
import math


def f(row, col, nd=1, default='NA'):
    """Format a numeric cell with fixed decimals; NaN/missing -> NA."""
    try:
        v = float(row[col])
        if math.isnan(v):
            return default
        return f'{v:,.{nd}f}' if nd else f'{v:,.0f}'
    except (KeyError, ValueError, TypeError):
        return default


def num(row, col, default=0.0):
    try:
        v = float(row[col])
        return default if math.isnan(v) else v
    except (KeyError, ValueError, TypeError):
        return default


def rupee(lakhs):
    """Format a ₹-lakh amount for readability: crore above 1 crore (100
    lakh), lakh below. Computed once here so the LLM only ever cites the
    pre-formatted figure — never converts lakh<->crore itself."""
    try:
        v = float(lakhs)
    except (TypeError, ValueError):
        return 'NA'
    if math.isnan(v):
        return 'NA'
    if abs(v) >= 100:
        return f'₹{v / 100:,.2f} crore'
    return f'₹{v:,.1f} lakh'


def build_data_block(city, rows, stats):
    ranked = sorted(rows, key=lambda r: -num(r, 'riskIndex'))
    out = []
    w = out.append

    w(f'## WARD DATA FOR {city.upper()}')
    w('')
    w('Source: CHAITRA methodology (chaitra.info) computed via Google Earth')
    w(f'Engine. Analysis window: {stats["analysis_window"]}.')
    w('All classifications are city-specific percentiles. All numbers below were')
    w('computed by the pipeline — cite them exactly as written; do not derive new ones.')
    w('')

    # ── City-wide context ──
    p = stats['LST_percentiles']
    exc = stats['exceedance_area_km2_above_C']
    w('### City-wide heat context')
    w(f'- Total wards: {len(rows)}')
    w(f'- City area (union of wards): {stats["area_km2"]:,.1f} km²')
    w(f'- City mean daytime land surface temperature (LST, summer): {stats["cityMeanLST_C"]:.1f} °C')
    w(f'- City LST percentiles (°C): median {p["LST_p50"]:.1f}, P90 {p["LST_p90"]:.1f}, '
      f'P95 {p["LST_p95"]:.1f}, P99 {p["LST_p99"]:.1f}')
    w(f'- City mean nighttime LST (MODIS): {stats["cityMeanNightLST_C"]:.1f} °C')
    w(f'- Cool vegetation reference temperature (SUHI baseline): {stats["coolReference_C"]:.1f} °C')
    w(f'- Area above 40 °C: {float(exc["40"]):,.1f} km²; above 45 °C: '
      f'{float(exc["45"]):,.1f} km²; above 50 °C: {float(exc["50"]):,.1f} km²')
    w(f'- City mean albedo: {stats["cityMeanAlbedo"]:.3f}; city mean rooftop albedo: '
      f'{stats["cityMeanRoofAlbedo"]:.3f}')
    w('')

    # ── Priority counts + aggregates over High wards (computed here, citable) ──
    def count_levels(col):
        c = {'High': 0, 'Medium': 0, 'Low': 0}
        for r in rows:
            if r.get(col) in c:
                c[r[col]] += 1
        return c

    layers = [
        ('Composite Heat Risk Index', 'priority_level'),
        ('Population Heat Risk', 'pop_priority_level'),
        ('Cool Roof Priority', 'coolroof_priority_level'),
        ('Tree Planting Priority', 'tree_priority_level'),
        ('24-Hour Heat Zones', 'activity_priority_level'),
        ('Dense/Vulnerable Housing', 'informal_priority_level'),
    ]
    w('### Ward classification counts (High / Medium / Low)')
    for name, col in layers:
        c = count_levels(col)
        w(f'- {name}: {c["High"]} High / {c["Medium"]} Medium / {c["Low"]} Low')
    w('')

    high_risk = [r for r in rows if r.get('priority_level') == 'High']
    high_pop = sum(num(r, 'totalPop') for r in high_risk)
    high_roof = [r for r in rows if r.get('coolroof_priority_level') == 'High']
    roof_area = sum(num(r, 'darkRoofArea_km2') for r in high_roof)
    roof_cost = sum(num(r, 'estimatedCost_Lakhs') for r in high_roof)
    high_tree = [r for r in rows if r.get('tree_priority_level') == 'High']
    saplings = sum(num(r, 'saplingsToPlant') for r in high_tree)
    tree_cost = sum(num(r, 'totalCost_Lakhs') for r in high_tree)
    tree_deficit = sum(num(r, 'canopyDeficit_ha') for r in high_tree)

    w('### City-wide aggregates for High-priority wards (pre-computed)')
    w(f'- Population living in High composite-risk wards: {high_pop:,.0f} '
      f'(modelled estimate, WorldPop 2020)')
    w(f'- High cool-roof-priority wards: dark roof area needing treatment '
      f'{roof_area * 100:,.0f} ha; estimated coating cost {rupee(roof_cost)} '
      f'(₹150-230/m², midpoint ₹190/m²)')
    w(f'- High tree-priority wards: canopy deficit {tree_deficit:,.0f} ha; '
      f'saplings to plant {saplings:,.0f} (150 trees/ha of deficit, ×1.35 '
      f'mortality buffer); estimated cost {rupee(tree_cost)} (₹1,400/tree '
      f'incl. 3-yr maintenance)')
    w('')

    # ── Table 1: composite risk ranking ──
    # Ward numbers only — no ward-name identifier strings, no population
    # columns (WorldPop and Census 2011 disagree; both removed per review).
    w('### Table 1 — Composite Heat Risk Index ranking (all wards, highest risk first)')
    w('Rank computed by the pipeline. riskIndex = (Hazard × Exposure × Vulnerability)^(1/3), IPCC AR6.')
    w('(Risk Index is for grounding/traceability; HAP output tables show Rank | Ward No. | Priority only.)')
    w('')
    w('| Rank | Ward No. | Risk Index | Priority |')
    w('|---|---|---|---|')
    for i, r in enumerate(ranked, 1):
        w(f'| {i} | {r["WARD_NO"]} | {f(r, "riskIndex", 2)} | {r["priority_level"]} |')
    w('')

    # ── Table 2: heat hazard ──
    w('### Table 2 — Heat hazard per ward (daytime + nighttime)')
    w('LST dev = ward mean LST deviation from city mean (°C). Night dev = MODIS')
    w('nighttime deviation from city mean (°C). 24h score combines day/night heat,')
    w('population and nightlight activity (0-100 scale, geometric mean; values can exceed 100).')
    w('')
    w('| Ward | LST mean °C | LST dev °C | Night dev °C | Day LST °C (MODIS) | Night LST °C (MODIS) | 24h Heat Score | 24h Class |')
    w('|---|---|---|---|---|---|---|---|')
    for r in ranked:
        w(f'| {r["WARD_NO"]} | {f(r, "LST_mean")} | {f(r, "LST_hotspot")} | '
          f'{f(r, "nighttemp_hotspot")} | {f(r, "dayLST")} | {f(r, "nightLST")} | '
          f'{f(r, "activityHeatScore")} | {r["activity_priority_level"]} |')
    w('')

    # ── Table 3: exposure & vulnerability ──
    # No per-ward population or Census 2011 columns (removed per review —
    # population still feeds the scores, it just isn't printed per ward).
    w('### Table 3 — Exposure and vulnerability per ward')
    w('Housing = Dense/Vulnerable Housing score (0-100). PopRisk = Population Heat')
    w('Risk score. Canopy = current tree canopy in built-up areas (%). NDVI = vegetation index.')
    w('')
    w('| Ward No. | Housing Score | Housing Class | PopRisk Score | PopRisk Class | Canopy % | NDVI |')
    w('|' + '---|' * 7)
    for r in ranked:
        w(f'| {r["WARD_NO"]} | {f(r, "informalHousingScore")} | '
          f'{r["informal_priority_level"]} | {f(r, "riskScore")} | '
          f'{r["pop_priority_level"]} | {f(r, "currentCanopy_pct", 2)} | '
          f'{f(r, "ndvi_mean", 2)} |')
    w('')

    # ── Table 4: interventions ──
    # Dark roof area in HECTARES (km² values read as unhelpful decimals in
    # review). Priority scores kept for grounding only — HAP output tables
    # show class + quantities, never the scores.
    w('### Table 4 — Intervention quantities per ward (cool roofs + tree planting)')
    w('CoolRoof score NA = ward ineligible/insufficient data (classified Low).')
    w('Costs shown as ₹ lakh below ₹1 crore, ₹ crore at or above (pre-formatted — cite as written).')
    w('Dark roof area in hectares (roof albedo < 0.20).')
    w('(Scores are for grounding/traceability; HAP output tables show class and quantities only.)')
    w('')
    w('| Ward No. | CoolRoof Score | CoolRoof Class | Dark Roof ha | Roof Cost | Tree Score | Tree Class | Canopy Deficit ha | Saplings | Tree Cost |')
    w('|' + '---|' * 10)
    for r in ranked:
        roof_ha = num(r, 'darkRoofArea_km2') * 100
        w(f'| {r["WARD_NO"]} | {f(r, "coolRoofPriorityScore")} | {r["coolroof_priority_level"]} | '
          f'{roof_ha:,.1f} | {rupee(num(r, "estimatedCost_Lakhs"))} | '
          f'{f(r, "treePriorityScore")} | {r["tree_priority_level"]} | '
          f'{f(r, "canopyDeficit_ha")} | {f(r, "saplingsToPlant", 0)} | '
          f'{rupee(num(r, "totalCost_Lakhs"))} |')
    w('')

    # ── Methodology notes for the appendix ──
    w('### Data sources and methodology (for Appendix)')
    w('- Ward boundaries: municipal ward shapefile as hosted in CHAITRA (GEE asset)')
    w('- Daytime LST: Landsat 8/9 Collection 2 L2 thermal, 30 m, summer (Apr-Jul) '
      'median composite, cloud-masked')
    w('- Nighttime LST: MODIS Terra+Aqua (MOD11A1/MYD11A1), 1 km, 2-year median')
    w('- Population: WorldPop 100 m, 2020 (model input for risk scores; not '
      'printed per ward — to be reconciled with municipal records)')
    w('- Land cover: ESA WorldCover v200 (2021), 10 m; canopy: Google Dynamic World, 10 m')
    w('- Albedo: Sentinel-2 broadband albedo (Liang 2001 coefficients), 10 m')
    w('- Housing vulnerability: GHSL Built Surface 2020 density + vegetation deficit '
      '+ VIIRS nightlight dimness, geometric mean, P5-P95 normalized')
    w('- Composite risk: IPCC AR6 framework, Risk = (H × E × V)^(1/3); H = day + '
      'night heat hotspot scores, E = ln(population+1), V = canopy deficit + '
      'housing density + albedo deficit; classified by city percentiles (P50/P70)')
    w('- Cool roof costing: ₹150-230/m² (GRIHA 2021 / GEDA 2022-23), midpoint ₹190/m²')
    w('- Tree costing: 150 trees/ha of canopy deficit, ×1.35 mortality buffer, '
      '₹1,400/tree including 3-year maintenance (CHAITRA layer constants)')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='Agra')
    args = ap.parse_args()
    city = args.city
    slug = city.lower()

    import os
    os.makedirs('outputs', exist_ok=True)
    rows = list(csv.DictReader(open(f'outputs/{slug}_ward_data.csv')))
    stats = json.load(open(f'outputs/{slug}_city_stats.json'))
    template = open('chaitra_hap_prompt_template.md').read()

    data_block = build_data_block(city, rows, stats)
    with open(f'outputs/{slug}_hap_data.md', 'w') as fh:
        fh.write(data_block)

    prompt = template.replace('[CITY NAME]', city)
    prompt = prompt.replace(
        '## WARD DATA FOR ' + city + '\n[Insert exported Chaitra data here — per ward: population, composite index + classification, surface temp deviation, housing vulnerability score, cool roof priority + cost estimate, tree planting priority + sapling count + cost, 24-hour heat zone score]',
        data_block)
    # Fallback if template placeholder text differs
    if data_block not in prompt:
        marker = f'## WARD DATA FOR {city}'
        idx = prompt.find(marker)
        if idx >= 0:
            end = prompt.find('\n---', idx)
            prompt = prompt[:idx] + data_block + prompt[end:]
        else:
            prompt += '\n\n' + data_block

    with open(f'outputs/{slug}_hap_prompt.md', 'w') as fh:
        fh.write(prompt)
    print(f'wrote outputs/{slug}_hap_data.md ({len(data_block):,} chars) '
          f'and outputs/{slug}_hap_prompt.md')


if __name__ == '__main__':
    main()
