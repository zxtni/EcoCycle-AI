# Final verification report

## Implemented

EcoCycle AI includes email/password sessions, citizen and municipality roles, photo analysis with CPU ONNX inference, saved corrections, versioned value and impact estimates, recycling history, streaks and badges. The locator combines Overpass results with local listings on a clustered Leaflet map. Municipal tools include date-filtered summaries, CSV and PDF exports, weekly hotspot scenarios and a suggested stop sequence. Administration includes center CRUD, feedback review, forecast retraining and audit history. The installable PWA provides a cached offline page.

## Verified

A fresh Git clone installed dependencies, applied migrations and loaded demo data using `node scripts/setup.mjs`. Python lint, mypy, nine API and calculator tests, frontend lint, TypeScript, the frontend unit test and a production build all passed with `node scripts/check.mjs`. Playwright passed at widths of 375 and 390 pixels using locally installed Brave. Both runs signed in, uploaded a real image, detected plastic, saved an impact record and reached the locator results. Additional local API checks verified the seeded administrator, the 16 demo records, model metrics, center creation/edit/removal and audit entries. A fresh forecast retrain reproduced the saved metrics.

## Additional production-build checks

- Mobile Lighthouse on the production overview using Brave scored **96 performance, 100 accessibility and 96 best practices**. These are automated scores for the overview under local test conditions.
- A fresh UTF-8 PostgreSQL 17.12 instance applied Alembic revision 001 and seeded 16 scan records.
- Playwright on the production build captured a photo using a virtual camera, confirmed the standalone PWA manifest and verified that offline navigation served the cached fallback.

## Measured models

| Evaluation | Result |
| --- | --- |
| Scanner on held-out target-class photos | 400/521 correct, 76.8% top-label accuracy including abstentions |
| Scanner on the small TACO street benchmark | 1/36 correct detections at IoU 0.50, 2.8% recall |
| Seasonal forecast on 312 held-out simulated ward-weeks | MAE 1,564.57 kg, RMSE 2,144.14 kg |

The scanner is suited to close photos of visible objects. The gap on street images limits its use for surveying litter. Forecast error measures the simulated Bengaluru task derived from historical measured Austin collections. Real Bengaluru forecast accuracy remains unknown. See [MODEL_CARD.md](MODEL_CARD.md) and [forecast method](docs/forecast-method.md).

## Synthetic and estimated inputs

Demo accounts, saved demo scans, local sample collection points and Bengaluru ward forecasts are synthetic. Citizen benefit estimates use published representative factors and self-reported recycling activity. Sample collection points suppress directions. OpenStreetMap and observed Austin collection weights are external data sources.

## Deployment and verification limits

The application runs on the Ubuntu VPS at https://eco.zxtni.in with Supabase PostgreSQL. Live registration, scanning and impact saving have been verified. Production administrator access, physical-device camera and installation still require verification. The browser walkthrough verifies locator rendering and can use seed listings when Overpass is unavailable. Local Playwright used Brave. Formal WCAG AA conformance remains unaudited. The hotspot map uses intensity-scaled ward circles, and suggested stops use straight-line distance. The rate limiter is per API process.

## Commands

```sh
node scripts/setup.mjs
node scripts/dev.mjs
node scripts/check.mjs
pnpm --dir web exec playwright install chromium
pnpm --dir web run e2e
node scripts/retrain.mjs
docker compose up --build
```

For production, import the Render Blueprint, set the database and web-origin variables, deploy the Vercel project from `web/`, then provision the first administrator with `python -m backend.provision`. Follow [DEPLOY.md](DEPLOY.md).

