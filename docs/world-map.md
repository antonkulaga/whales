# Marine-mammal dataset world map

Open the saved [interactive world map](maps/world-map.html) in a browser. It
lives under `docs/maps/` so Git can include it alongside this guide.

For the proposed next step—location → recording → playable event → annotation
→ artwork—see the [map/audio investigation](2026-art-ideas.md#4-connect-the-map-to-audio-and-annotations).
The [existing-project review](cetacean-art-precedents.md) discusses Pattern Radio
and Tay Fins; the [2026 model audit](2026-art-models.md) covers representations
for a linked sound-similarity view. Those interactions extend the present map
and are not implemented by this documentation update.

Metadata inspection on **7 October 2026** covers the project's 16 catalogue
entries. The downloadable DCLDE Northeast Pacific annotation CSV identifies
**orca and humpback whale**; `UndBio` and `AB` are unidentified biological and
abiotic sound classes. The wider catalogue supports a much broader comparison.

The world map contains **44 identified species at 172 coordinate/region
entries**: 34 whale, dolphin and porpoise species and 10 seal, sea-lion and walrus
species. There are **233 species/location associations**, because one location
can contain several species. These are dataset locations, not species ranges,
animal positions, animal counts, or comparable measures of recording effort.

## Coverage and coordinate meaning

| Source | Map entries | Species/location evidence |
|---|---:|---|
| Watkins metadata mirror | 107 | Archive species labels and coarse coordinates; historical wild and captive recordings |
| DCLDE NE Pacific combined CSV | 17 | Published deployment coordinates and one authors' regional center; includes every sound class at mapped deployments |
| Madeira recordings | 27 | 35 recordings at initial-sighting GPS positions, covering seven species |
| Killer-whale high-frequency modulated signals | 6 | Published recording locations; contour archive not downloaded |
| Cape Cod Bay right-whale tasks | 5 | Published MARU positions; right whale is the challenge target |
| SanctSound humpback DAC9 | 4 | Actual source sites represented in token metadata; published hydrophone coordinates |
| Oregon fin-whale DAS | 2 | Cable centroids derived from downloaded geometry; fin whale is the challenge target |
| DSWP / sperm-whale combinatoriality | 1 | Approximate Dominica region; datasets overlap, no coda-level GPS join |
| OpenWhistle configurations | 1 | Approximate Dolphin Reef, Eilat location; two reported corpus-participant species, no per-clip species assignments |
| DOLPHINFREE | 1 | Approximate offshore Brittany region anchored to Pointe de Penmarc'h |
| Sarasota Dolphin Whistle Database | 1 | Approximate bay region; audio access by research request |

Published positions use circles; archive approximations and regional anchors
use diamonds with distinct colors. Equal marker sizes avoid comparing archive
cuts, annotation rows, recordings and token chunks as if they were the same unit.
Species selection narrows the points; location selection provides a keyboard
alternative to densely overlapping map markers. Selection details retain the
unit and distinguish reported corpus/target species from joined annotations.

### Watkins metadata

The [2019 metadata mirror](https://marine-mammal.soundwave.cl/data.html)
provides downloadable JSON and GeoJSON independently of audio. We retrieved
both compressed metadata files; the original WHOI archive currently redirects
to a maintenance page. This mirror also adds geographic information, so its
coordinates are explicitly treated as archive approximations rather than
verified original instrument GPS.

There are **15,254 unique archive records**, of which **13,910** contain
coordinates. **13,835 animal-labelled records** contribute mapped species after
excluding non-animal/unlabelled records. Each record is counted once per
coordinate and species. Records can have multiple coordinates or species:
location/species counts must not be summed to recover the unique archive total.
Source location names and taxon labels remain available in the saved map data.

Across the inspected metadata, **55 normalized species** are represented;
**11 have no coordinate join** and are excluded from this map: *Arctocephalus
philippii*, *Cephalorhynchus heavisidii*, *Cystophora cristata*, *Enhydra lutris*,
*Eumetopias jubatus*, *Halichoerus grypus*, *Inia geoffrensis*, *Neophocaena
phocaenoides*, *Phoca vitulina*, *Sotalia fluviatilis*, and *Sousa chinensis*.
Some have named places that could be geocoded in a later pass; we have not
silently assigned coordinates to those records. One harbour-seal source label
mixes “Marine Land of the Pacific” with “San Diego” and needs review.

Taxon normalization uses saved [GBIF API](https://techdocs.gbif.org/en/openapi/v1/species)
responses, accepted synonyms, and species-level collapse of subspecies. Reviewed
spelling repairs include `Leptonychotes weddelli`, `Ommatophoca rossi`, and three
Madeira spreadsheet typos. `Delphinus bairdii` collapses to *D. delphis*;
`Physeter catodon` to *P. macrocephalus*. Historical archive identifications have
not been reidentified using current geographic species boundaries. English
display names use GBIF with five explicit readability corrections; scientific
names are the map's taxon keys.

### Other sources and exclusions

- [DCLDE descriptor Table 1](https://www.nature.com/articles/s41597-025-05281-5/tables/1):
  38,287 mapped annotation rows, including 8,078 with the authors' approximate
  regional center. **169,282 rows have withheld DFO coordinates**; five rows
  have a source longitude sign inconsistent with Alaska. The existing
  [DCLDE join rules](../resources/maps/README.md) remain in effect.
- [Madeira metadata](https://zenodo.org/records/17952229): `Metadata.xlsx` is
  36,345 bytes. Initial-sighting GPS is not the location of a localized caller.
- [Simonis et al., Table 1](https://www.cetus.ucsd.edu/docs/publications/SimonisJASA2012.pdf):
  degree/minute positions converted to decimal degrees. The Aleutian site is
  **178°31.24′ E**, not west longitude. The 5.99 GB contour/audio ZIP was not downloaded.
- [SanctSound Hawaii site map](https://sanctsound.ioos.us/s_hihwnms.html):
  published coordinates extracted from the site's embedded Leaflet data.
  The complete **53,875,749-byte**
  [chunk-scores CSV](https://huggingface.co/datasets/cairninstitute/mmc-sanctsound-humpback-dac9/resolve/main/metadata/chunk_scores.csv)
  contains **485,811 metadata entries**, while the model card declares 488,320.
  Actual source codes are HI01 (146,087), HI03 (97,758), HI04 (235,878), HI05
  (6,088). Other SanctSound sites are not assigned to this token corpus.
- Cape Cod Bay positions come from the generation-pinned NOAA deployment JSON
  linked in each map entry. Audio and detection catalogue entries share these
  five sensors and are represented once.
- Oregon north/south DAS geometry CSVs were downloaded completely, about
  **10.2 MB combined**. Centroids represent 31,518 and 46,440 cable sensors,
  respectively; they are not localized fin-whale detections.
- [Dominica study](https://www.nature.com/articles/s41598-025-23733-1): regional
  anchor at 15.30° N, 61.40° W; no alignment between DSWP clips and coda tables.
- [OpenWhistle paper](https://arxiv.org/html/2609.34839v1): resident
  *Tursiops truncatus* and an intermittently present *T. aduncus* female are
  reported corpus participants. Approximate Dolphin Reef anchor rounded to
  29.52° N, 34.94° E from the named-site
  [supplementary coordinates](https://www.int-res.com/articles/suppl/m12348_supp.pdf).
- [DOLPHINFREE descriptor](https://essd.copernicus.org/articles/17/4495/2025/):
  offshore Penmarc'h region, anchored to
  [GeoNames](https://www.geonames.org/2988087/point-penmarc-h.html), 47.8° N, 4.36667° W.
- [Sarasota database paper](https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2022.923046/full):
  Sarasota Bay, with an approximate anchor computed from the bounding-box
  center of [NOAA's bay shoreline metadata](https://www.fisheries.noaa.gov/inport/item/61414).
  This is an explicit regional inference, not a database recording coordinate.

All new downloads for this map are metadata or geographic geometry. No new
audio or token TAR shard was downloaded. Metadata, audio, model weights and
software have separate reuse terms; the catalogue's access/license notes still apply.

## Saved data and rebuilding

`dataset_world_map.py` reads the downloaded snapshots under
`data/input/world-map/`, the full DCLDE CSV, and the saved deployment table. It
has no network calls. File sizes and SHA-256 hashes are in
`resources/maps/world-map-provenance.json`. Aggregated metadata and the literal
map template are tracked; larger raw downloads and generated exports are ignored.

```bash
uv run python dataset_world_map.py
uv run python dataset_world_map.py --visualization /absolute/output/world-map.html
uv run python -m unittest tests.test_world_map tests.test_dclde tests.test_cli
```

Outputs:

- `docs/maps/world-map.html`: saved standalone browser copy of the
  interactive world map, including embedded metadata and geographic geometry.
  The D3 library loads from its pinned CDN URL.
- `resources/maps/world-map-data.json`: species inventory, original labels,
  map points, source links, counts with units, and coverage audit.
- `data/output/world-map/summary.json`: summary and coordinate exclusions.
- `data/output/world-map/species-locations.csv`: one row per species/location.
- `data/output/world-map/locations.geojson`: WGS84 point features, including
  approximate anchors and their provenance.

The world basemap is the pinned
[`@d3-maps/atlas` 1.0.0 countries-110m](https://esm.sh/@d3-maps/atlas@1.0.0/world/countries/countries-110m)
Topology converted with `topojson-client` 3.1.0. Saved GeoJSON contains 177
features with ISO3 `properties.id`; it is embedded with metadata so viewing
the map requires no data API requests.
