# Proactive Road Risk Dashboard

A full-stack road-safety analytics showcase built with **React + Vite + FastAPI + Pandas + NumPy + SQLite**, using Plotly for charts and Leaflet for interactive maps.

> **Scope and safety:** this is a historical analytics prototype. Its transparent, rule-based indicator prioritizes historic accident records for exploration; it is not a trained model, a calibrated probability of a future crash, a live traffic feed, or an operational safety warning.

## Stack

- **Frontend:** React, Vite, custom responsive CSS, Plotly, React Leaflet
- **Backend:** FastAPI, Python, Pandas, NumPy
- **Storage:** SQLite single-active-dataset store
- **Testing:** Pytest and GitHub Actions
- **Deployment:** Render (API) + Vercel (frontend), or run both locally

## Features

- Dark, responsive dashboard UI with summary metrics
- Filter records by region, historic event severity, and explainable indicator band
- Search by city, state, weather label and explanation
- Historical monthly and hourly patterns, region and weather summaries
- Interactive geographic map with selectable record markers
- Incident explorer with pagination and CSV export
- Upload a CSV, validate coordinates and numeric fields, and inspect missing values
- Built-in synthetic demo data so the app starts without a multi-gigabyte source dataset
- Explicit limitation labels: historical heuristic does not represent future-crash probability

## Repository layout

```text
.
├── backend/
│   ├── analytics.py          # normalization and transparent indicator
│   ├── main.py               # FastAPI routes
│   ├── storage.py            # SQLite persistence
│   └── tests/
├── frontend/
│   ├── src/App.jsx
│   ├── src/styles.css
│   ├── package.json
│   └── vite.config.js
├── tests/test_backend_import.py
├── requirements.txt
├── requirements-notebook.txt # optional environment for the original audit notebook
├── render.yaml
└── docs/DATA_AUDIT.md
```

## Run locally (Windows)

Install Python 3.12 and Node.js 20 or newer. Open two PowerShell terminals in the repository.

**Terminal 1 — API**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)  
Interactive API documentation: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

**Terminal 2 — React frontend**

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` requests to the API on port 8000 by default.

**Run automated tests** from the repository root, in the activated Python environment:

```powershell
python -m pytest -q
```

Build-check the frontend:

```powershell
cd frontend
npm run build
```

## CSV input

Use the included synthetic sample for the first demonstration. To analyse source data, upload a CSV that contains latitude and longitude columns, such as `Start_Lat` and `Start_Lng`. The importer recognizes common columns from the US Accidents dataset and several simpler aliases; optional columns can be absent.

The showcase upload limit is **25 MB and 100,000 rows per upload** to keep memory use and response time manageable. For the full `US_Accidents_March23.csv` dataset, create a representative sample first. The raw source dataset is not committed to this repository.

Invalid/missing coordinates are dropped during import. Out-of-range optional weather readings are treated as missing, and the data-quality view shows missing-field counts. The app does not silently pretend that bad values are real measurements.

## Deploy the API to Render

1. Push the branch with this stack to GitHub and select **New → Blueprint** in [Render](https://render.com/).
2. Connect this repository. Render reads `render.yaml` and creates the FastAPI service using `backend.main:app`.
3. After deployment, test the generated service URL at `/api/health` and `/api/docs`.
4. Copy the API service URL; you will set it as `VITE_API_BASE_URL` in Vercel below.

The free Render instance does not guarantee persistence for a local SQLite file through restarts/redeploys. This is okay for a lightweight showcase but not for durable multi-user storage. For persistent live use, configure a persistent volume or switch the DB layer to hosted PostgreSQL.

## Deploy the frontend to Vercel

1. Import this GitHub repository in [Vercel](https://vercel.com/).
2. Set **Root Directory** to `frontend` and use the Vite defaults: build command `npm run build`, output directory `dist`.
3. Add environment variable `VITE_API_BASE_URL` with the full Render API URL, for example `https://your-api-service.onrender.com` (no trailing slash).
4. Deploy and copy the frontend URL.
5. In Render, set `CORS_ORIGINS` to that exact frontend origin (for example `https://your-project.vercel.app`), save the change, and redeploy/restart the API.
6. Open the frontend URL and verify overview metrics, filters, map, import, data quality and CSV export. The first request to a free backend may take a little while if it has been sleeping.

The dashboard is not considered live until the public frontend URL and its backend connection have been manually smoke-tested.

## API routes

- `GET /api/health` — service health
- `GET /api/meta` and `GET /api/options` — active dataset metadata and filter options
- `GET /api/dashboard` — filtered metrics, charts, map points and high-indicator records
- `GET /api/records` — filtered, paginated incident rows
- `GET /api/quality` — missing-value summary
- `GET /api/export.csv` — filtered CSV export
- `POST /api/upload` — validate and replace the active dataset with a CSV
- `POST /api/demo/reset` — restore synthetic showcase data

## Indicator and modelling limitations

The score is a fixed, explainable heuristic based on selected visibility, weather, precipitation, wind, humidity, night-time and road-context fields. It is not trained or calibrated. The historical event `Severity` field is deliberately not used to calculate it.

A defensible future-crash model requires a clear road-segment/time unit, positive crash examples plus suitable non-crash/background observations, a prediction horizon, leakage review, temporal/geographic holdout data, and evaluation/calibration against a baseline. A claim about *current* risk additionally needs trustworthy, timestamped live weather/traffic data.

## Original dataset audit

The original repository's audit of `US_Accidents_March23.csv` remains in `docs/DATA_AUDIT.md` and `notebooks/01_data_audit.ipynb`. See the audit's missing data, extreme values, target definition, and leakage warnings before making research claims.

## Privacy and licensing

Do not upload sensitive personal or restricted operational records to this public demo. The current prototype has no authentication/role-based access. Confirm the source dataset's current terms and attribution requirements before redistributing it or publishing a derived data dump.
