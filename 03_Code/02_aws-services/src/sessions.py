import json
import os
from decimal import Decimal
from pathlib import Path

import boto3
import jsonschema
from boto3.dynamodb.conditions import Key

from api import respond

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
SCHEMA = json.loads((Path(__file__).parent / "active_session_schema.json").read_text())
USER_ID = "demo"  # shortcut: single user until Cognito is added


def handler(event, context):
    if event["httpMethod"] == "POST":
        try:
            session = json.loads(event["body"] or "", parse_float=Decimal)  # DynamoDB rejects float
            jsonschema.validate(session, SCHEMA)
        except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
            return respond(400, {"error": getattr(exc, "message", str(exc))})
        # Same timestamp_start overwrites the same item, so a resend from the Pi never duplicates.
        table.put_item(Item={"user_id": USER_ID, **session,
                             "timestamp_start": session["metadata"]["timestamp_start"]})
        return respond(201, {"session_id": session["metadata"]["session_id"]})

    params = event.get("queryStringParameters") or {}
    resp = table.query(KeyConditionExpression=Key("user_id").eq(USER_ID),
                       ScanIndexForward=False, Limit=int(params.get("limit", 20)))
    return respond(200, resp["Items"])
