"""Create one-time reminder schedules in EventBridge Scheduler."""
import json
import os
from datetime import timedelta

import boto3
from dateutil import parser as dtparser
from strands import tool

TARGET_ARN = os.environ.get("REMINDER_TARGET_ARN", "")
ROLE_ARN = os.environ.get("REMINDER_ROLE_ARN", "")
GROUP_NAME = os.environ.get("REMINDER_GROUP", "default")


@tool
def schedule_reminders(evento_id: str, inicio_iso: str) -> dict:
    """Create schedules 24h and 4h before the appointment."""
    client = boto3.client("scheduler")
    start = dtparser.isoparse(inicio_iso)
    results = {}
    for hours in (24, 4):
        run = start - timedelta(hours=hours)
        name = f"{evento_id}-{hours}h"
        resp = client.create_schedule(
            Name=name,
            GroupName=GROUP_NAME,
            ScheduleExpression=f"at({run.strftime('%Y-%m-%dT%H:%M:%S')})",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": TARGET_ARN,
                "RoleArn": ROLE_ARN,
                "Input": json.dumps({"event_id": evento_id, "offset_hours": hours}),
            },
        )
        results[name] = resp
    return results
