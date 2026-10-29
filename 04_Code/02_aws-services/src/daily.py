"""Folds one day's Sessions and SpotMeasurements into a DailyVitals item (daily_vitals_schema.json).
A day is Vietnam time (UTC+7). Fields with no data that day are left out, never faked.
The nightly schedule does yesterday; invoke with {"date": "YYYY-MM-DD"} to (re)compute a given day.
GET /vitals/daily?date=YYYY-MM-DD reads one day, without date the latest one."""

import json
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import boto3
import jsonschema
from boto3.dynamodb.conditions import Key

from api import respond

dynamodb = boto3.resource("dynamodb")
sessions = dynamodb.Table(os.environ["SESSIONS_TABLE"])
spots = dynamodb.Table(os.environ["SPOT_TABLE"])
daily = dynamodb.Table(os.environ["DAILY_TABLE"])
SCHEMA = json.loads((Path(__file__).parent / "daily_vitals_schema.json").read_text())
USER_ID = "demo"  # shortcut: single user until Cognito is added
VN = timezone(timedelta(hours=7))


def day_range(day):
    """UTC ISO bounds of a Vietnam day, inclusive, in the same format the Pi writes (seconds, +00:00)."""
    start = datetime.combine(day, time(), VN).astimezone(timezone.utc)
    return start.isoformat(), (start + timedelta(days=1, seconds=-1)).isoformat()


def query_day(table, sort_key, day):
    kwargs = {"KeyConditionExpression": Key("user_id").eq(USER_ID) & Key(sort_key).between(*day_range(day))}
    items = []
    while True:
        resp = table.query(**kwargs)
        items += resp["Items"]
        if "LastEvaluatedKey" not in resp:
            return items
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def summarize(day, day_sessions, day_spots, computed_at):
    """Returns the DailyVitals record, or None when nothing was measured that day."""
    heart = [(s["metadata"]["timestamp_start"], s["summary_insights"]["average_vitals"]) for s in day_sessions]
    heart = [(ts, v) for ts, v in heart if v.get("heart_rate_bpm")]  # sessions without HR (HR = 0) say nothing
    oxygen = [m for m in day_spots if m.get("type") == "spo2"]
    if not heart and not oxygen:
        return None

    summary = {}
    h303 = [v["heart_rate_bpm"] for _, v in heart if v["heart_rate_source"] == "magene_h303"]
    if h303:
        # shortcut: lowest H303 session average stands in for resting HR until morning resting readings exist
        summary["resting_heart_rate_bpm"] = int(round(min(h303)))
    if oxygen:
        summary["average_blood_oxygen_pct"] = round(sum(m["spo2_pct"] for m in oxygen) / len(oxygen), 1)

    record = {"metadata": {"user_id": USER_ID, "date": day.isoformat(), "computed_at": computed_at},
              "daily_summary": summary}
    if heart:
        record["heart_rate_log"] = [{"timestamp": ts, "bpm": int(round(v["heart_rate_bpm"])),
                                     "source_device": v["heart_rate_source"]} for ts, v in heart]
    if oxygen:
        last_per_minute = {m["timestamp"][:16]: m for m in sorted(oxygen, key=lambda m: m["timestamp"])}
        record["blood_oxygen_log"] = [{"timestamp": m["timestamp"], "spo2_pct": m["spo2_pct"],
                                       "pulse_bpm": int(m["pulse_bpm"]), "source_device": m["source_device"]}
                                      for m in last_per_minute.values()]
    jsonschema.validate(record, SCHEMA)
    return record


def handler(event, context):
    if "httpMethod" in event:
        day = (event.get("queryStringParameters") or {}).get("date")
        if day:
            item = daily.get_item(Key={"user_id": USER_ID, "date": day}).get("Item")
        else:
            item = next(iter(daily.query(KeyConditionExpression=Key("user_id").eq(USER_ID),
                                         ScanIndexForward=False, Limit=1)["Items"]), None)
        return respond(200, item) if item else respond(404, {"error": "no daily vitals"})

    day = date.fromisoformat(event["date"]) if event.get("date") else datetime.now(VN).date() - timedelta(days=1)
    record = summarize(day, query_day(sessions, "timestamp_start", day), query_day(spots, "timestamp", day),
                       datetime.now(timezone.utc).isoformat(timespec="seconds"))
    if record:
        daily.put_item(Item={"user_id": USER_ID, "date": day.isoformat(), **record})
    return {"date": day.isoformat(), "saved": record is not None}
