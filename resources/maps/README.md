# Dataset map sources

The [world-map guide](../../docs/world-map.md) describes the full catalogue map,
metadata downloads, coordinate meaning, species normalization, and exclusions.
`world-map-data.json` contains 44 species and 172 location entries;
`world-map-provenance.json` records snapshot hashes and source endpoints.
`world-countries-110m.geojson` is the pinned published atlas geometry, converted
to GeoJSON. `world-map-template.html` is the editable map fragment template;
`dataset_world_map.py` embeds the saved metadata and geometry when requested.

## DCLDE deployment map

Retrieved 7 October 2026 for the metadata-only summary dashboard.

- `dclde-deployment-table.json`: provider, location, dataset, latitude, longitude
  cells from [Table 1 of the dataset descriptor](https://www.nature.com/articles/s41597-025-05281-5/tables/1).
  Blank provider/location cells were forward-filled; coordinate text remains as
  published, including Unicode minus signs and `NA`.
- `dclde-basemap.geojson`: a JSON dictionary of regional GeoJSON feature
  collections and clipping bounds. Published Natural Earth 1:10m country
  polygons for Canada and the USA were clipped to the Pacific Northwest,
  southern Alaska, and Salish Sea, simplified with topology-preserving tolerance
  0.002 degrees using Shapely, and exterior rings oriented clockwise for D3.
  Source: [Natural Earth GeoJSON](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_0_countries.geojson).
  Natural Earth geometry is [public domain](https://www.naturalearthdata.com/about/terms-of-use/).
  The locally saved geometry is the fixed dashboard input; upstream `master`
  may change. Hashes and crop parameters are in `provenance.json`.

`dclde_visuals.deployment_join` joins on both provider and dataset. Provider
aliases are `JASCO/VPFA` → `JASCO_VFPA`, `JASCO/VPFA/ONC` → `JASCO_VFPA_ONC`,
`SMRU` → `SMRUConsulting`, `Orca Sound` → `OrcaSound`, `DFO CRP` → `DFO_CRP`,
and `DFO WDLP` → `DFO_WDLP`. Dataset aliases are `LmKln` → `LimeKiln`,
`BerkleyCanyon` → `BarkleyCanyon`, `NorthBC` → `NorthBc`, and `StrGeosS2` →
`StrGeoS2`. Each is an identifier spelling adjustment, not a coordinate estimate.

DFO coordinates are withheld. The source repeats `StrGeoN1` for its North 2
row; no coordinate is inferred from that duplicated identifier or from a place
name. The CSV's `StrGeoN2` remains withheld.

The source gives `RB_67424266` latitude 59.733, longitude **+149.53**, while
another Resurrection Bay deployment uses **−149.53**. The positive sign places
it outside Alaska. Five associated annotation rows are excluded from mapping;
the original positive value remains in the exported source-coordinate columns.
We do not silently repair it.

`Field_HTI` and `Field_SondTrap` use the authors' approximate central coordinate
for focal-follow recordings in Kenai Fjords / Prince William Sound. They are
aggregated as a diamond, separately from fixed instruments. Published fixed
coordinates are rounded and are not precise animal positions.
