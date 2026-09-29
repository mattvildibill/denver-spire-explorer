# Denver Explorer

A free, self-contained 3D city explorer built from Blender geometry, Denver open building data, OpenStreetMap, and public-domain USDA NAIP aerial imagery.

Open `exports/Denver_Explorer_Offline.html` in a current desktop browser after running the build script. The hosted entry is `dist/index.html`; it loads only local static asset chunks. The downloaded HTML requires no server, network, account, API key, trial or paid asset. The hosted website requires an internet connection. The hosted version contains the same standalone document. External Street View links open Google's own service and need internet; its content is not copied or embedded.

## Controls

- **Fly:** drag to look; WASD or arrows to move; Q/E lower/rise; Shift faster; scroll forward/backward.
- **Walk:** 1.72 m eye height; WASD/arrows; building collision checks and safe landmark approaches.
- **Touch:** left joystick to move, drag the scene to look; +/− altitude buttons in flight.
- Landmark buttons, north-up clickable minimap, building inspection, full-district aerial, six-stop guided cinematic tour, current-view link, and offline download.

The standalone HTML embeds all geometry, aerial pixels, the Three.js runtime, and credits. It does not call a map service during exploration. Mobile file preview apps may not execute downloaded HTML; desktop browsers are the dependable offline option.

## Geographic basis

Local WGS84 azimuthal equidistant projection centered on Spire, longitude −104.99562, latitude 39.74484. Blender: +X east, +Y true north, +Z up, metres. Viewer: x=X, y=Z, z=−Y. Bounds −105.003/39.740/−104.986/39.756, about 2.6 km². Camera coordinates convert back to WGS84 through a Vincenty direct solution, verified against pyproj.

There are 530 source building groups and 1,916 source roof sections. The mapped galleria canopy is treated as suspended and its inferred curved profile uses the city's approximately 80 ft crown reference. Spire's roof profile is scaled to a 147.2 m crown, with the priority architectural detail retained from Blender.

## Accuracy and limits

This is a GIS reconstruction with photographic ground detail, not a hyperreal photogrammetric twin or survey. Facades, balcony modules, some trees and lamps are procedural/inferred. Ground is flattened. Roof data is principally 2022; aerial data is September 25, 2023; OSM source extract reports July 15, 2026. New construction, current shopfronts, the completed Mall renovation, detailed sculptures, interiors and every street fixture are not reconstructed. Orthoimagery includes shadows, building lean and acquisition seams. Low roofs use projected aerial color; high roofs keep neutral finishes to avoid gross displacement.

Walking checks roof footprints and respects holes and suspended structures; it is not a pedestrian accessibility or route-planning system. Flying allows movement through geometry. Older phones may need Light rendering quality.

## Sources and licensing

- City and County of Denver Building Outlines: https://www.arcgis.com/home/item.html?id=04e5069b4cf843d2bfe15ad0d1c66e00 . Anonymous public GIS. Source roof heights and ground elevation are in feet.
- © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright . Preserve attribution and source database terms when redistributing.
- USDA NAIP 2023 via Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/dataset/naip . Source imagery 30 cm, acquired September 25, 2023, resampled for this viewer. STAC records and download requests are in the Blender project. The collection's license link is explicitly titled “Public Domain” and points to USDA policies; its generic STAC `license` field says `proprietary`. USDA/USGS identify NAIP as public-domain imagery: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip . No commercial imagery or user credentials are used.
- Denver canopy reference: https://denverpublicart.org/for-artists/denver-performing-arts-complex-rfq/ . Approximately 80 ft crown; the exact curved section is inferred.
- Google Maps URL documentation: https://developers.google.com/maps/documentation/urls/get-started . External links need no API key. Google imagery is not part of the download.
- Three.js 0.180.0 and esbuild 0.25.10: MIT; full licenses in `vendor/`.
- Blender 4.5.3 LTS, Python, Shapely and pyproj are free/open source. Original viewer code is MIT; geographic datasets retain their separate source terms.

## Rebuild

The tracked hosted HTML and asset chunks are the source of truth for runtime assets; the build script extracts its local caches as needed. The cached Blender export is in `data/city.bin.gz`, the navigation database in `data/world.json`, and the compressed aerial image in `data/aerial.jpg`. Run:

```
python scripts/assemble.py
node scripts/check_navigation.mjs
```

The pinned Linux x64 esbuild executable is downloaded automatically from the public npm registry and hash-checked when rebuilding a fresh checkout; no npm install or account is required. Viewing remains fully offline. For another platform, use the same open-source esbuild release for that platform. `src/` contains all authored controls, styling, geometry loading and geography code. `data/verification.json` records geometry, landmark, collision, projection and self-containment checks. Browser interaction/performance testing was not available in this static-site build environment and is not claimed.

To regenerate the geometry, use `scripts/upgrade_export.py` in the companion Blender project. It reads the cached original scene, improves the materials/canopy, saves `Denver_Spire_Explorer.blend`, and exports material batches. Copy its `explorer/world.json` and `explorer/city.bin.gz` into this project's `data/`, then rebuild.


## Major exploration pass — September 2026

- Guided Spire → Convention Center → Performing Arts → Sculpture Park → Larimer Square → 16th Street tour, with a smooth elevated transfer, pause/resume, previous/next and free exploration. Approximately 108 seconds, with reduced-motion support and suspension while dialogs are open.
- Convention Center anchor derived from the 26 named mapped roof sections, not a guessed address pin. Existing Blender roof geometry and Spire’s 147.2 m modeled crown preserved.
- Search mapped building names, inspect individual height sources, visit the virtual Spire crown, or use the existing eye-level walking and free-flight modes.
- Connecting route computed over connected OpenStreetMap ways; 1.862 km between snapped network endpoints. Route overlays may use street centerlines and are not verified pedestrian or accessible directions.
- Official Denver statistical-neighborhood boundaries; distance rings at 100/250/500/1,000 m; one-batch roof-height overlay; source-linked historical/date context for each destination.
- Smooth illustrative day/night lighting, seasonal foliage color, more conservative glass metalness and district reflections on curtain walls. Geometry is unchanged; these are rendering improvements, not newly measured facades.
- Three foliage detail tiers (112/40/12 cards) selected by camera distance; nearby foliage and trunks cast shadows. Balanced rendering is the default. No performance benchmark on physical phones was available.
- Retried/timed local asset requests, optional photo-material fallback, and a north-up footprint map with an accessible destination list when WebGL initialization or its context fails.
- Larger controls and typography, keyboard focus outlines, associated form labels, mobile layout rules, and a concise first-visit introduction.

### Additional data

`data/routes_osm.json.gz` preserves the anonymous Overpass response, whose own timestamp is **2026-05-31T22:37:44Z**, downloaded September 9, 2026. It differs from the older model extract’s reported July 15, 2026 timestamp. OSM dates are source metadata, not a claim of a September field survey. Streets: https://overpass.private.coffee/api/interpreter (fallback: https://overpass.kumi.systems/api/interpreter); ODbL attribution applies.

`data/neighborhoods.geojson` preserves the public Denver query for statistical neighborhood layer 13: https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ADMN_NEIGHBORHOOD_A/FeatureServer/13 . Retrieved September 9, 2026. These are official statistical boundaries, not informal neighborhood identities or historic-district boundaries. Regenerate the locally projected overlay data with `node scripts/prepare_layers.mjs`. Projection inversion uses the existing WGS84 geodesic routine; coordinates are rounded to a millimeter, which does not imply millimeter source accuracy.

Historical source links live alongside each card in `src/exploration.js`. They provide factual context; no historical imagery or geometry is synthesized. Detailed Dancers and Blue Bear sculptures remain absent. The 2022 roof source does not fully capture the Convention Center’s later rooftop expansion, and the 2023 surface does not depict today’s completed 16th Street works. Terrain remains level.

### Validation

Run after `python scripts/assemble.py`:

```
node scripts/check_navigation.mjs
node scripts/check_realism.mjs
node scripts/check_exploration.mjs
node scripts/check_interactions.mjs
python scripts/check_shell.py
```

The checks cover binary geometry integrity, projection, walking collisions, all six tour legs at 1,086 camera samples, tour timing/pause/seek/completion, route connectivity, the Spire/CBD boundary lookup, shader-hook construction, UI control handlers, daylight/seasons, building search, form associations and local/offline assets. Six new historical/source links returned HTTP 200 during this pass.

**Testing limit:** interaction tests use a DOM adapter and real Three.js math/geometry, not an actual browser or GPU. This plain-static Sites project has no supported agent-preview server. Desktop/mobile visual layouts, real pointer/keyboard dispatch, GPU shader compilation, live performance, context-loss behavior and clipboard/file download execution could not be browser-tested here. They must not be described as a completed end-to-end browser pass.
