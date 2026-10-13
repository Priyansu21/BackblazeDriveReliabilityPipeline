# Backblaze Drive Reliability Pipeline

## Project Overview

A Data Engineering portfolio project using Backblaze Drive Stats data to investigate drive reliability and build a pipeline that handles historical data, schema evolution, and incremental processing.

## Current Progress

- Downloaded and profiled the Q1 2016 dataset.
- Inspected 91 daily CSV files.
- Validated the candidate natural key `(date, serial_number)` within daily files.
- Investigated historical schema evolution using Backblaze's published schema reference.
- Generated schema-drift and schema-registry reports.

## Planned Engineering Work

1. Verify documented schema changes against actual daily CSV headers.
2. Define the Bronze ingestion contract.
3. Implement incremental ingestion and schema-drift handling in PySpark on Databricks.
4. Add idempotency, data-quality checks, and historical backfill support.
5. Build curated drive reliability metrics.
6. Add workflow orchestration and automated validation.

## Data Source

Backblaze Drive Stats:

https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data

Raw source datasets are stored locally and excluded from Git tracking.

## Technology Stack

- Python
- SQL
- PySpark
- Databricks
- Git and GitHub

Additional technologies will be introduced as the implementation progresses.