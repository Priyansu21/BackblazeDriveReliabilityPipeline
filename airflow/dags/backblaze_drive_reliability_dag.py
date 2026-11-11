# Configuration and it's purpose
# dag_id: Unique Airflow workflow identifier
# schedule=None: Manual execution only
# catchup=False: No historical scheduled runs
# DatabricksRunNowOperator: Triggers an existing Databricks Job
# databricks_default: Airflow connection containing Databricks credentials
# job_id: Your existing Databricks Job ID
# wait_for_termination=True: Airflow waits for the Databricks job to finish
# polling_period_seconds=30: Checks job status every 30 seconds

import pendulum

from airflow.sdk import dag
from airflow.providers.databricks.operators.databricks import (
    DatabricksRunNowOperator,
)


@dag(
    dag_id="backblaze_drive_reliability_pipeline",
    description="Orchestrates the Backblaze Drive Reliability Databricks workflow",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["backblaze", "databricks", "data-engineering"],
)
def backblaze_drive_reliability_pipeline():

    run_databricks_job = DatabricksRunNowOperator(
        task_id="trigger_databricks_job",
        databricks_conn_id="databricks_default",
        job_id=376708906540244,
        wait_for_termination=True,
        polling_period_seconds=30,
    )


backblaze_drive_reliability_pipeline()
