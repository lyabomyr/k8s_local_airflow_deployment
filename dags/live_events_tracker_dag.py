from __future__ import annotations
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from custom_operators.fail_slack_alert_operator import task_fail_slack_alert

default_args = {
    "owner": "test",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_fail_slack_alert,
}


@dag(
    schedule_interval="*/5 * * * *",
    default_args=default_args,
    start_date=datetime(2023, 10, 14),
    catchup=False,
    tags=["slack_alerts"],
    description="DAG for sending slack alert for live BBL markets",
)
def LiveEventTracker():
    @task
    def live_event_trigger() -> None:
        print(f"sent message")

    # Call the task to ensure it's part of the DAG
    live_event_trigger()


# Assign the DAG to a variable
LiveEventTracker_dag = LiveEventTracker()
