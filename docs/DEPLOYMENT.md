# Vercel deployment

Intended production domain: https://denver.mattvildibill.com
Source: https://github.com/mattvildibill/denver-spire-explorer
Production branch: `main`.

`vercel.json` records the framework, build and output settings. Import this exact repository into Vercel and retain its Git connection. Vercel builds each push to `main`; other branches receive previews. No manual asset copy or Sites publishing is needed. Domain attachment and automatic deployment must be verified in Vercel before this migration branch is promoted.

Use Node.js 24. Run `npm ci` when a lockfile is present, then `npm run build`. No application secrets or database are required. Never commit `.env` files or Vercel credentials.

The portfolio launches one iframe at a time. Each project owns its runtime and assets. The embed bridge validates its parent origin; closing the viewer destroys the iframe and stops its work. Headers allow embedding from the portfolio. Original project attributions and model boundaries are retained.

Existing ChatGPT-hosted versions have not been deleted or redirected. Keep them online until the new production domains pass verification. If redirects are later installed on old hosts, preserve paths and query parameters.

## Assets

`asset-bundles/` stores lossless, SHA-256-verified assets recovered from the original source. `npm run assets:restore` restores them to their original paths; the build runs it automatically. Text source remains directly editable. Restore refuses to overwrite a modified local asset. To replace an asset, update and repack the bundles with `python scripts/pack-assets.py`; commit the resulting bundles and manifest.
