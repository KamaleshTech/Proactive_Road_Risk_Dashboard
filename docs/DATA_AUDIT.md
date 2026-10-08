# Roadsafety AI — Dataset Audit

## Dataset

- Dataset: `US_Accidents_March23.csv`
- Rows: 7,728,394
- Columns: 46
- Exact duplicate rows: 0

## Temporal Coverage

### Start Time
- Minimum: `2016-01-14 20:18:33`
- Maximum: `2023-03-31 23:30:00`
- Actual missing values: 0
- Parsing failures: 0

### End Time
- Minimum: `2016-02-08 06:37:08`
- Maximum: `2023-03-31 23:59:00`
- Actual missing values: 0
- Parsing failures: 0

### Weather Timestamp
- Minimum: `2016-01-14 19:51:00`
- Maximum: `2023-03-31 23:53:00`
- Actual missing values: 120,228
- Parsing failures: 0

## Spatial Coverage

### Start Coordinates
- `Start_Lat`: 100% numeric values
- `Start_Lng`: 100% numeric values
- Start latitude range: `24.5548` to `49.002201`
- Start longitude range: `-124.623833` to `-67.113167`

### End Coordinates
- `End_Lat`: 4,325,632 available; 3,402,762 missing
- `End_Lng`: 4,325,632 available; 3,402,762 missing

Therefore, start coordinates are more reliable than end coordinates for the prototype.

## Missing Values

Highest missing-value fields:

| Column | Missing % |
|---|---:|
| End_Lat | 44.03% |
| End_Lng | 44.03% |
| Precipitation(in) | 28.51% |
| Wind_Chill(F) | 25.87% |
| Wind_Speed(mph) | 7.39% |
| Visibility(mi) | 2.29% |
| Wind_Direction | 2.27% |
| Humidity(%) | 2.25% |
| Weather_Condition | 2.24% |
| Temperature(F) | 2.12% |

## Data Quality Flags

Potential extreme values requiring investigation before feature engineering:

- Wind_Speed maximum: 1087.0 mph
- Visibility maximum: 140 mi
- Pressure maximum: 58.63 in
- Temperature maximum: 207°F
- Precipitation maximum: 36.47 in
- Distance maximum: 441.75 mi

These values are flagged for investigation only. No values were removed or modified during the audit.

## Predictive Leakage Review

The following columns require exclusion or further justification before use as prediction inputs:

- `Severity`
- `End_Time`
- `Description`
- `Distance(mi)` — requires investigation regarding availability at prediction time
- Other event-derived fields must be reviewed against the prediction timestamp

## Constant / Near-Constant Fields

`Turning_Loop` contains only `False` values and therefore has no observed variation in this dataset.

Several other road-context indicators are highly imbalanced and should be evaluated before feature selection.

## Target Design Concern

The dataset consists of recorded accident events. It does not directly provide a continuous background population of road-segment/time observations where no accident occurred.

Therefore, a valid positive/negative prediction target cannot be assumed directly from the raw accident rows.

A dedicated target and background-sampling strategy must be designed and documented before model training.

## Audit Conclusion

The dataset provides strong starting location and event-time information and substantial weather and road-context attributes.

However, target construction, temporal leakage prevention, missing weather handling, and extreme-value investigation must be resolved before predictive modeling.

No raw data was modified during this audit.