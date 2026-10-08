# Comprehensive Data Audit Report: US Accidents (2016–2023)
**Project**: RoadSafe AI — Proactive Road Risk Intelligence Platform  
**Author**: Data Engineering Team  
**Audit Date**: October 2026  
**Audited File**: `US_Accidents_March23.csv` (Size: 3.06 GB / 2.85 GiB)

---

## 1. Dataset Overview
The US Accidents dataset is a countrywide traffic incident dataset covering the contiguous United States from February 2016 through March 2023. The data is gathered from multiple real-time traffic APIs (principally MapQuest and Bing Traffic, streaming data from transportation departments, law enforcement agencies, traffic cameras, and airborne traffic monitoring sensors).

Each raw record in the dataset represents a **reported traffic event / accident incident**. The dataset does **not** represent a continuous sensor stream of road network conditions; rather, it is an opportunistic collection of verified incident notifications.

---

## 2. Dataset Dimensions
- **Total Records (Rows)**: `7,728,394`
- **Total Attributes (Columns)**: `46`
- **File Size on Disk**: `3,058,183,727 bytes` (~3.06 GB uncompressed)
- **Memory Footprint**: ~2.8 GiB in streaming text, ~4.2 GiB when loaded into default pandas DataFrames.

---

## 3. Column / Data Dictionary

Below is the verified schema audit of all 46 columns, detailing what each column represents, whether it is known prior to prediction time $T$, whether it can be used for ML, and the technical justification:

| # | Column Name | Raw Dtype | Verified Missing (%) | Available Before Event Time $T$? | Usable as ML Prediction Feature? | Rationale & Governance Decision |
|---|---|---|---|---|---|---|
| 1 | `ID` | `object` | 0.00% | No | **NO** | Identifier string (`A-1`, `A-2`...); arbitrary record key, non-generalizable. |
| 2 | `Source` | `object` | 0.00% | No | **NO** | API reporting feed provider (Source1, Source2, Source3). Reflects reporting pipeline artifact, not road risk. |
| 3 | `Severity` | `int64` | 0.00% | No | **NO (as feature)** | Post-event traffic delay rating (1 to 4). Assigned *after* accident occurs based on queue delay. |
| 4 | `Start_Time` | `object` | 0.00% | Yes (as timestamp) | **YES (for featurization)** | Start timestamp of the incident. Used to extract pre-event hour, day of week, month, season. |
| 5 | `End_Time` | `object` | 0.00% | No | **NO (CRITICAL LEAKAGE)** | Timestamp when incident clearance ended. Known only *after* emergency response clears the road. |
| 6 | `Start_Lat` | `float64` | 0.00% | Yes | **YES** | Latitude of incident starting location; used for spatial corridor indexing. |
| 7 | `Start_Lng` | `float64` | 0.00% | Yes | **YES** | Longitude of incident starting location; used for spatial corridor indexing. |
| 8 | `End_Lat` | `float64` | 44.03% | No | **NO (LEAKAGE)** | Latitude of traffic queue termination. Measured during/after incident. 44% missing. |
| 9 | `End_Lng` | `float64` | 44.03% | No | **NO (LEAKAGE)** | Longitude of traffic queue termination. Measured during/after incident. 44% missing. |
| 10 | `Distance(mi)` | `float64` | 0.00% | No | **NO (CRITICAL LEAKAGE)** | Length of road extent impacted by accident. Only measurable *after* collision occurs. |
| 11 | `Description` | `object` | <0.01% | No | **NO (CRITICAL LEAKAGE)** | Natural language incident description (e.g., "Accident on I-95 North, lanes blocked"). Post-event summary. |
| 12 | `Street` | `object` | 0.14% | Yes | **YES (Categorical/Corridor)** | Road/street name. Static identifier. |
| 13 | `City` | `object` | <0.01% | Yes | **YES (Context)** | Municipality name. Static administrative context. |
| 14 | `County` | `object` | 0.00% | Yes | **YES (Context)** | County name. Static administrative context. |
| 15 | `State` | `object` | 0.00% | Yes | **YES (Spatial Stratification)** | US State code. Essential for spatial robustness splits. |
| 16 | `Zipcode` | `object` | 0.02% | Yes | **NO (High Cardinality)** | Postal code. Over 100k distinct values; prone to overfitting. |
| 17 | `Country` | `object` | 0.00% | Yes | **NO (Zero Variance)** | Constant (`US`) across 100% of rows. Zero predictive information. |
| 18 | `Timezone` | `object` | 0.10% | Yes | **YES (Normalization)** | Timezone indicator (US/Eastern, US/Central, etc.). Needed to align UTC/local timestamps. |
| 19 | `Airport_Code` | `object` | 0.29% | Yes | **NO** | Weather reporting station ID. Surrogate station key. |
| 20 | `Weather_Timestamp` | `object` | 1.56% | Conditional | **NO** | Time of weather station observation. Station readings vary; must use readings prior to $T$. |
| 21 | `Temperature(F)` | `float64` | 2.12% | Yes (via forecast/reading) | **YES** | Ambient temperature in Fahrenheit. |
| 22 | `Wind_Chill(F)` | `float64` | 25.87% | Yes | **NO (High Missingness/Collinear)** | Perceived wind chill. 25.87% missing; heavily collinear with Temperature. |
| 23 | `Humidity(%)` | `float64` | 2.25% | Yes | **YES** | Relative humidity percentage. |
| 24 | `Pressure(in)` | `float64` | 1.82% | Yes | **YES** | Atmospheric pressure in inches of mercury. |
| 25 | `Visibility(mi)` | `float64` | 2.29% | Yes | **YES** | Visual distance in miles. Crucial for fog/storm road hazards. |
| 26 | `Wind_Direction` | `object` | 2.27% | Yes | **NO (Low Signal)** | Wind cardinal heading. Weak correlation with road safety risk. |
| 27 | `Wind_Speed(mph)` | `float64` | 7.39% | Yes | **YES** | Sustained wind speed. Relevant for high-profile vehicles and highway blowover risks. |
| 28 | `Precipitation(in)` | `float64` | 28.51% | Yes | **YES (Indicator Engineered)** | Measured rain/snow accumulation. High missing rate (28.5%) requires missingness indicators. |
| 29 | `Weather_Condition` | `object` | 2.24% | Yes | **YES** | Categorical atmospheric condition (Fair, Rain, Fog, Snow, etc.). |
| 30 | `Amenity` | `bool` | 0.00% | Yes | **YES** | Roadside amenity indicator (building, plaza). Static road context. |
| 31 | `Bump` | `bool` | 0.00% | Yes | **YES** | Speed bump presence. Static road context. |
| 32 | `Crossing` | `bool` | 0.00% | Yes | **YES** | Pedestrian crossing presence. Static road context. |
| 33 | `Give_Way` | `bool` | 0.00% | Yes | **YES** | Yield / Give way signage. Static road context. |
| 34 | `Junction` | `bool` | 0.00% | Yes | **YES** | Highway interchange / intersection presence. Key road context feature. |
| 35 | `No_Exit` | `bool` | 0.00% | Yes | **YES** | Dead end / no outlet road presence. Static road context. |
| 36 | `Railway` | `bool` | 0.00% | Yes | **YES** | Railroad crossing presence. Static road context. |
| 37 | `Roundabout` | `bool` | 0.00% | Yes | **YES** | Traffic circle / roundabout presence. Static road context. |
| 38 | `Station` | `bool` | 0.00% | Yes | **YES** | Transit / bus station presence. Static road context. |
| 39 | `Stop` | `bool` | 0.00% | Yes | **YES** | Stop sign presence. Static road context. |
| 40 | `Traffic_Calming` | `bool` | 0.00% | Yes | **YES** | Engineered speed reduction features. Static road context. |
| 41 | `Traffic_Signal` | `bool` | 0.00% | Yes | **YES** | Stop light presence. Static road context. |
| 42 | `Turning_Loop` | `bool` | 0.00% | Yes | **NO (Zero Variance)** | 0 true entries across all 7,728,394 rows. Constant false. |
| 43 | `Sunrise_Sunset` | `object` | 0.30% | Yes | **YES** | Solar day/night period. Useful proxy for ambient lighting. |
| 44 | `Civil_Twilight` | `object` | 0.30% | Yes | **NO (Collinear)** | Astronomical sun angle. Redundant with Sunrise_Sunset. |
| 45 | `Nautical_Twilight`| `object` | 0.30% | Yes | **NO (Collinear)** | Astronomical twilight angle. Redundant. |
| 46 | `Astronomical_Twilight` | `object`| 0.30% | Yes | **NO (Collinear)** | Astronomical twilight angle. Redundant. |

---

## 4. Missing Values Audit
Out of 46 attributes, missingness patterns fall into three distinct tiers:

### Tier 1: Severe Missingness (>25%)
1. **`End_Lat` / `End_Lng` (44.03% missing — 3,402,762 rows)**: Not recorded in older API schemas where point locations rather than road segment vectors were submitted.
2. **`Precipitation(in)` (28.51% missing — 2,203,586 rows)**: Weather stations frequently do not report precipitation during non-rain intervals rather than logging explicit `0.00`. An imputation rule must explicitly create a boolean `is_rain_snow` and impute NaN as 0.0.
3. **`Wind_Chill(F)` (25.87% missing — 1,999,019 rows)**: Only computed by weather stations when temperatures fall below 50°F and wind exceeds 3 mph.

### Tier 2: Moderate Atmospheric Missingness (1% – 10%)
- `Wind_Speed(mph)`: 7.39% (571,233 rows)
- `Visibility(mi)`: 2.29% (177,098 rows)
- `Wind_Direction`: 2.27% (175,206 rows)
- `Humidity(%)`: 2.25% (174,144 rows)
- `Weather_Condition`: 2.24% (173,459 rows)
- `Temperature(F)`: 2.12% (163,853 rows)
- `Pressure(in)`: 1.82% (140,679 rows)
- `Weather_Timestamp`: 1.56% (120,228 rows)

### Tier 3: Zero or Negligible Missingness (<1%)
- `ID`, `Severity`, `Start_Time`, `End_Time`, `Start_Lat`, `Start_Lng`, `Distance(mi)`, `County`, `State`, `Country`, and all 13 road infrastructure flags have **0.00% missing values** across all 7.728 million rows.

---

## 5. Duplicate Analysis
- Total Rows: `7,728,394`
- Unique `ID` Values: `7,728,394` (100% unique primary keys)
- Duplicate Check on Spatiotemporal Tuples `(Start_Time, Start_Lat, Start_Lng)`:
  - Several thousand accident records share identical timestamps and coordinates where multi-vehicle pileups generated distinct incident IDs, or overlapping agency feeds (MapQuest vs Bing) logged the same crash.
  - **Deduplication Recommendation**: For corridor risk models, deduplicate records falling within $\pm 15$ minutes and $<50$ meters to avoid counting a single multi-vehicle pileup as multiple independent events.

---

## 6. Temporal Coverage
- **Earliest Recorded Incident**: `2016-01-14 20:18:33`
- **Latest Recorded Incident**: `2023-03-31 23:30:00`
- **Total Duration**: 7 years, 2 months, 17 days (2,633 calendar days)
- **Yearly Trend & Shift**:
  - 2016–2019: Steady reporting density (~300k–500k crashes/year).
  - 2020–2022: Marked increase in reporting density (>1.2M crashes/year), reflecting expanded sensor coverage and ingestion changes by the data authors rather than a 300% real-world crash spike.
  - **Methodology Impact**: Validates why a **chronological split** is mandatory. Random splitting would introduce severe temporal leakage across pipeline versions.

---

## 7. Spatial Coverage
- **Latitude Span**: `24.5548° N` to `49.0022° N` (Key West, FL to US-Canada border)
- **Longitude Span**: `-124.6238° W` to `-67.1132° W` (Pacific to Atlantic coast)
- **Geographic Entities**: 49 entities (48 contiguous states + District of Columbia). Alaska and Hawaii are not present.
- **Top 5 State Concentrations**:
  1. California (`CA`): 1,741,433 crashes (22.53%)
  2. Florida (`FL`): 880,192 crashes (11.39%)
  3. Texas (`TX`): 582,837 crashes (7.54%)
  4. South Carolina (`SC`): 382,557 crashes (4.95%)
  5. New York (`NY`): 347,960 crashes (4.50%)
- **Spatial Clustering Finding**: Over 41% of all records originate from just three states (CA, FL, TX). A model trained without geographic awareness risks learning state-specific reporting artifacts rather than generalizable road safety principles.

---

## 8. Data Leakage Audit

> [!CAUTION]
> **Strict Leakage Enforcement Policy**: Any feature that is only known because an accident has already happened must be classified as **DO NOT USE** for risk prediction.

### Excluded Leakage Columns and Technical Rationale:

1. **`End_Time`**:
   - *Nature*: Timestamp when traffic queues dissipated and emergency crews cleared the road.
   - *Verdict*: **CRITICAL POST-EVENT LEAKAGE**. Completely unavailable before the crash occurs.
2. **`End_Lat` & `End_Lng`**:
   - *Nature*: Coordinates of the tail of the accident-induced queue.
   - *Verdict*: **CRITICAL POST-EVENT LEAKAGE**. Generated solely by the disruption.
3. **`Distance(mi)`**:
   - *Nature*: The linear length of the road section impacted by the incident.
   - *Verdict*: **CRITICAL POST-EVENT LEAKAGE**. Measurable only after traffic backs up.
4. **`Description`**:
   - *Nature*: Natural language reports written by DOT dispatchers and police (e.g., *"Right lane blocked due to three-car crash on I-95 South"*).
   - *Verdict*: **TOTAL LEAKAGE**. Directly states that a crash occurred and describes vehicle damages.
5. **`Severity` (as an input feature)**:
   - *Nature*: A 1–4 index assigned by Bing/MapQuest reflecting the **severity of traffic delay caused by the crash** (Severity 2 = moderate delay, Severity 4 = full closure / severe incident).
   - *Verdict*: **LEAKAGE IF USED AS A FEATURE**. Cannot be used to predict whether a crash occurs, because it is an outcome rating. (It can only be used as a *prediction target* in conditional severity modeling).
6. **`Weather_Timestamp`**:
   - *Nature*: The timestamp when an ASOS airport weather station reported readings.
   - *Verdict*: **EXCLUDED**. If the weather timestamp is later than $T$, it uses future weather. Weather readings must be strictly aligned to forecasts or observations available before $T$.

---

## 9. Available Prediction-Time Features
The following features are scientifically verified to be available *before* an event timestamp $T$:

### Temporal Features (Derived from $T$):
- `hour` (0–23)
- `day_of_week` (0=Monday, 6=Sunday)
- `month` (1–12)
- `is_weekend` (Binary 0/1)
- `season` (Winter, Spring, Summer, Fall)
- `hour_sin`, `hour_cos` (Cyclical time representations)

### Static Road Infrastructure Context (OSM Boolean Flags):
- `Junction` (High-conflict highway interchange)
- `Traffic_Signal` (Signalized intersection)
- `Crossing` (Pedestrian crossing)
- `Stop` (Stop sign)
- `Station` (Bus/rail passenger station)
- `Railway` (Level crossing)
- `Amenity`, `Bump`, `Give_Way`, `No_Exit`, `Roundabout`, `Traffic_Calming`
- `road_infrastructure_count` (Composite infrastructure complexity score)

### Pre-Event Environmental & Atmospheric Features:
- `Temperature(F)` & `is_freezing` ($\le 32^\circ\text{F}$)
- `Humidity(%)`
- `Pressure(in)`
- `Visibility(mi)` & `is_low_visibility` ($\le 2\text{ miles}$)
- `Wind_Speed(mph)`
- `Precipitation(in)` & `is_rain_snow` ($> 0.01\text{ in}$)
- `Weather_Condition` (Grouped categorical: Clear, Rain, Snow, Fog, Cloudy)
- `Sunrise_Sunset` (Day vs Night ambient lighting)

### Spatial Coordinates:
- `Start_Lat`, `Start_Lng`
- `grid_cell` (0.05° spatial resolution corridor tile)
- `State`

---

## 10. Traffic / Exposure Availability Audit
- **Does traffic volume exist in the dataset?**
  **NO.** There is no column for Annual Average Daily Traffic (AADT), vehicle miles traveled (VMT), or live vehicle throughput.
- **Why is this critical?**
  Risk is fundamentally defined as:
  $$\text{Risk} = \frac{\text{Accidents}}{\text{Exposure (Traffic Volume)}} \times \text{Hazard Rate}$$
  Because traffic volume is absent, urban highways like I-5 in Los Angeles record thousands of crashes simply because millions of cars travel on them daily. Rural mountain roads may have a much higher danger per vehicle, but register fewer total raw crashes.
- **Rule Enforcement**:
  We must **never fabricate traffic volume** or claim that our model outputs "true accident probability per vehicle mile". We can only estimate **corridor-level elevated risk presence**.

---

## 11. Weather Availability Audit
- **Does continuous weather exist for non-crash periods?**
  **NO.** Weather records in this CSV are strictly attached to accident events.
- **Are there weather observations for safe, sunny hours when no crash occurred?**
  **NO.** The dataset only records what the weather was *when a crash happened*.
- **Consequence**:
  If an analyst naively trains on this dataset without understanding this constraint, the model will see that 80% of accidents happened in "Clear / Fair" weather and falsely conclude that fair weather is dangerous. In reality, clear weather represents the vast majority of baseline days.

---

## 12. Target Feasibility Investigation
Can we predict: *"Given road/location + time + contextual conditions available at time T, estimate whether a recorded crash occurs within a defined future window?"*

### Two Defensible Options:

| Formulation | Unit of Observation | Target $Y$ Definition | Negative Class Strategy | Scientific Defensibility |
|---|---|---|---|---|
| **Option 1: Corridor Shift Risk Window** | Monitored Road Corridor Cell $i$ during a 4-hour Operational Window $t$ | $Y=1$ if $\ge 1$ accident occurred in cell $i$ during shift $t$; $Y=0$ if 0 accidents occurred. | Restricted strictly to **active monitored corridors** during monitored periods. | **FEASIBLE with documented corridor bounds**. Avoids nationwide negative fabrication. |
| **Option 2: Conditional Severe Impact Risk** | Individual verified road hazard / incident event | $Y=1$ if $\text{Severity} \ge 3$ (High / Critical disruption); $Y=0$ if $\text{Severity} \le 2$. | Every row is a genuine observed event; no synthetic negatives needed. | **HIGHLY DEFENSIBLE**. 100% genuine empirical observations. |

---

## 13. The Negative-Sampling Problem

### The Fundamental Dilemma:
The raw dataset contains $7,728,394$ positive event records ($Y=1$). There are **zero** explicitly labeled negative ($Y=0$) records.

### Three Unscientific Pitfalls (Strictly Prohibited):
1. **Nationwide Random Negative Sampling**: Assuming that if no crash was reported in rural Wyoming at 3:00 AM, that location is "safe". That is unmonitored road, not confirmed safe road.
2. **"Sunny Weather = Safe" Fallacy**: Generating synthetic non-crash rows by picking random sunny weather timestamps. This introduces severe selection bias.
3. **Implicit Negative Assumption**: Labeling any missing cell as a negative example without accounting for reporting agency coverage.

### Scientific Solution to Propose to Team:
Restrict the negative sampling universe to **Monitored Road Corridors**:
- Identify spatial cells with sustained historical reporting (e.g., top 1,000 highway segments with $\ge 20$ historical reports).
- Construct time windows (e.g., 4-hour shifts) across those specific monitored corridors.
- If an active monitored corridor has no reported incident in a given 4-hour shift, that cell-window can be defensibly treated as a non-event window ($Y=0$).

---

## 14. Major Dataset Limitations

1. **Incident-Only Reporting (Presence-Only Data)**: Lacks true non-incident denominator data.
2. **Zero Traffic Volume / Exposure**: Cannot normalize for vehicle density or AADT.
3. **Discontinuous Weather Observations**: Weather readings exist only as point-in-time attachments to accidents.
4. **Extreme Sensor Outliers**:
   - `Wind_Speed(mph)`: Max of 1,087 mph (sensor malfunction).
   - `Temperature(F)`: Min of -89°F, Max of 207°F.
   - `Pressure(in)`: Min of 0.00 inches.
5. **Zero-Variance Columns**: `Turning_Loop` has 0 true entries (100% false across 7.7M rows). `Country` is 100% 'US'.
6. **Reporting Bias**: Over 41% of data comes from CA, FL, and TX alone. Incident detection depends heavily on local agency API feeds rather than uniform physical monitoring.

---

## 15. Recommended Next Step for Member 2
Before Member 2 starts feature engineering:
1. **Agree on Prediction Task**: Review whether the team selects **Option 1 (Monitored Corridor Shift Risk)** or **Option 2 (Conditional Severe Impact Risk)**.
2. **Filter Outliers**: Implement domain-boundary clipping for weather values (e.g., $-40^\circ\text{F} \le \text{Temp} \le 130^\circ\text{F}$, $0 \le \text{Wind Speed} \le 120\text{ mph}$).
3. **Drop Zero-Variance & Leakage Columns**: Drop `Turning_Loop`, `Country`, `ID`, `Description`, `End_Time`, `End_Lat`, `End_Lng`, `Distance(mi)`.
4. **Construct Chronological Splits**:
   - Train: 2016–01-01 to 2021–12-31 (~5 years)
   - Validation: 2022–01-01 to 2022–09-30 (9 months)
   - Test: 2022–10-01 to 2023–03-31 (6 months)

---

## 16. Final Go / No-Go Assessment

### Assessment: **CONDITIONAL GO**

- **Why GO**: The dataset contains 7.728 million rich, empirical records spanning 7+ years with high-precision timestamps, coordinates, road infrastructure indicators, and environmental attributes. It is fully capable of powering a high-impact, award-winning hackathon prototype for **elevated road risk identification and explainable prioritization**.
- **Conditions**:
  1. We must **never claim exact accident prediction**.
  2. We must **never claim causality from SHAP**.
  3. We must strictly exclude the 5 post-event leakage columns (`End_Time`, `End_Lat`, `End_Lng`, `Distance(mi)`, `Description`).
  4. We must clearly disclose that traffic volume / exposure is not present, framing risk as **corridor elevated risk conditions**.
