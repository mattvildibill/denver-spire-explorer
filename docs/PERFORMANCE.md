# Loading and device performance

## What changed

The portfolio links directly to `https://denver.mattvildibill.com`; it does not run Denver inside an iframe. Denver owns its loading, graphics and touch controls. The portfolio also offers a direct lightweight-map link.

The previous explorer downloaded all city geometry, a 3268 × 4000 aerial image, photo materials and HDR lighting before starting. It copied those assets into base64 DOM strings and retained a second full offline document. Every frame redrew the scene and its shadows even when idle. Touch controls were only styled at phone widths, leaving wider tablets without movement controls.

- Phones, tablets, low-memory devices and data-saving connections default to Light. An explicit `?quality=low`, `balanced`, or `high` overrides automatic selection.
- Light preserves all mapped building geometry, six destinations, walking collisions, tours and layers. Four inferred decorative mesh batches are omitted: sandstone surrounds, anodized aluminium, recessed glazing and street furniture. High retains all original detail.
- Geometry is indexed using exact full-attribute vertex records. Triangle order, positions, normals, UVs and ambient visibility are verified byte-for-byte for every retained triangle.
- Light and Balanced use a committed 2048-pixel aerial derivative. Full-resolution imagery, photo materials, HDR lighting and district reflection capture are reserved for High.
- Hosted assets stay binary, download through a three-request queue, retry once, and have bounded per-request timeouts. The offline edition is generated as a separate download; it is never reconstructed or retained in the active viewer.
- WebGL and decompression support are checked before city-asset downloads. `?view=map` bypasses 3D entirely, retaining the footprint map and six destinations. Failed or lost graphics contexts also fall back to that map.
- The GPU renders only when camera, UI or atmosphere changes, or a tour is active. Tree LOD and camera-following shadows update less often. Rendering quality can reduce automatically after sustained slow frames.
- Touch controls are available on coarse-pointer tablets at desktop widths; low-height landscape layouts give more space to the scene. Photo quality remains an explicit choice in Help and reloads the page.

## Reproducible budgets

These are uncompressed HTTP asset-file sizes, not measured cellular transfer times or whole-process memory usage. HTTP text compression and caching will vary.

| Measure | Previous | Light | Balanced |
| --- | ---: | ---: | ---: |
| Initial city assets | 23,738,074 bytes | 9,058,947 bytes | 13,822,281 bytes |
| Decoded geometry | 69,879,040 bytes | 26,509,688 bytes | 51,654,368 bytes |
| Geometry vertices | 1,940,922 | 616,064 | 1,218,996 |
| Geometry triangles | 646,974 | 360,474 | 646,974 |

The full indexed geometry compresses slightly less efficiently (12,024,047 versus 11,292,660 bytes); its benefit is lower decoded/GPU vertex memory. The smaller imagery and omitted startup photo payload still reduce Balanced's initial asset total. The hosted HTML is below 850 KB, with the application bundle cached separately. Fingerprinted assets use immutable caching.

## Build and checks

Use Node.js 24 and Python 3:

```
npm run build
npm run check
```

The build restores verified original assets, generates deterministic indexed profiles with standard-library Python, bundles the app, and produces `dist/index.html`, local asset chunks and `dist/offline.html`. The original source assets and photo attribution remain available. The aerial derivative is tracked, so Vercel does not require Pillow. Run the build before serving `dist` from a fresh checkout.

Checks cover navigation/collision, all six tour stops, material shader construction, map fallback/focus, controls and layers, exact geometry reconstruction, malformed input, deterministic builds, quality selection, download concurrency/retry/error behavior, size budget and the actual render loop's idle/movement/visibility transitions.

Cloud Chromium cannot create a WebGL context in this verification environment. Its map fallback can be checked, but that does not establish GPU rendering correctness, frame rate, or physical iPhone/iPad Safari behavior. Physical-device testing remains a verification limit; no universal frame-rate guarantee is made.
