"""Local summary figures and a provenance-preserving deployment-coordinate join."""

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent
TABLE_SOURCE = "https://www.nature.com/articles/s41597-025-05281-5/tables/1"


def deployment_join(frame, table):
    """Join explicit aliases; preserve missing or inconsistent source coordinates."""
    providers = {"JASCO/VPFA": "JASCO_VFPA", "JASCO/VPFA/ONC": "JASCO_VFPA_ONC",
                 "SMRU": "SMRUConsulting", "Orca Sound": "OrcaSound",
                 "DFO CRP": "DFO_CRP", "DFO WDLP": "DFO_WDLP"}
    aliases = {"LmKln": "LimeKiln", "BerkleyCanyon": "BarkleyCanyon",
               "NorthBC": "NorthBc", "StrGeosS2": "StrGeoS2"}
    lookup = defaultdict(list)
    for row in table:
        lookup[(providers.get(row['provider'], row['provider']),
                aliases.get(row['dataset'], row['dataset']))].append(row)
    keys = ['Provider', 'Dataset', 'Soundfile']
    groups = frame.group_by('Provider', 'Dataset').agg(
        pl.len().alias('annotations'), pl.struct(keys).n_unique().alias('recordings'),
        (pl.col('ClassSpecies') == 'KW').sum().alias('orca_annotations'),
    ).sort('Provider', 'Dataset')
    result = []
    for counts in groups.to_dicts():
        candidates = lookup.get((counts['Provider'], counts['Dataset']), [])
        source = candidates[0] if len(candidates) == 1 else None
        status = 'unmatched'
        lat = lon = None
        if counts['Provider'] in ['DFO_CRP', 'DFO_WDLP']:
            # Do not infer withheld coordinates from place names, even if table IDs conflict.
            status = 'withheld'
        elif source:
            try:
                lat = float(source['lat'].replace('−', '-'))
                lon = float(source['lon'].replace('−', '-'))
                status = 'approximate_region' if counts['Dataset'].startswith('Field_') else 'fixed'
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    status = 'invalid_coordinate'
                elif counts['Provider'] == 'UAF_NGOS' and lon > 0:
                    status = 'inconsistent_longitude_sign'
                if status not in ['fixed', 'approximate_region']:
                    lat = lon = None
            except ValueError:
                status = 'missing_coordinate'
        result.append({**counts, 'location': source['location'].rstrip('*') if source else counts['Dataset'],
                       'latitude': lat, 'longitude': lon, 'coordinate_status': status,
                       'source_dataset': source['dataset'] if source else None,
                       'source_latitude': source['lat'] if source else None,
                       'source_longitude': source['lon'] if source else None,
                       'coordinate_source': TABLE_SOURCE})
    return result


def visual_data(path, output):
    import numpy as np
    report = json.loads((output / 'summary.json').read_text())
    with path.open('rb') as stream:
        source_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    if source_hash != report['input_sha256']:
        raise ValueError('Source CSV differs from summary.json; rerun dclde summary first')
    stats = report['statistics']
    columns = ['Provider', 'Dataset', 'Soundfile', 'ClassSpecies', 'UTC',
               'AnnotationLevel', 'FileBeginSec', 'FileEndSec']
    frame = pl.read_csv(path, columns=columns, schema_overrides={c: pl.String for c in columns})
    table = json.loads((ROOT / 'resources/maps/dclde-deployment-table.json').read_text())
    deployments = deployment_join(frame, table)
    with (output / 'deployment-map.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, deployments[0].keys())
        writer.writeheader()
        writer.writerows(deployments)
    points = {}
    for row in deployments:
        if row['latitude'] is None:
            continue
        key = (row['longitude'], row['latitude'], row['coordinate_status'])
        point = points.setdefault(key, {'location': row['location'], 'longitude': key[0], 'latitude': key[1],
                                       'status': key[2], 'datasets': [], 'annotations': 0,
                                       'recordings': 0, 'orca_annotations': 0})
        point['datasets'].append(row['Dataset'])
        for field in ['annotations', 'recordings', 'orca_annotations']:
            point[field] += row[field]
    coverage = defaultdict(int)
    for row in deployments:
        coverage[row['coordinate_status']] += row['annotations']
    years = frame.with_columns(pl.col('UTC').str.slice(0, 4).alias('year')).group_by('year').len(
        name='annotations').sort('year').to_dicts()
    timed = frame.with_columns(pl.col('FileBeginSec').cast(pl.Float64, strict=False).alias('start'),
                              pl.col('FileEndSec').cast(pl.Float64, strict=False).alias('stop'))
    valid = timed.filter(pl.col('start').is_finite() & pl.col('stop').is_finite() & (pl.col('start') >= 0)
                         & (pl.col('stop') > pl.col('start'))
                         & pl.col('AnnotationLevel').is_in(['Call', 'Detection']))
    durations = (valid['stop'] - valid['start']).to_numpy()
    edges = np.geomspace(durations.min(), durations.max(), 31)
    counts, edges = np.histogram(durations, bins=edges)
    data = {'statistics': stats, 'years': years,
            'duration_histogram': [{'begin': float(a), 'end': float(b), 'annotations': int(n)}
                                   for a, b, n in zip(edges[:-1], edges[1:], counts)],
            'deployments': deployments, 'points': list(points.values()), 'coverage': dict(coverage),
            'coordinate_source': TABLE_SOURCE, 'input_sha256': source_hash}
    # Saved regional geometry is embedded so the dashboard needs no data requests.
    data['basemap'] = json.loads((ROOT / 'resources/maps/dclde-basemap.geojson').read_text())
    (output / 'visual-data.json').write_text(json.dumps(data, separators=(',', ':'), allow_nan=False) + '\n')
    features = [{'type': 'Feature', 'properties': {k: v for k, v in row.items()
                 if k not in ['latitude', 'longitude']},
                 'geometry': {'type': 'Point', 'coordinates': [row['longitude'], row['latitude']]}}
                for row in deployments if row['latitude'] is not None]
    (output / 'deployment-map.geojson').write_text(json.dumps(
        {'type': 'FeatureCollection', 'features': features}, indent=2) + '\n')
    return data


def static_summary(data, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    stats = data['statistics']
    fig, axes = plt.subplots(3, 2, figsize=(14, 13), layout='constrained')
    panels = [(stats['groups']['ClassSpecies'], 'ClassSpecies', 'Sound classes'),
              (stats['known_orca_ecotypes'] + [{'Ecotype': 'Unknown', 'annotations':
                 stats['orca_annotations_without_ecotype']}], 'Ecotype', 'Orca populations'),
              (stats['groups']['Provider'], 'Provider', 'Provider contributions'),
              (stats['groups']['AnnotationLevel'], 'AnnotationLevel', 'Annotation levels')]
    for axis, (rows, label, title) in zip(axes.flat, panels):
        values = [r['annotations'] for r in rows]
        bars = axis.barh([r[label] for r in rows], values, color='#246d84')
        axis.invert_yaxis()
        axis.bar_label(bars, labels=[f'{n:,}' for n in values], padding=4)
        axis.set_xlim(0, max(values) * 1.27)
        axis.set_title(title)
        axis.set_xlabel('Annotation rows')
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value / 1000:g}k'))
        axis.spines[['top', 'right']].set_visible(False)
    axis = axes[2, 0]
    axis.bar([r['year'] for r in data['years']], [r['annotations'] for r in data['years']], color='#246d84')
    axis.tick_params(axis='x', rotation=45)
    axis.set(title='Annotations by recording year', xlabel='UTC year', ylabel='Annotation rows')
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value / 1000:g}k'))
    axis = axes[2, 1]
    hist = data['duration_histogram']
    axis.bar([r['begin'] for r in hist], [r['annotations'] for r in hist],
             width=[r['end'] - r['begin'] for r in hist], align='edge', color='#246d84')
    axis.set(xscale='log', title='Valid call/detection durations', xlabel='Duration (seconds; log scale)',
             ylabel='Annotation rows per log-spaced bin')
    for value, label in [(stats['duration_seconds']['median'], 'Median'),
                         (stats['duration_seconds']['p95'], '95th percentile')]:
        axis.axvline(value, color='#a34523', linewidth=1, linestyle='--', label=f'{label} {value:.3f} s')
    axis.legend(frameon=False)
    fig.suptitle(f"DCLDE orca metadata: {stats['annotations']:,} annotation rows, {stats['recordings']:,} recording keys\n"
                 'Counts describe annotations; durations exclude file-level labels. No audio downloaded.', fontsize=14)
    for suffix in ['png', 'svg']:
        fig.savefig(output / f'summary-statistics.{suffix}', dpi=170)
    plt.close(fig)


def generate(path, output):
    data = visual_data(path, output)
    static_summary(data, output)
    return data
