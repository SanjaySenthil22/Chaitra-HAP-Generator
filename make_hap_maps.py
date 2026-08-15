"""
HAP Map Rendering
=================
Renders the 7 CHAITRA output layers as ward-choropleth PNGs (like the figure
maps in the MHT/NRDC Churu HAP) and inserts them at the [MAP: ...]
placeholders in a drafted HAP.

Ward polygons come from the same GEE ward asset the pipeline uses (no
dashboard, no API key — only the authenticated earthengine account). Ward
colors come from outputs/<city>_ward_data.csv, so the maps show exactly the
classifications the text cites.

Usage:
    python3 make_hap_maps.py --city Agra --project <your-gcp-project>
    python3 make_hap_maps.py --city Agra --insert   # also patch the draft
Outputs:
    outputs/maps/<slug>_<layer>.png   (7 files)
    outputs/<slug>_hap_draft.md       (placeholders replaced, with --insert)
"""

import argparse
import csv
import math
import os
import re
import sys

# (key, draft placeholder title, class column, score column)
LAYERS = [
    ('composite',   'Composite Heat Risk Index',    'priority_level',          'riskIndex'),
    ('lst_hotspot', 'Surface Temperature Hotspots', None,                      'LST_hotspot'),
    ('heat24',      '24-Hour Heat Zones',           'activity_priority_level', 'activityHeatScore'),
    ('poprisk',     'Population Heat Risk',         'pop_priority_level',      'riskScore'),
    ('housing',     'Dense / Vulnerable Housing',   'informal_priority_level', 'informalHousingScore'),
    ('coolroof',    'Cool Roof Opportunity',        'coolroof_priority_level', 'coolRoofPriorityScore'),
    ('tree',        'Tree Planting Priority',       'tree_priority_level',     'treePriorityScore'),
]

CLASS_COLORS = {'High': '#d7191c', 'Medium': '#fdae61', 'Low': '#a6d96a'}
MISSING_COLOR = '#cccccc'


def fetch_ward_geometries(city, project):
    import ee
    from chaitra_ward_pipeline import load_boundaries
    ee.Initialize(project=project)
    wards, _cfg = load_boundaries(city)
    fc = wards.getInfo()
    out = {}
    for feat in fc['features']:
        ward_no = int(feat['properties']['WARD_NO'])
        geom = feat['geometry']
        if geom['type'] == 'Polygon':
            polys = [geom['coordinates']]
        elif geom['type'] == 'MultiPolygon':
            polys = geom['coordinates']
        else:
            continue
        out[ward_no] = polys
    return out


def ward_values(slug):
    rows = list(csv.DictReader(open(f'outputs/{slug}_ward_data.csv')))
    return {int(float(r['WARD_NO'])): r for r in rows}


def _paths(polys):
    """Build one matplotlib Path per polygon (exterior + hole rings)."""
    from matplotlib.path import Path
    for rings in polys:
        verts, codes = [], []
        for ring in rings:
            verts.extend(ring)
            codes.extend([Path.MOVETO] + [Path.LINETO] * (len(ring) - 2)
                         + [Path.CLOSEPOLY])
        yield Path(verts, codes)


def _centroid(polys):
    ring = max((r[0] for r in polys), key=len)
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def render_layer(geoms, values, key, title, class_col, score_col, city, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch, Patch
    from matplotlib import colormaps
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.cm import ScalarMappable

    fig, ax = plt.subplots(figsize=(9, 9))
    continuous = class_col is None
    cmap = colormaps['RdYlBu_r'] if continuous else None
    norm = None
    if continuous:
        vals = []
        for r in values.values():
            try:
                v = float(r[score_col])
                if not math.isnan(v):
                    vals.append(v)
            except (ValueError, TypeError):
                pass
        lim = max(abs(min(vals)), abs(max(vals))) or 1.0
        norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)

    for ward_no, polys in geoms.items():
        r = values.get(ward_no)
        color = MISSING_COLOR
        if r is not None:
            if continuous:
                try:
                    v = float(r[score_col])
                    if not math.isnan(v):
                        color = cmap(norm(v))
                except (ValueError, TypeError):
                    pass
            else:
                color = CLASS_COLORS.get(r.get(class_col, ''), MISSING_COLOR)
        for p in _paths(polys):
            ax.add_patch(PathPatch(p, facecolor=color, edgecolor='#555555',
                                   linewidth=0.4))
        cx, cy = _centroid(polys)
        ax.text(cx, cy, str(ward_no), fontsize=4.5, ha='center', va='center',
                color='#222222')

    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.set_axis_off()
    ax.set_title(f'{title} — {city} (CHAITRA, ward level)', fontsize=13)
    if continuous:
        cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                          fraction=0.04, pad=0.02)
        cb.set_label('LST deviation from city mean (°C)')
    else:
        ax.legend(handles=[Patch(facecolor=c, edgecolor='#555555', label=l)
                           for l, c in CLASS_COLORS.items()],
                  loc='lower right', title='Priority (city-relative)')
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)


def insert_maps(slug, city):
    draft_path = f'outputs/{slug}_hap_draft.md'
    text = open(draft_path).read()
    replaced = 0
    for key, title, _cc, _sc in LAYERS:
        png = f'outputs/maps/{slug}_{key}.png'
        if not os.path.exists(png):
            continue
        # image path relative to the draft file, so IDE preview and
        # pandoc --resource-path=outputs both resolve it
        img = (f'![{title} — {city}](maps/{slug}_{key}.png)\n\n'
               f'*Figure: {title}, ward-level map generated from the CHAITRA '
               f'analysis. Classifications are relative to {city}\'s own '
               f'distribution.*')
        pattern = re.compile(r'^\[MAP: ' + re.escape(title) + r' —[^\]]*\]$',
                             re.MULTILINE)
        text, n = pattern.subn(img, text)
        replaced += n
    open(draft_path, 'w').write(text)
    print(f'inserted {replaced} maps into {draft_path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='Agra')
    ap.add_argument('--project', default=os.environ.get('CHAITRA_GEE_PROJECT'),
                    help='GCP project with Earth Engine enabled (or set '
                         'CHAITRA_GEE_PROJECT)')
    ap.add_argument('--insert', action='store_true',
                    help='replace [MAP: ...] placeholders in the draft')
    ap.add_argument('--force', action='store_true',
                    help='re-render PNGs even if they exist')
    args = ap.parse_args()
    city, slug = args.city, args.city.lower()

    csv_path = f'outputs/{slug}_ward_data.csv'
    os.makedirs('outputs/maps', exist_ok=True)
    csv_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0

    def _stale(png):
        return not os.path.exists(png) or os.path.getmtime(png) < csv_mtime

    todo = [l for l in LAYERS if args.force or
            _stale(f'outputs/maps/{slug}_{l[0]}.png')]
    if todo and not args.force:
        print(f'{len(todo)} map(s) missing or older than {csv_path} — '
              f'(re)rendering to stay in sync with the current ward data')
    if todo:
        if not args.project:
            sys.exit('No GCP project given: pass --project <your-gcp-project> '
                      'or set CHAITRA_GEE_PROJECT (needs Earth Engine enabled '
                      'and read access to the ward asset — see README).')
        print(f'fetching ward geometries for {city} from GEE...')
        geoms = fetch_ward_geometries(city, args.project)
        values = ward_values(slug)
        missing = sorted(set(geoms) - set(values))
        if missing:
            print(f'note: {len(missing)} wards lack CSV rows: {missing}',
                  file=sys.stderr)
        for key, title, cc, sc in todo:
            path = f'outputs/maps/{slug}_{key}.png'
            render_layer(geoms, values, key, title, cc, sc, city, path)
            print('wrote', path)
    else:
        print('all PNGs present (use --force to re-render)')

    if args.insert:
        insert_maps(slug, city)


if __name__ == '__main__':
    main()
