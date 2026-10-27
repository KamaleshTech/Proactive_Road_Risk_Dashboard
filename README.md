# Proactive Road Risk Dashboard

An explainable road-safety analytics prototype using the US Accidents (2016–March 2023) dataset. The project is designed to help users explore historical accident patterns and understand indicative risk factors.

> **Important scope note:** the current source repository contains a dataset-audit notebook, not a validated predictive model or operational live-risk feed. This MVP makes that limitation explicit. Its dashboard performs transparent exploratory scoring on historical records; it must not be used for emergency response or real-world safety decisions.

## What is included

- Streamlit dashboard with data-upload support and a small built-in demo dataset
- Dataset validation and safe handling of missing or malformed values
- Historical accident analytics by time, state, severity, and weather
- Transparent, rule-based **historical risk indicator** with a visible explanation (not a trained AI prediction)
- Data quality diagnostics, filters, downloadable filtered records, and charts
- Automated tests for data validation and risk-indicator behavior

## Repository structure

```text
.
├── app.py
├── road_risk/
│   ├── __init__.py
│   └── analytics.py
├── tests/
│   └── test_analytics.py
├── requirements.txt
├── runtime.txt
├── .gitignore
└── docs/
    └── DATA_AUDIT.md
```

## Run locally (Windows PowerShell)

Use Python 3.12 for the documented setup.

```powershell
git clone https://github.com/KamaleshTech/Proactive_Road_Risk_Dashboard.git
cd Proactive_Road_Risk_Dashboard
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

If Python 3.12 isn't installed, install it from python.org or use another supported Python version compatible with the dependencies. If PowerShell blocks environment activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and then `.venv\Scripts\python.exe -m streamlit run app.py`.

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Dataset

The original audit refers to `US_Accidents_March23.csv` (7,728,394 rows and 46 columns). The raw dataset is not included in this repository and should not be committed to Git because of its size and licensing/source considerations. Download it from the dataset provider and upload it in the app, or use the built-in sample data for a lightweight demo.

The dashboard accepts CSVs containing fields from the US Accidents dataset, including `Start_Time`, `Start_Lat`, `Start_Lng`, `State`, `Severity`, `Weather_Condition`, and road-context flags. Missing optional fields are handled with documented fallbacks. The full CSV may be too large for a free cloud instance; make a smaller representative sample for demo use.

## Deploy to Streamlit Community Cloud

1. Push this branch to GitHub and open a pull request to `main` after reviewing the code and tests.
2. Once merged, go to [Streamlit Community Cloud](https://share.streamlit.io/) and connect the GitHub repository.
3. Select the repository's default branch (`kanish/data-audit`), app file `app.py`, then deploy.
4. Use the built-in sample for the first live smoke test; upload a small CSV only after the dashboard loads.
5. Check the app's deployment logs and test filters, charts, download, and data-quality warnings.

Do not claim deployment is complete until a public URL has been opened and smoke-tested.

## How the indicator works

This prototype calculates a transparent heuristic from available weather and road-context fields. The score is an exploratory prioritization aid on historical accident records, **not** a calibrated probability that a crash will occur. It does not establish causality and does not predict risk for accident-free road/time windows. Its formula and limitations are shown in the app.

## Next steps before research claims

- Define a road-segment/time observation unit and sample non-crash/background observations.
- Choose an operationally meaningful prediction horizon and target.
- Remove leakage from fields only known after an accident (for example, event severity/end time or event description).
- Split data by time and/or geography; evaluate calibration, recall/precision and subgroup performance.
- Compare a baseline model against a trained model and document uncertainty.
- If claiming current risk, integrate and validate time-stamped live weather/traffic inputs.

## License and data source

Confirm the source dataset's current terms and attribution requirements before redistributing data or publishing a derived public dataset.
