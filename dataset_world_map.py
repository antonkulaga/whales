"""Build the world coverage map from local metadata; never download audio.

Run with `uv run python dataset_world_map.py`. Input snapshots and their hashes
are recorded in resources/maps/world-map-provenance.json.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

import polars as pl
from dclde_visuals import deployment_join, TABLE_SOURCE

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'data/input/world-map'
OUTPUT = ROOT / 'data/output/world-map'
ASSETS = ROOT / 'resources/maps'
NOISE = {'Ship engine noise', 'Clicks', 'Ambient X'}
CORRECTIONS = {'Globicephala macrorhyncus': 'Globicephala macrorhynchus',
               'Steno bredanesis': 'Steno bredanensis', 'Tursiop truncatus': 'Tursiops truncatus'}
APPROVED_FUZZY = {'Leptonychotes weddelli', 'Ommatophoca rossi'}
DISPLAY_NAMES = {'Stenella frontalis': 'Atlantic spotted dolphin', 'Tursiops aduncus': 'Indo-Pacific bottlenose dolphin',
                 'Monodon monoceros': 'Narwhal', 'Stenella clymene': 'Clymene dolphin',
                 'Arctocephalus forsteri': 'New Zealand fur seal'}


def load(name):
    return json.loads((INPUT / name).read_text())


def valid_coordinate(lon, lat):
    return math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90


def resolve_species(raw, matches, accepted):
    """Explicit spelling repairs, accepted synonyms, and species-level collapse."""
    name = ' '.join(raw.split())
    if name in NOISE:
        return None
    name = CORRECTIONS.get(name, name)
    match = matches[name]
    if match.get('matchType') != 'EXACT' and name not in APPROVED_FUZZY:
        raise ValueError(f'Unreviewed taxonomy match: {raw}')
    taxon = accepted[str(match.get('acceptedUsageKey', match['usageKey']))]
    return taxon['species'], str(taxon['speciesKey']), taxon['family']


def archive_groups(records, resolve):
    """Count distinct archive IDs at each coordinate and species, not animals."""
    groups = {}
    mapped_ids = set()
    for row in records:
        taxa = {resolve(x['name'])[0] for x in row['animal'].get('genus', []) if resolve(x['name'])}
        if not taxa:
            continue
        for c in row.get('location', {}).get('coordinates', []):
            key = (float(c['lon']), float(c['lat']))
            if not valid_coordinate(*key):
                continue
            item = groups.setdefault(key, {'ids': set(), 'taxa': defaultdict(set), 'names': set(),
                                           'raw_names': set()})
            item['ids'].add(row['record_number'])
            mapped_ids.add(row['record_number'])
            item['names'].update(row['location'].get('name', []))
            item['raw_names'].update(x['name'] for x in row['animal'].get('genus', []))
            for name in taxa:
                item['taxa'][name].add(row['record_number'])
    return groups, mapped_ids


def build():
    matches, accepted, common = load('taxonomy-gbif.json'), load('taxonomy-accepted.json'), load('taxonomy-common.json')
    species = {}
    def resolve(raw):
        if raw in species:
            item = species[raw]
            return raw, item['gbif_key'], item['family']
        result = resolve_species(raw, matches, accepted)
        if result:
            name, key, family = result
            taxon = accepted.get(key, {})
            names = common.get(key, [])
            vernacular = taxon.get('vernacularName') or next((x['vernacularName'] for x in names
                         if x.get('preferred')), names[0]['vernacularName'] if names else name)
            vernacular = DISPLAY_NAMES.get(name, vernacular)
            species.setdefault(name, {'scientific': name, 'common': vernacular, 'gbif_key': key, 'family': family,
                'group': 'Seals, sea lions & walrus' if family in {'Phocidae', 'Otariidae', 'Odobenidae'}
                         else 'Sea otter' if family == 'Mustelidae' else 'Whales, dolphins & porpoises',
                'raw_names': set()})['raw_names'].add(raw)
        return result

    points = []
    def add(label, dataset, lon, lat, kind, taxa, source, note='', counts=None, units=None, extra=None):
        assert valid_coordinate(lon, lat), (label, lon, lat)
        names = sorted({resolve(t)[0] for t in taxa})
        points.append({'id': len(points), 'label': label, 'dataset': dataset,
            'lon': round(lon, 6), 'lat': round(lat, 6), 'kind': kind, 'species': names,
            'source': source, 'note': note, 'counts': counts or {}, 'units': units,
            **(extra or {})})

    archive = load('watkins-rows.json')
    groups, mapped_ids = archive_groups(archive, resolve)
    for (lon, lat), group in sorted(groups.items()):
        names = sorted(group['names'])
        add(min(names, key=len) if names else f'Unnamed archive region ({lat:g}°, {lon:g}°)', 'Watkins archive (2019 metadata mirror)',
            lon, lat, 'archive', list(group['taxa']), 'https://marine-mammal.soundwave.cl/data.html',
            'Coarse archive/mirror coordinates; some recordings are captive. Multiple locations or species can refer to the same record.',
            {name: len(ids) for name, ids in group['taxa'].items()}, 'archive records',
            {'records': len(group['ids']), 'raw_species': sorted(group['raw_names']), 'location_names': names})

    frame = pl.read_csv(ROOT / 'data/input/dclde/Annotations.csv', columns=['Provider', 'Dataset', 'Soundfile', 'ClassSpecies'])
    table = json.loads((ASSETS / 'dclde-deployment-table.json').read_text())
    deployments = deployment_join(frame, table)
    grouped = {}
    for row in deployments:
        if row['longitude'] is None:
            continue
        counts = Counter(frame.filter((pl.col('Provider') == row['Provider']) &
                         (pl.col('Dataset') == row['Dataset']))['ClassSpecies'].to_list())
        key = (row['longitude'], row['latitude'], row['coordinate_status'])
        g = grouped.setdefault(key, {'labels': set(), 'datasets': [], 'counts': Counter()})
        g['labels'].add(row['location']); g['datasets'].append(row['Dataset']); g['counts'].update(counts)
    class_taxon = {'KW': 'Orcinus orca', 'HW': 'Megaptera novaeangliae'}
    for (lon, lat, status), group in grouped.items():
        counts = {class_taxon[k]: v for k, v in group['counts'].items() if k in class_taxon}
        add(' / '.join(sorted(group['labels'])), 'DCLDE NE Pacific: ' + ', '.join(group['datasets']),
            lon, lat, 'regional' if status == 'approximate_region' else 'published', list(counts),
            TABLE_SOURCE, 'Published deployment position or authors’ regional center; annotations are not animal counts.',
            counts, 'annotation rows', {'sound_classes': dict(group['counts'])})

    madeira = defaultdict(list)
    for row in load('madeira-rows.json')[1:]:
        if row.get('D'):
            madeira[(float(row['H']), float(row['G']))].append(row)
    for (lon, lat), rows in madeira.items():
        counts = Counter(resolve(r['A'])[0] for r in rows)
        add('Madeira · ' + ', '.join(r['D'] for r in rows), 'Madeira odontocete recordings', lon, lat,
            'published', [r['A'] for r in rows], 'https://zenodo.org/records/17952229',
            'GPS of initial sighting; not acoustic localization of the caller.', dict(counts), 'recordings')

    add('Dominica · west-coast study region', 'DSWP / sperm-whale combinatoriality', -61.40, 15.30,
        'regional', ['Physeter macrocephalus'], 'https://www.nature.com/articles/s41598-025-23733-1',
        'Named-island anchor for the west-coast study region; no coda-level GPS joined. These datasets overlap.')
    add('Eilat · Dolphin Reef', 'OpenWhistle · four overlapping configurations', 34.94, 29.52,
        'regional', ['Tursiops truncatus', 'Tursiops aduncus'], 'https://arxiv.org/html/2609.34839v1',
        'Approximate site anchor. Both species are reported corpus participants; clips have no individual species assignments.',
        extra={'coordinate_source': 'https://www.int-res.com/articles/suppl/m12348_supp.pdf'})
    add('Brittany · off Pointe de Penmarc’h', 'DOLPHINFREE', -4.36667, 47.8,
        'regional', ['Delphinus delphis'], 'https://essd.copernicus.org/articles/17/4495/2025/',
        'Approximate coastal anchor for offshore recordings, not vessel GPS.',
        extra={'coordinate_source': 'https://www.geonames.org/2988087/point-penmarc-h.html'})
    add('Florida · Sarasota Bay', 'Sarasota Dolphin Whistle Database',
        (-82.7801804-82.4636148)/2, (27.62003718+27.23144648)/2, 'regional', ['Tursiops truncatus'],
        'https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2022.923046/full',
        'Approximate regional anchor from NOAA shoreline bounding-box center. Audio access is by request.',
        extra={'coordinate_source': 'https://www.fisheries.noaa.gov/inport/item/61414'})

    hfm = [('Southern California Bight · HARP', 32+22.19/60, -(118+33.89/60)),
           ('Hoke Seamount', 32+6.37/60, -(126+54.58/60)),
           ('Aleutian Islands', 52+19.01/60, 178+31.24/60),
           ('Gulf of California', 23+49.45/60, -(109+37.67/60)),
           ('Washington Coast', 48+20.25/60, -(125+12.52/60)),
           ('Southern California Bight · FLIP', 33+2.44/60, -(118+41/60))]
    for label, lat, lon in hfm:
        add(label, 'Killer-whale high-frequency modulated signals', lon, lat, 'published', ['Orcinus orca'],
            'https://www.cetus.ucsd.edu/docs/publications/SimonisJASA2012.pdf',
            'Table 1 recording position; contour archive not downloaded. No local contour counts.',
            extra={'dataset_source': 'https://datadryad.org/dataset/doi:10.5061/dryad.8cz8w9h7f'})
    site_counts = load('sanctsound-site-counts.json')
    marker_args = load('sanctsound-hawaii-markers.json')['args']
    for code, lat, lon in zip(marker_args[10], marker_args[0], marker_args[1]):
        if code not in site_counts:
            continue
        add('Hawaiʻi · ' + code, 'SanctSound humpback DAC9 tokens', lon, lat, 'published',
            ['Megaptera novaeangliae'], 'https://sanctsound.ioos.us/s_hihwnms.html',
            'Published hydrophone position. Derived token metadata entries, not independently annotated whale calls.',
            {'Megaptera novaeangliae': site_counts[code]}, 'token-metadata entries',
            {'dataset_source': 'https://huggingface.co/datasets/cairninstitute/mmc-sanctsound-humpback-dac9'})
    for row in load('das-region-centers.json'):
        add('Oregon · ' + row['dataset'], 'DCLDE fin-whale DAS localization', row['longitude'], row['latitude'],
            'regional', ['Balaenoptera physalus'], row['source'],
            'Centroid of published cable geometry; species is the challenge target, not a verified detection here.',
            extra={'sensors': row['sensors'], 'bounds': row['bounds']})
    for row in load('cape-cod.json')['DEPLOYMENT']['LOCATIONS']:
        add('Cape Cod Bay · channel ' + row['CHANNEL'], 'DCLDE right-whale array / detection surveys',
            float(row['LONGITUDE']), float(row['LATITUDE']), 'published', ['Eubalaena glacialis'],
            'https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde2027_acoustic_monitoring_in_cape_cod_bay/metadata/DCLDE2026_Acoustic_Monitoring_in_Cape_Cod_Bay.json?generation=1774651626804496',
            'Published MARU position. Right whale is the challenge target; no per-sensor annotation counts joined.')

    # Keep only taxa with a mapped location; retain original labels for audit.
    mapped_taxa = {s for point in points for s in point['species']}
    unmapped_taxa = sorted(set(species) - mapped_taxa)
    for name in list(species):
        if name not in mapped_taxa:
            del species[name]
        else:
            species[name]['raw_names'] = sorted(species[name]['raw_names'])
            species[name]['locations'] = sum(name in point['species'] for point in points)
    summary = {'species': len(species), 'location_entries': len(points),
        'distinct_coordinates': len({(p['lon'], p['lat']) for p in points}),
        'kinds': dict(Counter(p['kind'] for p in points)),
        'species_groups': dict(Counter(s['group'] for s in species.values())),
        'watkins_total_records': len(archive), 'watkins_mapped_animal_records': len(mapped_ids),
        'watkins_records_with_coordinates': sum(bool(r['location'].get('coordinates')) for r in archive),
        'watkins_map_locations': len(groups), 'madeira_recordings': sum(len(v) for v in madeira.values()),
        'unmapped_species_without_coordinate_join': unmapped_taxa,
        'sanctsound_metadata_entries': sum(site_counts.values()), 'sanctsound_card_declared_entries': 488320,
        'dclde_coverage_annotations': dict(Counter({status: sum(r['annotations'] for r in deployments
            if r['coordinate_status'] == status) for status in {r['coordinate_status'] for r in deployments}})),
        'dclde_classes': dict(Counter(frame['ClassSpecies'].to_list())),
        'catalogue_entries': 16, 'retrieved': '2026-10-07'}
    data = {'summary': summary, 'species': sorted(species.values(), key=lambda s:s['common'].lower()), 'points': points}
    ASSETS.mkdir(exist_ok=True); OUTPUT.mkdir(parents=True, exist_ok=True)
    (ASSETS / 'world-map-data.json').write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False)+'\n')
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    geo = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties':
           {k:v for k,v in p.items() if k not in {'lon','lat'}}, 'geometry': {'type': 'Point',
           'coordinates': [p['lon'], p['lat']]}} for p in points]}
    (OUTPUT / 'locations.geojson').write_text(json.dumps(geo, ensure_ascii=False)+'\n')
    with (OUTPUT / 'species-locations.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, ['species','common_name','location','dataset','longitude','latitude','coordinate_kind','count','units','source'])
        writer.writeheader()
        for p in points:
            for s in p['species']:
                writer.writerow(dict(species=s, common_name=species[s]['common'], location=p['label'], dataset=p['dataset'],
                    longitude=p['lon'], latitude=p['lat'], coordinate_kind=p['kind'], count=p['counts'].get(s),
                    units=p['units'], source=p['source']))
    files = [*INPUT.glob('*'), ROOT/'data/input/dclde/Annotations.csv', ASSETS/'world-countries-110m.geojson',
             ASSETS/'dclde-deployment-table.json']
    hashes = {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in files if p.is_file()}
    provenance = {'retrieved': '2026-10-07', 'files': hashes, 'taxonomy_match_api': 'https://api.gbif.org/v1/species/match',
        'taxonomy_usage_api': 'https://api.gbif.org/v1/species/',
        'world_basemap': 'https://esm.sh/@d3-maps/atlas@1.0.0/world/countries/countries-110m',
        'watkins_metadata': 'https://marine-mammal.soundwave.cl/wmmsdb.20190601.b32a76a.json.xz',
        'watkins_geography': 'https://marine-mammal.soundwave.cl/wmmsdb.v20190517.geojson.xz',
        'madeira_metadata': 'https://zenodo.org/api/records/17952229/files/Metadata.xlsx/content',
        'sanctsound_metadata': 'https://huggingface.co/datasets/cairninstitute/mmc-sanctsound-humpback-dac9/resolve/main/metadata/chunk_scores.csv'}
    (ASSETS/'world-map-provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


def render_fragment(destination):
    """Embed saved metadata and published geometry into the literal template."""
    template = (ASSETS / 'world-map-template.html').read_text()
    for placeholder, filename in [('__WORLD_DATA__', 'world-map-data.json'),
                                  ('__WORLD_GEOGRAPHY__', 'world-countries-110m.geojson')]:
        template = template.replace(placeholder, (ASSETS/filename).read_text().replace('</', '<\\/'))
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--visualization', help='Optional absolute output path for the map fragment')
    args = parser.parse_args()
    build()
    if args.visualization:
        render_fragment(args.visualization)
