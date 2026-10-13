# Backblaze Source Data Profile

## 1. Source

- Dataset: Backblaze Drive Stats
- Initial period: Q1 2016
- Date range: 2016-01-01 to 2016-03-31
- Files inspected: 91 daily CSV files
- Source files are retained locally and excluded from Git tracking.

## 2. Observed Structure

- Each daily file contains drive observations for its date.
- Baseline schema contains 95 columns.
- All 91 daily CSV headers matched in name and order.
- The schema comparison covered Q1 2016 only.

## 3. Initial Grain Hypothesis

One row represents one drive observation on one date.

Candidate natural key:
(date, serial_number)

Validation performed:
- Duplicate key pairs found: 0
- Missing date values: 0
- Missing serial_number values: 0
- Rows whose date differed from the filename: 0

These results apply to the inspected Q1 2016 data.

## 4. Data Profile Results

- Total observations: 5,467,888
- Distinct serial numbers across the quarter: 64,074
- Distinct models: 69
- Distinct nonblank capacity values: 16
- Rows with failure = 1: 336

No missing values were found in:
- date
- serial_number
- model
- capacity_bytes
- failure

## 5. Important Interpretation Notes

- A drive appears on multiple dates, so row count is not unique drive count.
- Model observation counts are not unique-drive counts.
- The count of failure = 1 rows is not, by itself, a valid failure rate.
- Daily row counts vary during the quarter.
- Matching daily headers do not prove that schemas remain stable across historical periods.

## 6. Limitations and Next Investigations

- Compare schemas across different historical periods.
- Validate data types and numeric parsing.
- Investigate failure semantics and metric definitions.
- Determine how to handle missing SMART attributes.
- Define Bronze ingestion and idempotent processing.
- Establish data-quality checks appropriate for the source.

## 7. Historical Schema Drift Investigation

### Reference examined

- Reference file: `Drive_Stats_Schema_2018_Onward.csv`
- Purpose: Investigate how the documented Drive Stats column structure changes across quarters.
- Baseline: The first daily CSV from Q1 2016, containing 95 columns.
- Comparison method: Compare column names between the baseline and documented quarterly schemas.

### Findings

- The reference documents quarterly schemas beginning in Q1 2018.
- The documented schema contains 105 columns in 2018 Q1.
- The schema grows at several later quarterly boundaries.
- Examples of documented additions include SMART attribute columns and, in 2023, infrastructure-related fields such as `pod_id`, `vault_id`, and `datacenter`.
- The generated report is stored at `reports/schema_drift_summary.csv`.

### Limitations

- The reference begins in Q1 2018, so it does not show every change between Q1 2016 and Q1 2018.
- The comparison detects column-name additions and removals; it does not validate data types, values, or business meaning.
- A column first observed in a reference period is not necessarily a column introduced in that period.
- Actual daily CSV headers should be checked before treating the reference as proof of the schema of a downloaded data file.

### Engineering implication

The ingestion design must accommodate schema evolution while preserving raw source data, validating required fields, and tracking which columns are available in each period.
