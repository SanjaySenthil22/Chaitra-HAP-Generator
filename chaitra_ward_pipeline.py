"""
CHAITRA Ward Data Pipeline
==========================
Python port of the computation methods in chaitra.info's GEE App source
(`CHAITRA code copy.js`). Produces the real ward-level CSV that feeds the
Heat Action Plan (HAP) generator.

Faithful to the JS source: same datasets, same formulas, same percentile
normalizations, same constants. Line references in comments point to the JS.

Improvements over the JS export path (documented in chaitra_code_findings.md):
  - Joins heatRiskWards + informalHousingWards into the export (the JS export
    omits them, leaving riskIndex/informalHousingScore blank)
  - Per-layer priority levels exported under distinct column names
    (the JS export's single `priority_level` was whichever join came last)
  - Includes key Census 2011 ward attributes carried by the ward asset

Usage:
    python3 chaitra_ward_pipeline.py --city Agra --project <gcp-project> \
        [--out agra_ward_data.csv] [--citystats agra_city_stats.json]
"""

import argparse
import json
import os
import time
import urllib.parse
import urllib.request

import ee

# ───────────────────────────────────────────────────────────────────────────────
# CONFIG (JS lines 13-16, 37-155)
# ───────────────────────────────────────────────────────────────────────────────

START_DATE = '2022-04-01'
END_DATE = '2024-07-31'

CITY_CONFIGS = {
    'Varanasi':    {'assetPath': 'projects/gee-piyushn44/assets/Varanasi_Ward_Map', 'utmZone': 'EPSG:32644', 'areaKm2': 82},
    'Bhubaneswar': {'assetPath': 'projects/gee-piyushn44/assets/Bhubneshwar_Ward_BND', 'utmZone': 'EPSG:32645', 'areaKm2': 135},
    'Agra':        {'assetPath': 'projects/gee-piyushn44/assets/Agra_Wards', 'utmZone': 'EPSG:32643', 'areaKm2': 188},
    'Kolkata':     {'assetPath': 'projects/gee-piyushn44/assets/Kolkata_Ward_Map', 'utmZone': 'EPSG:32645', 'areaKm2': 205},
    'Surat':       {'assetPath': 'projects/gee-piyushn44/assets/Surat_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 327},
    'Lucknow':     {'assetPath': 'projects/gee-piyushn44/assets/Lucknow_Ward_Map', 'utmZone': 'EPSG:32644', 'areaKm2': 349},
    'Chennai':     {'assetPath': 'projects/gee-piyushn44/assets/Chennai_Ward_Map', 'utmZone': 'EPSG:32644', 'areaKm2': 426},
    'Jaipur':      {'assetPath': 'projects/gee-piyushn44/assets/Jaipur_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 485},
    'Ahmedabad':   {'assetPath': 'projects/gee-piyushn44/assets/Ahmedabad_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 505},
    'Mumbai':      {'assetPath': 'projects/gee-piyushn44/assets/Mumbai_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 603},
    'Hyderabad':   {'assetPath': 'projects/gee-piyushn44/assets/Hyderabad_Ward_Map', 'utmZone': 'EPSG:32644', 'areaKm2': 650},
    'Bangalore':   {'assetPath': 'projects/gee-piyushn44/assets/Bangalorewardmap', 'utmZone': 'EPSG:32643', 'areaKm2': 741},
    'Delhi':       {'assetPath': 'projects/gee-piyushn44/assets/Delhi_Ward_Map', 'utmZone': 'EPSG:32643', 'areaKm2': 1484},
}

CITY_STATE = {
    'Varanasi': 'Uttar Pradesh', 'Bhubaneswar': 'Odisha', 'Agra': 'Uttar Pradesh',
    'Kolkata': 'West Bengal', 'Surat': 'Gujarat', 'Lucknow': 'Uttar Pradesh',
    'Chennai': 'Tamil Nadu', 'Jaipur': 'Rajasthan', 'Ahmedabad': 'Gujarat',
    'Mumbai': 'Maharashtra', 'Hyderabad': 'Telangana', 'Bangalore': 'Karnataka',
    'Delhi': 'Delhi',
}

SCALES = {'lst': 30, 'ndvi': 30, 'population': 100, 'lulc': 10, 'night': 500}

CORE_LANDSAT_BANDS = [
    'SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7',
    'ST_B10', 'QA_PIXEL', 'ST_QA',
]

# Census 2011 attributes on the ward asset worth carrying into the HAP
CENSUS_COLUMNS = [
    'tot_p', 'tot_m', 'tot_f', 'p_06', 'no_hh', 'sexratio',
    'p_lit', 'p_ill', 'p_sc', 'p_st',
    'tot_work_p', 'mainwork_p', 'margwork_p', 'non_work_p',
]


# ───────────────────────────────────────────────────────────────────────────────
# NULL-SAFE HELPERS (JS lines 888-1401)
# ───────────────────────────────────────────────────────────────────────────────

def get_number(f, prop, default):
    """JS getNumber: null-safe feature property as ee.Number."""
    return ee.Number(ee.Algorithms.If(
        ee.Algorithms.IsEqual(f.get(prop), None), default, f.get(prop)))


def safe_dict_number(d, key, default):
    """JS safeDictNumber: null-safe dictionary value as ee.Number."""
    d = ee.Dictionary(d)
    v = d.get(key, default)
    return ee.Number(ee.Algorithms.If(ee.Algorithms.IsEqual(v, None), default, v))


def normalize_by_percentiles(value, p5, p95):
    """JS normalizeByPercentiles (line 1487)."""
    rng = ee.Number(p95).subtract(ee.Number(p5)).max(0.01)
    return ee.Number(value).subtract(ee.Number(p5)).divide(rng).clamp(0, 1)


def join_ward_results(base, results, join_key='WARD_NO', match_key='_m'):
    """JS joinWardResults (line 1502): outer saveFirst join, copy all props."""
    flt = ee.Filter.equals(leftField=join_key, rightField=join_key)
    joined = ee.Join.saveFirst(matchKey=match_key, outer=True).apply(base, results, flt)

    def _copy(f):
        matched = ee.Feature(f.get(match_key))
        props = ee.Algorithms.If(
            ee.Algorithms.IsEqual(matched, None), {}, matched.toDictionary())
        return ee.Feature(f).setMulti(props)

    return ee.FeatureCollection(joined.map(_copy))


def add_priority_by_percentiles(fc, prop, p_med, p_high):
    """JS addPriorityByPercentiles (line 1444): drops null wards."""
    fc = ee.FeatureCollection(fc).filter(ee.Filter.notNull([prop]))
    pct = ee.Dictionary(fc.reduceColumns(
        ee.Reducer.percentile([p_med, p_high]).setOutputs(['pMed', 'pHigh']), [prop]))
    t_med = safe_dict_number(pct, 'pMed', 0)
    t_high = safe_dict_number(pct, 'pHigh', 0)

    def _cls(f):
        v = get_number(f, prop, 0)
        level = ee.Algorithms.If(
            v.gte(t_high), 'High', ee.Algorithms.If(v.gte(t_med), 'Medium', 'Low'))
        return f.set({'priority_level': level, 'priority_score': v})

    return fc.map(_cls)


def add_priority_by_percentiles_keep_all(fc, prop, p_med, p_high):
    """JS addPriorityByPercentilesKeepAll (line 1529)."""
    fc = ee.FeatureCollection(fc)
    valid = fc.filter(ee.Filter.notNull([prop]))
    pct = ee.Dictionary(valid.reduceColumns(
        ee.Reducer.percentile([p_med, p_high]).setOutputs(['pMed', 'pHigh']), [prop]))
    t_med = safe_dict_number(pct, 'pMed', 0)
    t_high = safe_dict_number(pct, 'pHigh', 0)

    def _cls(f):
        is_null = ee.Algorithms.IsEqual(f.get(prop), None)
        v = ee.Number(ee.Algorithms.If(is_null, 0, f.get(prop)))
        level = ee.Algorithms.If(
            is_null, 'Low',
            ee.Algorithms.If(v.gte(t_high), 'High',
                             ee.Algorithms.If(v.gte(t_med), 'Medium', 'Low')))
        return f.set({'priority_level': level, 'priority_score': v})

    return fc.map(_cls)


def aggregate_image(img, src_scale, target_scale, reducer='mean', max_pixels=4096):
    """JS aggregateImage (line 3267)."""
    reducers = {'mean': ee.Reducer.mean(), 'max': ee.Reducer.max(),
                'min': ee.Reducer.min(), 'median': ee.Reducer.median()}
    src_proj = ee.Projection('EPSG:4326').atScale(src_scale)
    target_proj = ee.Projection('EPSG:4326').atScale(target_scale)
    return (img.setDefaultProjection(src_proj)
            .reduceResolution(reducer=reducers[reducer], maxPixels=max_pixels)
            .reproject(target_proj))


# ───────────────────────────────────────────────────────────────────────────────
# BOUNDARIES (JS loadBoundaries, line 1959)
# ───────────────────────────────────────────────────────────────────────────────

def load_boundaries(city):
    cfg = CITY_CONFIGS[city]
    wards = ee.FeatureCollection(cfg['assetPath'])

    def _standardize(f):
        names = f.propertyNames()
        # Prefer true municipal ward numbers over administrative codes.
        # 'sourcewa_1' (Varanasi asset) is the municipal ward number paired
        # with the ward name; 'ward_lgd_c' is a 5-digit LGD code (26xxx) that
        # reviewers flagged as NOT being a ward number — keep it only as a
        # last-resort fallback.
        ward_no_raw = ee.Algorithms.If(
            names.contains('WARD_NO'), f.get('WARD_NO'),
            ee.Algorithms.If(
                names.contains('ward_no'), f.get('ward_no'),
                ee.Algorithms.If(
                    names.contains('sourcewa_1'), f.get('sourcewa_1'),
                    ee.Algorithms.If(
                        names.contains('NNVNS'), f.get('NNVNS'),
                        ee.Algorithms.If(
                            names.contains('ward_lgd_c'), f.get('ward_lgd_c'),
                            ee.Algorithms.If(names.contains('id'), f.get('id'),
                                             f.get('system:index')))))))
        ward_no_str = ee.String(ward_no_raw)
        has_digits = ward_no_str.match('[0-9]+').length().gt(0)
        ward_no = ee.Number(ee.Algorithms.If(
            has_digits,
            ee.Number.parse(ee.String(ward_no_str.match('[0-9]+').get(0))),
            0)).int()

        ward_name = ee.String(ee.Algorithms.If(
            names.contains('ward_name'), f.get('ward_name'),
            ee.Algorithms.If(
                names.contains('WARD_NAME'), f.get('WARD_NAME'),
                ee.Algorithms.If(
                    names.contains('ward_lgd_n'), f.get('ward_lgd_n'),
                    ee.Algorithms.If(
                        names.contains('name'), f.get('name'),
                        ee.Algorithms.If(names.contains('NAME'), f.get('NAME'),
                                         ee.String('Ward ').cat(ward_no.format())))))))

        area = f.geometry().area(ee.ErrorMargin(1)).divide(1e6)  # JS line 6974
        return f.set({
            'WARD_NO': ward_no,
            'ward_name': ward_name,
            'city': city,
            'state': CITY_STATE.get(city, 'Unknown'),
            'area_km2': area,
        })

    return wards.map(_standardize), cfg


# ───────────────────────────────────────────────────────────────────────────────
# LANDSAT COMPOSITE + THERMAL (JS lines 2033-2583)
# ───────────────────────────────────────────────────────────────────────────────

def _apply_scale_factors(img):
    return (img
            .addBands(img.select('SR_B.*').multiply(0.0000275).add(-0.2), None, True)
            .addBands(img.select('ST_B.*').multiply(0.00341802).add(149.0), None, True))


def _mask_clouds(img):
    qa = img.select('QA_PIXEL')
    mask = (qa.bitwiseAnd(1 << 0).eq(0)
            .And(qa.bitwiseAnd(1 << 1).eq(0))
            .And(qa.bitwiseAnd(1 << 2).eq(0))
            .And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0))
            .And(qa.bitwiseAnd(1 << 5).eq(0)))
    band_names = img.bandNames()
    sat = ee.Image(ee.Algorithms.If(
        band_names.contains('QA_RADSAT'), img.select('QA_RADSAT').eq(0),
        ee.Image.constant(1)))
    st_unc_k = img.select('ST_QA').multiply(0.01)
    st_quality = st_unc_k.lte(5)
    cloud_dist = ee.Image(ee.Algorithms.If(
        band_names.contains('ST_CDIST'),
        img.select('ST_CDIST').multiply(0.01).gt(0.3),
        ee.Image.constant(1)))
    return (img.updateMask(mask).updateMask(sat)
            .updateMask(st_quality).updateMask(cloud_dist))


def load_landsat_composite(region, summer_filter):
    """JS loadLandsatData, Landsat C02 T1_L2 primary path (line 2321-2408)."""
    bounds = region.bounds()
    landsat = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
               .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
               .filterBounds(bounds)
               .filterDate(START_DATE, END_DATE)
               .filter(summer_filter)
               .filter(ee.Filter.lt('CLOUD_COVER', 80))
               .map(lambda img: _mask_clouds(_apply_scale_factors(img))
                    .select(CORE_LANDSAT_BANDS)))
    return landsat.median().select(CORE_LANDSAT_BANDS).clip(region)


def calculate_thermal(composite, region, water):
    """JS calculateAirTempAndNDVI (line 2429): NDVI, LST, SUHI vs cool reference."""
    ndvi = composite.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    land_mask = water.clip(region).lt(20).unmask(1)
    ndvi = ndvi.updateMask(land_mask)

    lst_raw = composite.select('ST_B10').subtract(273.15).rename('LST')
    lst = (lst_raw.updateMask(lst_raw.gt(10).And(lst_raw.lt(80)))
           .updateMask(land_mask)
           .setDefaultProjection('EPSG:4326', None, 30))

    ndvi_stats = ndvi.reduceRegion(
        reducer=ee.Reducer.percentile([80, 90]), geometry=region,
        scale=SCALES['ndvi'], crs='EPSG:4326', bestEffort=True,
        tileScale=4, maxPixels=1e13)
    ndvi_threshold = safe_dict_number(ndvi_stats, 'NDVI_p80', 0.5).max(0.30)

    cool_ref_mask = ndvi.gte(ee.Image.constant(ndvi_threshold)).And(land_mask).selfMask()
    ref_temp = lst.updateMask(cool_ref_mask).reduceRegion(
        reducer=ee.Reducer.percentile([20]), geometry=region,
        scale=SCALES['lst'], crs='EPSG:4326', bestEffort=True,
        tileScale=4, maxPixels=1e13)
    # NOTE: single-percentile reducer outputs key 'LST' (not 'LST_p20' as the
    # JS assumes — a latent bug there that silently made coolReference fall
    # back to 30°C). Check both keys, matching the JS's documented intent.
    ref_temp = ee.Dictionary(ref_temp)
    ref_cool = ee.Number(ref_temp.get('LST_p20', ref_temp.get('LST', 30)))

    uhi = lst.subtract(ee.Image.constant(ref_cool)).rename('UHI')
    return {
        'ndvi': ndvi.clip(region),
        'lst': lst.clip(region),
        'uhi': uhi.clip(region),
        'coolReference': ref_cool,
    }


def load_sentinel2_albedo(region, summer_filter):
    """JS loadSentinel2ForAlbedo (line 2129): 10m broadband albedo, Liang 2001."""
    bounds = region.bounds()

    def _albedo(img):
        qa = img.select('QA60')
        cloud_mask = (qa.bitwiseAnd(1 << 10).eq(0)
                      .And(qa.bitwiseAnd(1 << 11).eq(0)))
        scl = img.select('SCL')
        scl_mask = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
                    .And(scl.neq(10)).And(scl.neq(11)))
        blue = img.select('B2').divide(10000)
        green = img.select('B3').divide(10000)
        red = img.select('B4').divide(10000)
        nir = img.select('B8').divide(10000)
        swir2 = (img.select('B12').resample('bilinear')
                 .reproject(crs=img.select('B2').projection(), scale=10)
                 .divide(10000))
        albedo = (blue.multiply(0.356).add(green.multiply(0.130))
                  .add(red.multiply(0.373)).add(nir.multiply(0.085))
                  .add(swir2.multiply(0.072)).subtract(0.0018)
                  .clamp(0, 1).rename('albedo')
                  .setDefaultProjection(ee.Projection('EPSG:4326').atScale(10)))
        return albedo.updateMask(cloud_mask.And(scl_mask))

    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(bounds)
          .filter(summer_filter)
          .filterDate(START_DATE, END_DATE)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
          .map(_albedo))

    return (ee.Image(ee.Algorithms.If(
        s2.size().gt(0), s2.median(),
        ee.Image.constant(0.15).rename('albedo')))
        .clip(region)
        .setDefaultProjection(ee.Projection('EPSG:4326').atScale(10)))


# ───────────────────────────────────────────────────────────────────────────────
# URBAN LAYERS (JS processUrbanLayers, line 2585)
# ───────────────────────────────────────────────────────────────────────────────

def process_urban_layers(region, summer_filter, lst):
    wc_proj = ee.Projection('EPSG:4326').atScale(10)
    lulc = (ee.Image(ee.ImageCollection('ESA/WorldCover/v200').first())
            .select('Map').setDefaultProjection(wc_proj).clip(region))

    albedo = load_sentinel2_albedo(region, summer_filter)

    worldpop = (ee.Image(ee.ImageCollection('WorldPop/GP/100m/pop')
                         .filter(ee.Filter.eq('country', 'IND'))
                         .filter(ee.Filter.eq('year', 2020))
                         .first())
                .select('population').clip(region).unmask(0))

    analysis_end = ee.Date(END_DATE)
    viirs_proj = ee.Projection('EPSG:4326').atScale(463.83)
    nightlights = (ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
                   .filterBounds(region)
                   .filterDate(analysis_end.advance(-2, 'year'), analysis_end)
                   .select('avg_rad')
                   .median()
                   .setDefaultProjection(viirs_proj)
                   .clip(region).unmask(0))

    # MODIS Terra+Aqua day/night LST, 2-year window (JS line 2737-2780)
    modis_proj = ee.Projection('EPSG:4326').atScale(1000)
    modis_start = analysis_end.advance(-2, 'year')

    def _to_c(img):
        return img.multiply(0.02).subtract(273.15)

    terra = (ee.ImageCollection('MODIS/061/MOD11A1')
             .filterBounds(region).filterDate(modis_start, analysis_end))
    aqua = (ee.ImageCollection('MODIS/061/MYD11A1')
            .filterBounds(region).filterDate(modis_start, analysis_end))

    modis_day = (terra.select('LST_Day_1km').map(_to_c).median()
                 .add(aqua.select('LST_Day_1km').map(_to_c).median())
                 .divide(2).setDefaultProjection(modis_proj)
                 .clip(region).rename('MODIS_Day_LST'))
    modis_night = (terra.select('LST_Night_1km').map(_to_c).median()
                   .add(aqua.select('LST_Night_1km').map(_to_c).median())
                   .divide(2).setDefaultProjection(modis_proj)
                   .clip(region).rename('MODIS_Night_LST'))

    # Cropland exclusion at 1km (JS line 2790-2813)
    crop_frac_1km = (lulc.unmask(0).eq(40)
                     .reduceResolution(reducer=ee.Reducer.mean(), maxPixels=65536)
                     .reproject(crs=modis_proj, scale=1000))
    not_crop_1km = crop_frac_1km.lt(0.5)
    modis_day = modis_day.updateMask(not_crop_1km)
    modis_night = modis_night.updateMask(not_crop_1km)

    # 100m fraction layers (JS line 2834-2877)
    built_frac_100 = aggregate_image(lulc.unmask(0).eq(50), 10, 100, 'mean', 4096).rename('builtFrac100')
    crop_frac_100 = aggregate_image(lulc.unmask(0).eq(40), 10, 100, 'mean', 4096).rename('cropFrac100')

    # Dynamic World canopy, 6-month window
    canopy_start = analysis_end.advance(-6, 'month')
    dw_trees = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                .filterBounds(region).filterDate(canopy_start, analysis_end)
                .select('trees'))
    tree_prob_10_raw = (ee.Image(ee.Algorithms.If(
        dw_trees.size().gt(0), dw_trees.median(),
        lulc.eq(10).multiply(0.8)))
        .setDefaultProjection(wc_proj).clip(region))
    tree_prob_10 = tree_prob_10_raw.where(
        tree_prob_10_raw.gt(1.5), tree_prob_10_raw.divide(100)).rename('trees')
    not_crop_10 = lulc.unmask(0).neq(40).setDefaultProjection(wc_proj)
    canopy_prob_10 = tree_prob_10.toFloat().updateMask(not_crop_10).rename('canopyProb10')
    canopy_prob_10 = canopy_prob_10.where(canopy_prob_10.lt(0.10), 0)
    canopy_frac_100 = aggregate_image(canopy_prob_10, 10, 100, 'mean', 4096).rename('canopyFrac100')

    dw_built = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                .filterBounds(region).filterDate(canopy_start, analysis_end)
                .select('built'))
    dw_built_prob = (ee.Image(ee.Algorithms.If(
        dw_built.size().gt(0), dw_built.mean(),
        lulc.eq(50).multiply(0.8)))
        .setDefaultProjection(wc_proj).clip(region))

    return {
        'lulc': lulc, 'albedo': albedo, 'population': worldpop,
        'nightlights': nightlights, 'modisDay': modis_day, 'modisNight': modis_night,
        'builtFrac100': built_frac_100, 'cropFrac100': crop_frac_100,
        'canopyFrac100': canopy_frac_100, 'dwBuiltProb': dw_built_prob,
    }


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 1+2: WARD HEAT INDICATORS (JS calculateWardHeatIndicators, line 2936)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_ward_heat_indicators(wards, lst, uhi, lulc, cfg, city_mean_lst):
    built_mask = lulc.eq(50).selfMask()
    uhi_built = uhi.updateMask(built_mask)
    combined = (lst.rename('LST')
                .addBands(uhi.rename('UHI_all'))
                .addBands(uhi_built.rename('UHI_built')))

    scale = 60 if cfg['areaKm2'] > 1400 else SCALES['lst']
    tile_scale = 16 if cfg['areaKm2'] > 1400 else 8

    stats = combined.reduceRegions(
        collection=wards,
        reducer=(ee.Reducer.mean()
                 .combine(ee.Reducer.stdDev(), '', True)
                 .combine(ee.Reducer.min(), '', True)
                 .combine(ee.Reducer.max(), '', True)
                 .combine(ee.Reducer.percentile([10, 25, 75, 90]), '', True)),
        scale=scale, crs='EPSG:4326', tileScale=tile_scale)

    def _derive(ward):
        lst_mean = get_number(ward, 'LST_mean', 35)
        lst_min = get_number(ward, 'LST_min', 30)
        lst_max = get_number(ward, 'LST_max', 40)
        lst_p90 = get_number(ward, 'LST_p90', 38)
        heat_score = (lst_mean.multiply(0.3).add(lst_max.multiply(0.3))
                      .add(lst_p90.multiply(0.4)))
        return ward.set({
            'LST_mean': lst_mean,
            'LST_min': lst_min,
            'LST_max': lst_max,
            'heat_score': heat_score,
            'LST_hotspot': lst_mean.subtract(city_mean_lst),
            'UHI_all_mean': get_number(ward, 'UHI_all_mean', 0),
            'UHI_all_stdDev': get_number(ward, 'UHI_all_stdDev', 0),
            'UHI_built_mean': get_number(ward, 'UHI_built_mean', 0),
            'UHI_built_p90': get_number(ward, 'UHI_built_p90', 0),
        })

    return stats.map(_derive)


# ───────────────────────────────────────────────────────────────────────────────
# SUPPLEMENTAL WARD DATA (JS calculateSupplementalWardData, line 3079)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_supplemental(wards, ndvi, lulc, nightlights, urban, boundary, cfg):
    ghsl = (ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
            .select('built_surface').clip(boundary))
    built_mask = ghsl.gte(1000).And(lulc.eq(50))

    density_stats = ghsl.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=100, bestEffort=True, maxPixels=1e8)
    d_p5 = safe_dict_number(density_stats, 'built_surface_p5', 0).max(0)
    d_p95 = safe_dict_number(density_stats, 'built_surface_p95', 100).max(d_p5.add(1))
    density_norm = (ghsl.subtract(d_p5).divide(d_p95.subtract(d_p5).max(1))
                    .clamp(0, 1).multiply(100).updateMask(built_mask)
                    .rename('ghslDensity'))

    night_stats = nightlights.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=500, bestEffort=True, maxPixels=1e8)
    n_p5 = safe_dict_number(night_stats, 'avg_rad_p5', 0).max(0)
    n_p95 = safe_dict_number(night_stats, 'avg_rad_p95', 1).max(n_p5.add(0.1))
    brightness = nightlights.subtract(n_p5).divide(n_p95.subtract(n_p5).max(0.1)).clamp(0, 1)
    dimness = (ee.Image.constant(1).subtract(brightness).multiply(100)
               .clamp(0, 100).updateMask(built_mask).rename('dimness'))

    is_veg = lulc.eq(10).Or(lulc.eq(20)).Or(lulc.eq(30))
    veg_frac_100 = aggregate_image(is_veg, 10, 100, 'mean', 1024).clip(boundary)
    veg_stats = veg_frac_100.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=100, bestEffort=True, maxPixels=1e8)
    v_p5 = safe_dict_number(veg_stats, 'Map_p5', 0).max(0)
    v_p95 = safe_dict_number(veg_stats, 'Map_p95', 1).max(v_p5.add(0.01))
    veg_norm = veg_frac_100.subtract(v_p5).divide(v_p95.subtract(v_p5).max(0.01)).clamp(0, 1)
    veg_deficit = (ee.Image.constant(1).subtract(veg_norm).multiply(100)
                   .clamp(0, 100).updateMask(built_mask).rename('vegDeficit'))

    tree_prob_100 = urban['canopyFrac100'].multiply(100).rename('treeProb')
    dw_built_10 = urban['dwBuiltProb'].multiply(100).rename('dwBuiltProb')

    combined = (ndvi.rename('ndvi')
                .addBands(urban['modisNight'].rename('nightLST'))
                .addBands(tree_prob_100)
                .addBands(dw_built_10)
                .addBands(density_norm)
                .addBands(dimness)
                .addBands(veg_deficit))

    tile_scale = 16 if cfg['areaKm2'] > 1400 else 8
    stats = combined.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean(),
        scale=100, crs='EPSG:4326', tileScale=tile_scale)

    def _rename(ward):
        return ward.set({
            'ndvi_mean': get_number(ward, 'ndvi', 0.3),
            'nightLST_mean': get_number(ward, 'nightLST', 30),
            'treeProb_mean': get_number(ward, 'treeProb', 0),
            'dwBuiltProb_mean': get_number(ward, 'dwBuiltProb', 0),
            'ghslDensity_mean': get_number(ward, 'ghslDensity', 0),
            'dimness_mean': get_number(ward, 'dimness', 50),
            'vegDeficit_mean': get_number(ward, 'vegDeficit', 50),
        })

    return stats.map(_rename)


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 3: DENSE/VULNERABLE HOUSING (JS calculateInformalHousing, line 4882)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_informal_housing(wards, lulc, nightlights, boundary, cfg):
    ghsl = (ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
            .select('built_surface').clip(boundary)
            .reproject(crs='EPSG:4326', scale=10)
            .rename('coverage_pct'))

    built_mask = (lulc.eq(50).Or(ghsl.gte(10))
                  .reproject(crs='EPSG:4326', scale=10).selfMask())

    d_stats = ghsl.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=100, maxPixels=1e9, bestEffort=True)
    d_p5 = safe_dict_number(d_stats, 'coverage_pct_p5', 0)
    d_p95 = safe_dict_number(d_stats, 'coverage_pct_p95', 100)
    density_norm = (ghsl.updateMask(built_mask).subtract(d_p5)
                    .divide(d_p95.subtract(d_p5).max(1))
                    .multiply(100).clamp(0, 100).rename('density_norm'))

    veg_mask = (lulc.eq(10).Or(lulc.eq(20)).Or(lulc.eq(30))
                .reproject(crs='EPSG:4326', scale=10))
    veg_fraction = (veg_mask
                    .reduceResolution(reducer=ee.Reducer.mean(), maxPixels=256)
                    .reproject(crs='EPSG:4326', scale=100)
                    .multiply(100).rename('veg_fraction'))
    v_stats = veg_fraction.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=100, maxPixels=1e9, bestEffort=True)
    v_p5 = safe_dict_number(v_stats, 'veg_fraction_p5', 0)
    v_p95 = safe_dict_number(v_stats, 'veg_fraction_p95', 100)
    veg_deficit_norm = (veg_fraction.updateMask(built_mask).subtract(v_p5)
                        .divide(v_p95.subtract(v_p5).max(1))
                        .multiply(-100).add(100).clamp(0, 100)
                        .rename('vegdeficit_norm'))

    night_100 = nightlights.reproject(crs='EPSG:4326', scale=100)
    n_stats = night_100.updateMask(built_mask).reduceRegion(
        reducer=ee.Reducer.percentile([5, 95]), geometry=boundary,
        scale=100, maxPixels=1e9, bestEffort=True)
    n_p5 = safe_dict_number(n_stats, 'avg_rad_p5', 0)
    n_p95 = safe_dict_number(n_stats, 'avg_rad_p95', 10)
    dimness_norm = (night_100.updateMask(built_mask).subtract(n_p5)
                    .divide(n_p95.subtract(n_p5).max(1))
                    .multiply(-100).add(100).clamp(0, 100)
                    .rename('dimness_norm'))

    density_10 = density_norm.reproject(crs='EPSG:4326', scale=10)
    vegdef_10 = veg_deficit_norm.resample('bilinear').reproject(crs='EPSG:4326', scale=10)
    dimness_10 = dimness_norm.resample('bilinear').reproject(crs='EPSG:4326', scale=10)

    score = (density_10.add(1)
             .multiply(vegdef_10.add(1))
             .multiply(dimness_10.add(1))
             .pow(ee.Number(1).divide(3))
             .subtract(1).clamp(0, 100)
             .updateMask(built_mask)
             .reproject(crs='EPSG:4326', scale=10)
             .rename('vulnerable_housing'))

    tile_scale = 16 if cfg['areaKm2'] > 1000 else 8
    components = (score.rename('composite')
                  .addBands(density_10.rename('density'))
                  .addBands(vegdef_10.rename('vegdeficit'))
                  .addBands(dimness_10.rename('dimness')))
    stats = components.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean(), scale=30, tileScale=tile_scale)

    def _rename(ward):
        return ward.set({
            'informalHousingScore': get_number(ward, 'composite', 0).max(0),
            'buildingDensity': get_number(ward, 'density', 0).max(0),
            'vegetationDeficit': get_number(ward, 'vegdeficit', 0).max(0),
            'nightlightDimness': get_number(ward, 'dimness', 0).max(0),
        })

    return stats.map(_rename)


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 4: COOL ROOF PRIORITY (JS calculateCoolRoofPriority, line 3570)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_cool_roof(wards, lulc, albedo, worldpop, cfg, lst_wards, boundary,
                        city_mean_albedo, city_mean_roof_albedo):
    SCALE = 30 if cfg['areaKm2'] > 1400 else 10
    MIN_BUILT_FRAC = 0.20
    TARGET_ALBEDO = 0.60

    built_10m = lulc.eq(50).unmask(0)
    built_30m = built_10m.reproject(crs=albedo.projection(), scale=30)

    ghsl = (ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
            .select('built_surface').clip(boundary))
    ghsl_30m = ghsl.reproject(crs=albedo.projection(), scale=30)
    rooftop_mask = ghsl_30m.gte(1000).And(built_30m)

    roof_albedo = albedo.updateMask(rooftop_mask)
    combined = ee.Image.cat([
        roof_albedo.multiply(rooftop_mask).rename('roofAlbedoW'),
        rooftop_mask.rename('roofW'),
        albedo.multiply(built_30m).rename('albedoW'),
        built_30m.rename('builtW'),
        built_30m.rename('built'),
        albedo.rename('albedo'),
        albedo.updateMask(built_30m).rename('builtAlbedo'),
        worldpop.unmask(0).rename('population'),
    ])

    ward_stats = combined.reduceRegions(
        collection=wards,
        reducer=(ee.Reducer.sum()
                 .combine(ee.Reducer.mean(), '', True)
                 .combine(ee.Reducer.stdDev(), '', True)
                 .combine(ee.Reducer.min(), '', True)
                 .combine(ee.Reducer.max(), '', True)),
        scale=SCALE, crs='EPSG:4326',
        tileScale=16 if cfg['areaKm2'] > 1400 else 12,
        maxPixelsPerRegion=1e9)

    def _weighted(f):
        roof_w_sum = get_number(f, 'roofW_sum', 0).max(1e-6)
        roof_albedo_mean = get_number(f, 'roofAlbedoW_sum', 0).divide(roof_w_sum).clamp(0.01, 1)
        built_w_sum = get_number(f, 'builtW_sum', 0).max(1e-6)
        built_albedo_mean = get_number(f, 'albedoW_sum', 0).divide(built_w_sum).clamp(0.01, 1)
        return f.set({
            'builtAlbedo_mean': built_albedo_mean,
            'builtAlbedo_min': get_number(f, 'builtAlbedo_min', 0),
            'builtAlbedo_max': get_number(f, 'builtAlbedo_max', 1),
            'roofAlbedo_mean': roof_albedo_mean,
            'builtFrac_mean': get_number(f, 'built_mean', 0).clamp(0, 1),
            'albedo_stdDev': get_number(f, 'albedo_stdDev', 0),
            'albedo_min': get_number(f, 'albedo_min', 0),
            'albedo_max': get_number(f, 'albedo_max', 1),
            'w_sum': built_w_sum,
            'albedo_hotspot': get_number(f, 'albedo_mean', 0.20).subtract(city_mean_albedo),
            'roofAlbedo_hotspot': roof_albedo_mean.subtract(city_mean_roof_albedo),
        })

    ward_stats = ward_stats.map(_weighted)

    # Join LST_mean (JS line 3739-3767)
    def _join_lst(f):
        m = ee.Feature(f.get('_lstData'))
        lst_mean = ee.Number(ee.Algorithms.If(
            ee.Algorithms.IsEqual(m, None), 35,
            ee.Algorithms.If(ee.Algorithms.IsEqual(m.get('LST_mean'), None), 35,
                             m.get('LST_mean'))))
        return f.set('LST_mean', lst_mean)

    flt = ee.Filter.equals(leftField='WARD_NO', rightField='WARD_NO')
    joined = (ee.Join.saveFirst(matchKey='_lstData', outer=True)
              .apply(ward_stats, lst_wards, flt).map(_join_lst))

    eligible = joined.filter(ee.Filter.And(
        ee.Filter.notNull(['builtFrac_mean', 'builtAlbedo_mean', 'LST_mean']),
        ee.Filter.gte('builtFrac_mean', MIN_BUILT_FRAC),
        ee.Filter.gt('w_sum', 1e-3)))

    # computeCoolRoofPriority (JS line 3811)
    lst_pct = ee.Dictionary(eligible.reduceColumns(
        ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']), ['LST_mean']))
    lst_p5 = safe_dict_number(lst_pct, 'p5', 30)
    lst_p95 = safe_dict_number(lst_pct, 'p95', 50)
    lst_range = lst_p95.subtract(lst_p5).max(1)

    built_pct = ee.Dictionary(eligible.reduceColumns(
        ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']), ['builtFrac_mean']))
    built_p5 = safe_dict_number(built_pct, 'p5', 0.05)
    built_p95 = safe_dict_number(built_pct, 'p95', 0.80)
    built_range = built_p95.subtract(built_p5).max(0.1)

    alb_pct = ee.Dictionary(eligible.reduceColumns(
        ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']), ['builtAlbedo_mean']))
    alb_p5 = safe_dict_number(alb_pct, 'p5', 0.10)
    alb_p95 = safe_dict_number(alb_pct, 'p95', 0.25)
    alb_range = alb_p95.subtract(alb_p5).max(0.05)

    def _score(f):
        built_frac = get_number(f, 'builtFrac_mean', 0).clamp(0, 1)
        albedo_mean = get_number(f, 'builtAlbedo_mean', 0.20).clamp(0.01, 1)
        lst_mean = get_number(f, 'LST_mean', 35)
        wsum = get_number(f, 'w_sum', 0)
        ward_area = ee.Number(f.geometry().area(1)).divide(1e6)

        is_eligible = built_frac.gte(MIN_BUILT_FRAC)
        has_data = wsum.gt(1e-3)

        H = lst_mean.subtract(lst_p5).divide(lst_range)
        E = built_frac.subtract(built_p5).divide(built_range)
        albedo_norm = albedo_mean.subtract(alb_p5).divide(alb_range).clamp(0, 1)
        V = ee.Number(1).subtract(albedo_norm).clamp(0.01, 1)
        raw = H.multiply(E).multiply(V).pow(ee.Number(1).divide(3)).multiply(100)
        score = ee.Number(ee.Algorithms.If(is_eligible.And(has_data), raw, 0))

        built_area = ward_area.multiply(built_frac)
        roof_area = built_area.multiply(0.6)
        dark_frac = ee.Number(1).subtract(albedo_mean.divide(0.30)).clamp(0, 1)
        dark_roof = roof_area.multiply(dark_frac)
        albedo_gap = ee.Number(TARGET_ALBEDO).subtract(albedo_mean).max(0)

        return f.set({
            'builtFrac_pct': built_frac.multiply(100),
            'coolRoofPriorityScore': score,
            'darkRoofArea_km2': dark_roof,
            'potentialCooling_C': albedo_gap.multiply(15).divide(0.45),
            'estimatedCost_Lakhs': dark_roof.multiply(1e6).multiply(190).divide(1e5),
            'roofArea_km2': roof_area,
            'builtArea_km2': built_area,
        })

    scored = ee.FeatureCollection(joined.map(_score))

    eligible_scored = scored.filter(ee.Filter.gt('coolRoofPriorityScore', 0))
    ineligible = scored.filter(ee.Filter.lte('coolRoofPriorityScore', 0))
    score_pct = ee.Dictionary(eligible_scored.reduceColumns(
        ee.Reducer.percentile([40, 70]).setOutputs(['p40', 'p70']),
        ['coolRoofPriorityScore']))
    p40 = safe_dict_number(score_pct, 'p40', 30)
    p70 = safe_dict_number(score_pct, 'p70', 60)

    def _cls(f):
        s = ee.Number(f.get('coolRoofPriorityScore'))
        level = ee.Algorithms.If(
            s.gte(p70), 'High', ee.Algorithms.If(s.gte(p40), 'Medium', 'Low'))
        return f.set('priority_level', level)

    return (eligible_scored.map(_cls)
            .merge(ineligible.map(lambda f: f.set('priority_level', 'Low'))))


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 5: TREE PLANTING PRIORITY (JS calculateTreePlantingPriority_LowCanopy, 3965)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_tree_planting(wards, urban, lst_wards):
    TARGET_CANOPY_FRAC = 0.20
    MIN_BUILT_FRAC = 0.20
    LOW_CANOPY_THRESHOLD = 0.20

    built_frac_100 = urban['builtFrac100']
    canopy_frac_100 = urban['canopyFrac100']
    worldpop = urban['population']

    urban_mask = built_frac_100.gte(MIN_BUILT_FRAC)
    canopy_urban = canopy_frac_100.updateMask(urban_mask)
    built_urban = built_frac_100.updateMask(urban_mask)
    low_canopy = canopy_frac_100.lt(LOW_CANOPY_THRESHOLD)
    pop_low_canopy = worldpop.updateMask(low_canopy).rename('popLowCanopy')

    combined = (built_urban.rename('builtFrac')
                .addBands(canopy_urban.rename('canopyFrac'))
                .addBands(worldpop.unmask(0).rename('population'))
                .addBands(pop_low_canopy.unmask(0)))

    ward_stats = combined.reduceRegions(
        collection=wards,
        reducer=(ee.Reducer.mean()
                 .combine(ee.Reducer.stdDev(), '', True)
                 .combine(ee.Reducer.min(), '', True)
                 .combine(ee.Reducer.max(), '', True)
                 .combine(ee.Reducer.count(), '', True)
                 .combine(ee.Reducer.sum(), '', True)),
        scale=100, crs='EPSG:4326', tileScale=16, maxPixelsPerRegion=1e8)

    ward_stats = join_ward_results(ward_stats, lst_wards, 'WARD_NO', '_heat')
    ward_stats = ward_stats.filter(ee.Filter.gte('builtFrac_mean', MIN_BUILT_FRAC))

    lst_pct = ee.Dictionary(ward_stats
                            .filter(ee.Filter.notNull(['LST_mean']))
                            .reduceColumns(
                                ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']),
                                ['LST_mean']))
    lst_p5 = safe_dict_number(lst_pct, 'p5', 30)
    lst_p95 = safe_dict_number(lst_pct, 'p95', 50)

    def _score(f):
        built_frac = get_number(f, 'builtFrac_mean', 0).clamp(0, 1)
        canopy_frac = get_number(f, 'canopyFrac_mean', 0).clamp(0, 1)
        pop_low = get_number(f, 'popLowCanopy_sum', 0)
        lst_mean = get_number(f, 'LST_mean', 35)
        canopy_pct = canopy_frac.multiply(100)

        deficit = (ee.Number(TARGET_CANOPY_FRAC).subtract(canopy_frac)
                   .divide(TARGET_CANOPY_FRAC).clamp(0, 1))
        deficit_norm = deficit.max(0.01)
        exposed_norm = pop_low.add(1).log().max(0.01)
        lst_range = lst_p95.subtract(lst_p5).max(1)
        heat_norm = lst_mean.subtract(lst_p5).divide(lst_range).clamp(0.01, 1.0)

        raw = (deficit_norm.multiply(exposed_norm).multiply(heat_norm)
               .pow(ee.Number(1).divide(3)).multiply(100))

        ward_area_ha = f.geometry().area(1).divide(10000)
        built_area_ha = ee.Number(ward_area_ha).multiply(built_frac)
        # BUG FIX vs CHAITRA source (JS line 4154): the JS multiplies built
        # area by the NORMALIZED deficit ((target-current)/target, =1.0 for a
        # treeless ward), so "canopy deficit" comes out as the ward's entire
        # built area — Agra summed to 10,397 ha, 79% of the whole city, which
        # a 20% canopy target can never imply. The physically meaningful
        # quantity is the canopy-area gap: built area × (target − current)
        # = built area × deficit × TARGET. City totals then stay ≤ 20% of
        # built land, consistent with area actually available for planting.
        canopy_deficit_ha = (built_area_ha.multiply(deficit)
                             .multiply(TARGET_CANOPY_FRAC))
        # NOTE: layer constants (JS line 4157-4166): 150 trees/ha, 1.35 buffer,
        # Rs 1,400/tree. CHAITRA's UI resource panels use a different model
        # (RESOURCE_CONFIG: 400/plantable-ha, Rs 750) — see findings doc.
        trees_needed = canopy_deficit_ha.multiply(150).ceil()
        saplings = trees_needed.multiply(1.35).ceil()
        cost_lakhs = saplings.multiply(1400).divide(100000)

        urgency = ee.Algorithms.If(
            canopy_pct.lt(5), 'CRITICAL',
            ee.Algorithms.If(canopy_pct.lt(10), 'SEVERE',
                             ee.Algorithms.If(canopy_pct.lt(15), 'HIGH',
                                              ee.Algorithms.If(canopy_pct.lt(20), 'MODERATE', 'ADEQUATE'))))

        return f.set({
            'canopyFrac_mean': canopy_frac,
            'currentCanopy_pct': canopy_pct,
            'canopyDeficit_ha': canopy_deficit_ha,
            'treesNeeded': trees_needed,
            'saplingsToPlant': saplings,
            'totalCost_Lakhs': cost_lakhs,
            'greeningUrgency': urgency,
            'popInLowCanopy': pop_low,
            'priority_score': raw,
            'greenAccessScore': deficit.multiply(100),
        })

    scored = ee.FeatureCollection(ward_stats.map(_score))

    pct = ee.Dictionary(scored.filter(ee.Filter.notNull(['priority_score']))
                        .reduceColumns(
                            ee.Reducer.percentile([40, 70]).setOutputs(['p40', 'p70']),
                            ['priority_score']))
    p40 = safe_dict_number(pct, 'p40', 30)
    p70 = safe_dict_number(pct, 'p70', 60)

    def _cls(f):
        s = get_number(f, 'priority_score', 0)
        level = ee.Algorithms.If(
            s.gte(p70), 'High', ee.Algorithms.If(s.gte(p40), 'Medium', 'Low'))
        return f.set('priority_level', level)

    return scored.map(_cls)


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 6: 24-HOUR ACTIVITY HEAT (JS calculateActivityHeatStress_Ward, line 4299)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_activity_heat(wards, modis_day, modis_night, nightlights, population):
    day_by_ward = modis_day.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean().setOutputs(['dayLST_mean']),
        scale=1000, crs='EPSG:4326', tileScale=8, maxPixelsPerRegion=1e8)
    night_by_ward = modis_night.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean().setOutputs(['nightLST_mean']),
        scale=1000, crs='EPSG:4326', tileScale=8, maxPixelsPerRegion=1e8)
    ntl_by_ward = nightlights.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean().setOutputs(['ntl_mean']),
        scale=500, crs='EPSG:4326', tileScale=8, maxPixelsPerRegion=1e8)
    pop_by_ward = population.reduceRegions(
        collection=wards, reducer=ee.Reducer.sum().setOutputs(['pop_sum']),
        scale=100, crs='EPSG:4326', tileScale=8, maxPixelsPerRegion=1e8)

    joined = join_ward_results(wards, day_by_ward, 'WARD_NO', '_day')
    joined = join_ward_results(joined, night_by_ward, 'WARD_NO', '_night')
    joined = join_ward_results(joined, ntl_by_ward, 'WARD_NO', '_ntl')
    joined = join_ward_results(joined, pop_by_ward, 'WARD_NO', '_pop')

    def _pct(prop, d5, d95):
        p = ee.Dictionary(joined.filter(ee.Filter.notNull([prop])).reduceColumns(
            ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']), [prop]))
        return safe_dict_number(p, 'p5', d5), safe_dict_number(p, 'p95', d95)

    day_p5, day_p95 = _pct('dayLST_mean', 30, 40)
    night_p5, night_p95 = _pct('nightLST_mean', 25, 33)
    act_p5, act_p95 = _pct('ntl_mean', 0, 1)

    def _score(f):
        day_t = get_number(f, 'dayLST_mean', 35)
        night_t = get_number(f, 'nightLST_mean', 28)
        ntl = get_number(f, 'ntl_mean', 0)
        pop = get_number(f, 'pop_sum', 0).max(0)

        H = (normalize_by_percentiles(day_t, day_p5, day_p95)
             .add(normalize_by_percentiles(night_t, night_p5, night_p95))
             .divide(2))
        E = pop.add(1).log().max(0.01)
        V = normalize_by_percentiles(ntl, act_p5, act_p95).clamp(0.01, 1.0)
        score = H.multiply(E).multiply(V).pow(ee.Number(1).divide(3)).multiply(100)

        return f.set({
            'activityHeatScore': score,
            'dayLST': day_t,
            'nightLST': night_t,
            'avgLST_24h': day_t.add(night_t).divide(2),
            'ntl_mean': ntl,
        })

    return joined.map(_score)


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 7: POPULATION HEAT RISK (JS calculatePopulationHeatRisk_v2, line 3371)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_population_heat_risk(wards, lst_wards, worldpop, informal_wards, cfg):
    pop_scale = 200 if cfg['areaKm2'] > 1400 else 100
    tile_scale = 16 if cfg['areaKm2'] > 1400 else 8
    tolerance = 50 if cfg['areaKm2'] > 1000 else 30

    wards_simple = wards.map(lambda f: f.simplify(maxError=tolerance))
    pop_wards = worldpop.unmask(0).rename('population').reduceRegions(
        collection=wards_simple,
        reducer=ee.Reducer.sum().setOutputs(['totalPop']),
        scale=pop_scale, crs='EPSG:4326', tileScale=tile_scale)

    joined = join_ward_results(pop_wards, lst_wards, 'WARD_NO', '_lst')
    joined = join_ward_results(joined, informal_wards, 'WARD_NO', '_inf')

    lst_pct = ee.Dictionary(lst_wards.filter(ee.Filter.notNull(['LST_hotspot']))
                            .reduceColumns(
                                ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']),
                                ['LST_hotspot']))
    h_p5 = safe_dict_number(lst_pct, 'p5', 0)
    h_p95 = safe_dict_number(lst_pct, 'p95', 5)
    h_range = h_p95.subtract(h_p5).max(0.1)

    dense_pct = ee.Dictionary(informal_wards
                              .filter(ee.Filter.notNull(['informalHousingScore']))
                              .reduceColumns(
                                  ee.Reducer.percentile([5, 95]).setOutputs(['p5', 'p95']),
                                  ['informalHousingScore']))
    v_p5 = safe_dict_number(dense_pct, 'p5', 0)
    v_p95 = safe_dict_number(dense_pct, 'p95', 100)
    v_range = v_p95.subtract(v_p5).max(1)

    def _score(ward):
        total_pop = get_number(ward, 'totalPop', 1).max(1)
        H = get_number(ward, 'LST_hotspot', 0).subtract(h_p5).divide(h_range).max(0.01)
        E = total_pop.add(1).log()
        V = get_number(ward, 'informalHousingScore', 0).subtract(v_p5).divide(v_range).max(0.01)
        risk = H.multiply(E).multiply(V).pow(ee.Number(1).divide(3)).multiply(100)
        area = ee.Number(ee.Algorithms.If(
            ee.Algorithms.IsEqual(ward.get('area_km2'), None),
            ee.Number(ward.geometry().area(1)).divide(1e6).max(0.01),
            ward.get('area_km2'))).max(0.01)
        return ward.set({
            'riskScore': risk,
            'totalPop': total_pop,
            'popAtRisk': total_pop,
            'popDensity': total_pop.divide(area),
            'exposureRate': 100,
        })

    scored = joined.map(_score)
    return add_priority_by_percentiles_keep_all(scored, 'riskScore', 40, 70)


# ───────────────────────────────────────────────────────────────────────────────
# LAYER 8: COMPOSITE HEAT RISK INDEX (JS calculateHeatRiskIndex_IPCC, line 4471)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_heat_risk_index(wards, lst_wards, pop_wards, canopy_wards,
                              cool_roof_wards, informal_wards):
    joined = join_ward_results(wards, lst_wards, 'WARD_NO', '_lst')
    joined = join_ward_results(joined, pop_wards, 'WARD_NO', '_pop')
    joined = join_ward_results(joined, canopy_wards, 'WARD_NO', '_can')
    joined = join_ward_results(joined, cool_roof_wards, 'WARD_NO', '_roof')
    joined = join_ward_results(joined, informal_wards, 'WARD_NO', '_inf')

    valid = joined.filter(ee.Filter.And(
        ee.Filter.notNull(['LST_hotspot', 'nighttemp_hotspot']),
        ee.Filter.notNull(['canopyFrac_mean', 'informalHousingScore'])))

    main_pct = valid.reduceColumns(
        reducer=(ee.Reducer.percentile([5, 95]).setOutputs(['lst_p5', 'lst_p95'])
                 .combine(ee.Reducer.percentile([5, 95]).setOutputs(['night_p5', 'night_p95']), '', False)
                 .combine(ee.Reducer.percentile([5, 95]).setOutputs(['canopy_p5', 'canopy_p95']), '', False)
                 .combine(ee.Reducer.percentile([5, 95]).setOutputs(['dense_p5', 'dense_p95']), '', False)),
        selectors=['LST_hotspot', 'nighttemp_hotspot', 'canopyFrac_mean',
                   'informalHousingScore'])

    albedo_wards = valid.filter(ee.Filter.notNull(['builtAlbedo_mean']))
    albedo_pct = ee.Dictionary(ee.Algorithms.If(
        albedo_wards.size().gt(0),
        albedo_wards.reduceColumns(
            reducer=ee.Reducer.percentile([5, 50, 95]).setOutputs(
                ['albedo_p5', 'albedo_p50', 'albedo_p95']),
            selectors=['builtAlbedo_mean']),
        ee.Dictionary({'albedo_p5': 0.10, 'albedo_p50': 0.15, 'albedo_p95': 0.25})))

    pct = ee.Dictionary(main_pct).combine(albedo_pct)
    lst_p5 = safe_dict_number(pct, 'lst_p5', -3)
    lst_range = safe_dict_number(pct, 'lst_p95', 5).subtract(lst_p5).max(0.1)
    night_p5 = safe_dict_number(pct, 'night_p5', -2)
    night_range = safe_dict_number(pct, 'night_p95', 3).subtract(night_p5).max(0.1)
    canopy_p5 = safe_dict_number(pct, 'canopy_p5', 0)
    canopy_range = safe_dict_number(pct, 'canopy_p95', 40).subtract(canopy_p5).max(0.1)
    dense_p5 = safe_dict_number(pct, 'dense_p5', 0)
    dense_range = safe_dict_number(pct, 'dense_p95', 80).subtract(dense_p5).max(1)
    albedo_p5 = safe_dict_number(pct, 'albedo_p5', 0.1)
    albedo_p50 = safe_dict_number(pct, 'albedo_p50', 0.15)
    albedo_range = safe_dict_number(pct, 'albedo_p95', 0.3).subtract(albedo_p5).max(0.01)

    FLOOR = 0.05

    def _score(ward):
        total_pop = get_number(ward, 'totalPop', 1000).max(1)
        lst_hot = get_number(ward, 'LST_hotspot', 0)
        night_hot = get_number(ward, 'nighttemp_hotspot', 0)
        canopy = get_number(ward, 'canopyFrac_mean', 15)
        dense = get_number(ward, 'informalHousingScore', 30)
        built_albedo = ee.Number(ee.Algorithms.If(
            ee.Algorithms.IsEqual(ward.get('builtAlbedo_mean'), None),
            albedo_p50, get_number(ward, 'builtAlbedo_mean', 0.15)))

        H1 = lst_hot.subtract(lst_p5).divide(lst_range).clamp(0, 1).max(FLOOR)
        H2 = night_hot.subtract(night_p5).divide(night_range).clamp(0, 1).max(FLOOR)
        H = H1.add(H2)
        E = total_pop.add(1).log().max(FLOOR)
        V1 = ee.Number(1).subtract(
            canopy.subtract(canopy_p5).divide(canopy_range).clamp(0, 1)).max(FLOOR)
        V2 = dense.subtract(dense_p5).divide(dense_range).clamp(0, 1).max(FLOOR)
        V3 = ee.Number(1).subtract(
            built_albedo.subtract(albedo_p5).divide(albedo_range).clamp(0, 1)).max(FLOOR)
        V = V1.add(V2).add(V3)
        risk = H.multiply(E).multiply(V).pow(ee.Number(1).divide(3))

        return ward.set({
            'riskIndex': risk,
            'hazardIndex': H,
            'exposureIndex': E,
            'vulnerabilityIndex': V,
        })

    scored = joined.map(_score)
    return add_priority_by_percentiles_keep_all(scored, 'riskIndex', 50, 70)


# ───────────────────────────────────────────────────────────────────────────────
# EXPORT SCHEMA
# ───────────────────────────────────────────────────────────────────────────────

def select_props(fc, props, renames=None):
    """Select properties (keeping WARD_NO for joins), optionally renaming."""
    src = ['WARD_NO'] + props
    dst = ['WARD_NO'] + [(renames or {}).get(p, p) for p in props]
    return fc.select(src, dst, retainGeometry=False)


def export_columns(census_cols):
    return [
        # Identifiers
        'state', 'city', 'WARD_NO', 'ward_name', 'area_km2',
        # Census 2011 (from ward asset, when present)
        *census_cols,
        # Temperature / UHI
        'LST_mean', 'LST_min', 'LST_max', 'LST_hotspot', 'heat_score',
        'UHI_all_mean', 'UHI_all_stdDev', 'UHI_built_mean', 'nighttemp_hotspot',
        # Supplemental inputs
        'ndvi_mean', 'nightLST_mean', 'treeProb_mean', 'vegDeficit_mean',
        'dwBuiltProb_mean', 'ghslDensity_mean', 'dimness_mean',
        # Population heat risk
        'totalPop', 'popDensity', 'riskScore', 'popAtRisk', 'exposureRate',
        'pop_priority_level',
        # Cool roof
        'builtAlbedo_mean', 'builtAlbedo_min', 'builtAlbedo_max',
        'coolRoofPriorityScore', 'darkRoofArea_km2', 'potentialCooling_C',
        'estimatedCost_Lakhs', 'builtFrac_pct', 'coolroof_priority_level',
        # Tree planting
        'treePriorityScore', 'currentCanopy_pct', 'canopyDeficit_ha',
        'treesNeeded', 'saplingsToPlant', 'totalCost_Lakhs', 'greeningUrgency',
        'popInLowCanopy', 'tree_priority_level',
        # 24-hour heat
        'activityHeatScore', 'dayLST', 'nightLST', 'avgLST_24h', 'ntl_mean',
        'activity_priority_level',
        # Dense housing
        'informalHousingScore', 'buildingDensity', 'vegetationDeficit',
        'nightlightDimness', 'informal_priority_level',
        # Composite risk (the JS export left these blank — fixed here)
        'riskIndex', 'hazardIndex', 'exposureIndex', 'vulnerabilityIndex',
        'priority_level',
    ]


# ───────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ───────────────────────────────────────────────────────────────────────────────

def build_pipeline(city):
    wards, cfg = load_boundaries(city)
    available_props = set(wards.first().propertyNames().getInfo())
    census_cols = [c for c in CENSUS_COLUMNS if c in available_props]
    boundary = wards.geometry()
    summer_filter = ee.Filter.calendarRange(4, 7, 'month')
    water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')

    composite = load_landsat_composite(boundary, summer_filter)
    thermal = calculate_thermal(composite, boundary, water)
    lst, ndvi, uhi = thermal['lst'], thermal['ndvi'], thermal['uhi']

    urban = process_urban_layers(boundary, summer_filter, lst)
    lulc, nightlights = urban['lulc'], urban['nightlights']

    # City means (JS lines 7095-7145, 7371-7403)
    city_mean_lst = ee.Number(lst.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundary, scale=100,
        bestEffort=True, maxPixels=1e9, tileScale=8).get('LST'))
    city_mean_night = ee.Number(urban['modisNight'].reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundary, scale=1000,
        bestEffort=True, maxPixels=1e9).get('MODIS_Night_LST'))
    albedo_clipped = urban['albedo'].clip(boundary)
    city_mean_albedo = ee.Number(albedo_clipped.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundary, scale=30,
        bestEffort=True, maxPixels=1e9, tileScale=8).get('albedo'))
    ghsl = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020').select('built_surface').clip(boundary)
    rooftop_mask = ghsl.gte(1000).And(lulc.eq(50))
    city_mean_roof_albedo = ee.Number(albedo_clipped.updateMask(rooftop_mask).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundary, scale=30,
        bestEffort=True, maxPixels=1e9, tileScale=8).get('albedo'))

    # lstWards + nighttime hotspot + supplemental (JS lines 7285-7337)
    lst_wards = calculate_ward_heat_indicators(wards, lst, uhi, lulc, cfg, city_mean_lst)
    nighttemp_dev = urban['modisNight'].subtract(city_mean_night)
    night_by_ward = nighttemp_dev.reduceRegions(
        collection=wards, reducer=ee.Reducer.mean().setOutputs(['nighttemp_hotspot']),
        scale=1000, crs='EPSG:4326', tileScale=8)
    lst_wards = join_ward_results(lst_wards, night_by_ward, 'WARD_NO', '_mn')
    supplemental = calculate_supplemental(wards, ndvi, lulc, nightlights, urban, boundary, cfg)
    lst_wards = join_ward_results(lst_wards, supplemental, 'WARD_NO', '_sup')

    # Per-layer computations (JS lines 7348-7541)
    informal_wards = calculate_informal_housing(wards, lulc, nightlights, boundary, cfg)
    cool_roof_wards = calculate_cool_roof(
        wards, lulc, urban['albedo'], urban['population'], cfg, lst_wards,
        boundary, city_mean_albedo, city_mean_roof_albedo)
    canopy_wards = calculate_tree_planting(wards, urban, lst_wards)
    activity_wards = calculate_activity_heat(
        wards, urban['modisDay'], urban['modisNight'], nightlights, urban['population'])
    pop_wards = calculate_population_heat_risk(
        wards, lst_wards, urban['population'], informal_wards, cfg)
    risk_wards = calculate_heat_risk_index(
        wards, lst_wards, pop_wards, canopy_wards, cool_roof_wards, informal_wards)

    activity_classified = add_priority_by_percentiles(
        activity_wards, 'activityHeatScore', 50, 80)
    informal_classified = add_priority_by_percentiles(
        informal_wards, 'informalHousingScore', 50, 80)

    # ── Assemble export table ──
    base_cols = ['state', 'city', 'ward_name', 'area_km2'] + census_cols
    export = wards.select(['WARD_NO'] + base_cols, None, False)

    export = join_ward_results(export, select_props(lst_wards, [
        'LST_mean', 'LST_min', 'LST_max', 'LST_hotspot', 'heat_score',
        'UHI_all_mean', 'UHI_all_stdDev', 'UHI_built_mean', 'nighttemp_hotspot',
        'ndvi_mean', 'nightLST_mean', 'treeProb_mean', 'vegDeficit_mean',
        'dwBuiltProb_mean', 'ghslDensity_mean', 'dimness_mean']), 'WARD_NO', '_j1')

    export = join_ward_results(export, select_props(pop_wards, [
        'totalPop', 'popDensity', 'riskScore', 'popAtRisk', 'exposureRate',
        'priority_level'], {'priority_level': 'pop_priority_level'}), 'WARD_NO', '_j2')

    export = join_ward_results(export, select_props(cool_roof_wards, [
        'builtAlbedo_mean', 'builtAlbedo_min', 'builtAlbedo_max',
        'coolRoofPriorityScore', 'darkRoofArea_km2', 'potentialCooling_C',
        'estimatedCost_Lakhs', 'builtFrac_pct', 'priority_level'],
        {'priority_level': 'coolroof_priority_level'}), 'WARD_NO', '_j3')

    export = join_ward_results(export, select_props(canopy_wards, [
        'priority_score', 'currentCanopy_pct', 'canopyDeficit_ha',
        'treesNeeded', 'saplingsToPlant', 'totalCost_Lakhs', 'greeningUrgency',
        'popInLowCanopy', 'priority_level'],
        {'priority_score': 'treePriorityScore',
         'priority_level': 'tree_priority_level'}), 'WARD_NO', '_j4')

    export = join_ward_results(export, select_props(activity_classified, [
        'activityHeatScore', 'dayLST', 'nightLST', 'avgLST_24h', 'ntl_mean',
        'priority_level'], {'priority_level': 'activity_priority_level'}),
        'WARD_NO', '_j5')

    export = join_ward_results(export, select_props(informal_classified, [
        'informalHousingScore', 'buildingDensity', 'vegetationDeficit',
        'nightlightDimness', 'priority_level'],
        {'priority_level': 'informal_priority_level'}), 'WARD_NO', '_j6')

    export = join_ward_results(export, select_props(risk_wards, [
        'riskIndex', 'hazardIndex', 'exposureIndex', 'vulnerabilityIndex',
        'priority_level']), 'WARD_NO', '_j7')

    # City-wide HAP context stats (JS lines 7028-7060)
    city_heat_stats = lst.reduceRegion(
        reducer=(ee.Reducer.mean()
                 .combine(ee.Reducer.percentile([50, 90, 95, 99]), '', True)),
        geometry=boundary, scale=30, crs='EPSG:4326',
        bestEffort=True, maxPixels=1e8, tileScale=8)
    total_area = boundary.area(1).divide(1e6)
    exceedance = ee.Dictionary({
        str(t): (lst.gte(t).multiply(ee.Image.pixelArea()).divide(1e6)
                 .reduceRegion(reducer=ee.Reducer.sum(), geometry=boundary,
                               scale=30, crs=cfg['utmZone'], bestEffort=True,
                               maxPixels=1e8).get('LST'))
        for t in (40, 45, 50)
    })
    city_stats = ee.Dictionary({
        'city': city,
        'analysis_window': f'{START_DATE} to {END_DATE}, summer (Apr-Jul)',
        'cityMeanLST_C': city_mean_lst,
        'cityMeanNightLST_C': city_mean_night,
        'coolReference_C': thermal['coolReference'],
        'cityMeanAlbedo': city_mean_albedo,
        'cityMeanRoofAlbedo': city_mean_roof_albedo,
        'LST_percentiles': city_heat_stats,
        'area_km2': total_area,
        'exceedance_area_km2_above_C': exceedance,
    })

    return export, city_stats, export_columns(census_cols)


def fetch_csv(export_fc, columns, out_path):
    """Synchronous CSV download via getDownloadURL."""
    url = export_fc.getDownloadURL(
        filetype='csv', selectors=columns, filename='chaitra_ward_stats')
    print('  download URL obtained, fetching...')
    with urllib.request.urlopen(url, timeout=3000) as resp, open(out_path, 'wb') as f:
        f.write(resp.read())


def fetch_via_batch(export_fc, columns, city, out_path):
    """Fallback: batch export task to Drive, poll, download via Drive API."""
    desc = f'CHAITRA_WardStats_{city}_{int(time.time())}'
    task = ee.batch.Export.table.toDrive(
        collection=export_fc, description=desc, folder='CHAITRA_Exports',
        fileNamePrefix=desc, fileFormat='CSV', selectors=columns)
    task.start()
    print(f'  batch task {task.id} started; polling...')
    while True:
        status = task.status()
        state = status['state']
        if state in ('COMPLETED', 'FAILED', 'CANCELLED'):
            break
        time.sleep(20)
    if state != 'COMPLETED':
        raise RuntimeError(f'Batch export failed: {status}')
    print('  task completed; downloading from Drive...')

    import google.auth.transport.requests
    import google.oauth2.credentials
    from ee import oauth
    creds = google.oauth2.credentials.Credentials(None, **oauth.get_credentials_arguments())
    creds.refresh(google.auth.transport.requests.Request())
    hdr = {'Authorization': 'Bearer ' + creds.token}
    q = urllib.parse.quote(f"name contains '{desc}' and mimeType='text/csv'")
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)',
        headers=hdr)
    files = json.load(urllib.request.urlopen(req))['files']
    if not files:
        raise RuntimeError('Exported CSV not found in Drive')
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{files[0]['id']}?alt=media",
        headers=hdr)
    with urllib.request.urlopen(req) as resp, open(out_path, 'wb') as f:
        f.write(resp.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='Agra', choices=sorted(CITY_CONFIGS))
    ap.add_argument('--project', default=os.environ.get('CHAITRA_GEE_PROJECT'),
                    required='CHAITRA_GEE_PROJECT' not in os.environ,
                    help='GCP project with Earth Engine enabled (or set '
                         'CHAITRA_GEE_PROJECT)')
    ap.add_argument('--out', default=None)
    ap.add_argument('--citystats', default=None)
    ap.add_argument('--batch', action='store_true',
                    help='Use batch Drive export instead of synchronous download')
    args = ap.parse_args()

    os.makedirs('outputs', exist_ok=True)
    out_path = args.out or f'outputs/{args.city.lower()}_ward_data.csv'
    stats_path = args.citystats or f'outputs/{args.city.lower()}_city_stats.json'

    ee.Initialize(project=args.project)
    print(f'Building pipeline for {args.city}...')
    export_fc, city_stats, columns = build_pipeline(args.city)

    print('Fetching city-wide stats...')
    stats = city_stats.getInfo()
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f'  wrote {stats_path}')

    print('Fetching ward CSV (this triggers the full computation; may take minutes)...')
    t0 = time.time()
    try:
        if args.batch:
            fetch_via_batch(export_fc, columns, args.city, out_path)
        else:
            fetch_csv(export_fc, columns, out_path)
    except Exception as e:
        if args.batch:
            raise
        print(f'  synchronous download failed ({type(e).__name__}: {e})')
        print('  falling back to batch Drive export...')
        fetch_via_batch(export_fc, columns, args.city, out_path)
    print(f'  wrote {out_path} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
