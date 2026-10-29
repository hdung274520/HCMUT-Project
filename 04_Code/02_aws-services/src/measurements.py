"""POST /measurements takes a JSON list of spot readings (spot_measurement_schema.json, user_id is set here),
saves the valid ones and lists the rejected ones, so one bad reading never blocks the Pi's queue."""

import json
import os
from decimal import Decimal
from pathlib import Path

import boto3
import jsonschema
from boto3.dynamodb.conditions import Key

from api import respond

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
SCHEMA = json.loads((Path(__file__).parent / "spot_measurement_schema.json").read_text())
USER_ID = "demo"  # shortcut: single user until Cognito is added


def handler(event, context):
    if event["httpMethod"] == "POST":
        try:
            items = json.loads(event["body"] or "", parse_float=Decimal)  # DynamoDB rejects float
        except json.JSONDecodeError as exc:
            return respond(400, {"error": str(exc)})
        if not isinstance(items, list):
            return respond(400, {"error": "body must be a JSON list"})
        saved, rejected = [], []
        # Same timestamp overwrites the same item, so a resend from the Pi never duplicates.
        with table.batch_writer(overwrite_by_pkeys=["user_id", "timestamp"]) as batch:
            for m in items:
                m = {**m, "user_id": USER_ID} if isinstance(m, dict) else m
                try:
                    jsonschema.validate(m, SCHEMA)
                except jsonschema.ValidationError as exc:
                    rejected.append({"measurement_id": m.get("measurement_id") if isinstance(m, dict) else None,
                                     "error": exc.message})
                    continue
                batch.put_item(Item=m)
                saved.append(m["measurement_id"])
        return respond(200, {"saved": saved, "rejected": rejected})

    params = event.get("queryStringParameters") or {}
    resp = table.query(KeyConditionExpression=Key("user_id").eq(USER_ID),
                       ScanIndexForward=False, Limit=int(params.get("limit", 20)))
    return respond(200, resp["Items"])
