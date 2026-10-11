# Routine Irrigation Technology (software version)

AI-powered irrigation decision support for small farms in Cross River State, Nigeria. Built for the Junior Achievement Nigeria competition, Artificial Intelligence track.

It combines soil moisture, the local weather forecast, satellite crop-stress (NDVI), crop growth stage and last season's yield into one clear recommendation per field, explains **why** in plain language (English or Nigerian Pidgin), and keeps the farmer in control: accept, override or snooze, with every choice logged. Farmers can ask questions about any recommendation.

> **Honesty rule.** Wherever data is simulated (sensor stream, satellite fallback, scenario forecast) the UI says **Demo data** or **Simulated**. Nothing simulated is presented as real.

## Run it

```bash
# 1. Python
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Front-end assets (Tailwind CSS + vendored Alpine, Motion, Leaflet, fonts)
npm install
npm run vendor                    # also builds the tree-shaken Motion bundle (esbuild)
npm run build:css                 # or: npm run watch:css while editing templates

# 3. Database + demo farm
python manage.py migrate
python manage.py seed_demo

# 4. Go
python manage.py runserver        # http://127.0.0.1:8000
```

Or with Docker (Postgres included): `docker compose up --build`, then open http://localhost:8000.

Open the login page and press **Explore as a farmer** (no sign-up), or sign in with:

| Role | Email | Password |
|---|---|---|
| Farmer | `demo@irrigation.test` | `demo-pass-123` |
| Partner | `partner@irrigation.test` | `demo-pass-123` |
| Admin | `admin@irrigation.test` | `demo-pass-123` |

Pilot invite code for new sign-ups: `CALABAR2026`.

Configuration lives in `.env` (see `.env.example`). Nothing is required for the demo: with no API keys the app uses labelled simulated/template fallbacks.

### Tests

```bash
python manage.py test apps          # engine unit tests, component-state tests, end-to-end happy path, security checks
python scripts/contrast.py          # WCAG contrast check of both colour themes
```

## What is in it

| Area | Where |
|---|---|
| Farms, fields, crop library (FAO-56 style Kc, 11 crops, extensible), calculated growth stage, yield history | `apps/farms` |
| **Recommendation engine** (pure Python, no framework) and its unit tests | `apps/engine/core.py`, `apps/engine/tests.py` |
| Plain-language reasons, what-if, English / Pidgin | `apps/engine/explain.py` |
| Weather (Open-Meteo), satellite `SatelliteProvider`, `LLMProvider` | `apps/providers` |
| Accept / override / snooze, immutable decision log | `apps/decisions` |
| Ask-a-question assistant (streaming, grounded) | `apps/assistant` |
| In-app alerts, SMS/WhatsApp adapters (demo log), quiet hours, morning digest | `apps/notifications` |
| Plans in Naira, trial to paid, mock Paystack adapter (test mode only) | `apps/billing` |
| Pilot codes, onboarding checklist, partner dashboard, system health | `apps/partners` |
| Demo mode: seed, live scenario switch, simulated sensor, judge walkthrough | `apps/demo` |
| Design tokens, component library, `/design` gallery, PWA | `static/src`, `templates/components`, `templates/design` |

## Architecture

```
                 ┌────────────────────────── browser / installed PWA ──────────────────────────┐
                 │  Django templates + Tailwind (CSS-variable tokens)  ·  Alpine.js  ·  Motion │
                 │  service worker: offline shell + last viewed advice                         │
                 └───────────────┬─────────────────────────────────────────────┬───────────────┘
                                 │ HTML pages                                  │ JSON / streaming
                       ┌─────────▼──────────┐                         ┌────────▼─────────┐
                       │ farms / decisions  │  POST /api/decisions/   │ assistant /api/ask│
                       │ insights / billing │  POST /api/readings/    └────────┬─────────┘
                       └─────────┬──────────┘  (Bearer key: sensors)           │ facts only
                                 │ build_input()                               ▼
                       ┌─────────▼──────────┐                         ┌──────────────────┐
                       │  engine.core       │◄── DayWeather, NDVI ────│  LLMProvider     │
                       │  water balance     │                         │  Claude | template│
                       └─────────┬──────────┘                         └──────────────────┘
                                 │ signals, reasons, what-if, confidence
        ┌────────────────────────┼─────────────────────────┐
┌───────▼────────┐     ┌─────────▼─────────┐     ┌─────────▼──────────┐
│ Open-Meteo     │     │ SatelliteProvider │     │ DB: SQLite / Postgres│
│ (cached, stale │     │ Sentinel Hub or   │     │ immutable decisions │
│  flagged)      │     │ simulated (label) │     └─────────────────────┘
└────────────────┘     └───────────────────┘
```

## How the engine decides

Deterministic and explainable. For each field and day (`apps/engine/core.py`):

1. **Water the crop uses:** `ETc = ET0 × Kc`, where Kc comes from the crop's growth stage (calculated from the planting date).
2. **Rain we count:** `forecast probability × expected mm × 0.75` (discounted), for today and tomorrow.
3. **Soil bucket:** depletion = `(field capacity − soil moisture) × root depth`. The crop can use `RAW = p × available water` before stress; `p` is per crop and slightly lower in its most water-sensitive stage.
4. **Decide:**
   - depletion already ≥ RAW and rain does not cover it → **Water now**
   - will reach RAW by tonight → **Water later today**
   - rain covers it, or the soil has enough → **Skip today**
   - waterlogged soil with falling NDVI → **Watch** (more water will not fix it; says so)
   - nothing to go on → **Watch**, low confidence
5. **NDVI** raises urgency when it is falling **and** soil is dry; when it falls with wet soil it flags a non-water cause instead.
6. **Yield history** nudges the trigger 5 points earlier only if the newest season lost >15% to a recorded dry spell (small, and shown as a reason).
7. **Volume:** refill to field capacity, divided by method efficiency (drip 0.9, sprinkler 0.75, manual 0.7, flood 0.6), shown in litres, mm, and watering cans or 200 L drums.
8. **Confidence** drops for missing or old soil readings, missing or stale weather and missing NDVI, and the reasons say so.

Every output carries `signals[]` (value, status, share of the decision), ranked `reasons[]`, and `what_if` (the 24-hour wait). The assistant is only given these computed facts and is told to say when it does not know.

## Data sources

- **Weather:** Open-Meteo (free, no key): daily rain, rain probability, temperatures, ET0, wind, solar radiation. Cached per farm for 90 minutes; flagged stale after 6 hours.
- **Soil moisture:** manual entry, CSV import (`date,moisture`), `POST /api/readings/` with a bearer key (for a future sensor), and a labelled simulated stream in demo mode.
- **Crop stress (NDVI):** Sentinel-2 through Sentinel Hub when `SENTINELHUB_*` is set; otherwise a labelled **simulated** provider. One cached value per field per day.
- **AI explanations and Q&A:** Claude (`ANTHROPIC_API_KEY`); otherwise deterministic grounded templates.

## Limitations (honest)

- The engine is a transparent rule-and-water-balance model, not a trained ML model, and it has not been validated against field trials. Crop coefficients and thresholds are FAO-56 style defaults for tropical crops, not locally calibrated.
- Soil moisture is only as good as the reading. Manual readings are noisy; with none, the engine estimates and says confidence is low.
- NDVI is simulated unless Sentinel Hub credentials are configured, and cloud cover in the rainy season will limit real Sentinel-2 coverage.
- "Water saved" is an estimate against a stated baseline (daily watering at crop need), not a measurement.
- SMS/WhatsApp and payments are adapters with demo/test implementations. No real messages or charges.
- The brand mark is a droplet-and-leaf drawn for this build; swap `templates/components/logo.html` and `static/img/*` for the official artwork.
- Lighthouse was measured on the login page only, against a production-style build (DEBUG off, collectstatic, compressed assets): Performance 97, Accessibility 100, Best Practices 100, SEO 100. The authenticated pages are heavier and have not been audited. Lighthouse 12 no longer scores PWA; the manifest, icons and service worker are in place, but install was not exercised on a real device.

## Roadmap

1. Real soil sensors posting to `/api/readings/`, with calibration per soil type.
2. Drone and higher-resolution imagery for field-level stress maps.
3. Local calibration of Kc and thresholds from pilot overrides and yields.
4. SMS/WhatsApp delivery (Termii or Twilio) and USSD for feature phones.
5. Premium advisory: fertiliser and pest timing, market prices, group buying.

## Design

Dark "Estuary Night" and light "Harmattan Paper" themes from CSS-variable tokens (`static/src/tokens.css`); contrast checked by `scripts/contrast.py` (AA for all pairs, AAA for body text). Action states carry colour **and** icon **and** label. Motion uses springs, is interruptible, animates transform/opacity only, and falls back to quick fades under `prefers-reduced-motion`. Review every component state at `/design`.
