import os
import logging
import requests


def task_fail_slack_alert(
    context, slack_webhook_url=os.getenv("SLACK_AIRFLOW_WEB_HOOK")
) -> str:
    slack_msg = {
        "text": ":red_circle: Task Failed.",
        "attachments": [
            {
                "text": f"*Task*: {context.get('task_instance').task_id}"
                f"\n*Dag*: {context.get('task_instance').dag_id}"
                f"\n*Execution Time*: {context.get('execution_date')}"
            }
        ],
    }

    try:
        response = requests.post(slack_webhook_url, json=slack_msg)
        if response.status_code == 200:
            logging.info("Slack alert sent successfully")
        else:
            logging.error(
                f"Failed to send Slack alert. Status code: {response.status_code}"
            )
            return f"Failed to send Slack alert. Status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to Slack failed: {e}")
        return f"Request to Slack failed: {e}"

    return response.text
