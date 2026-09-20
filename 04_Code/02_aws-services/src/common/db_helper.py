"""
Database helper utility for interacting with Amazon DynamoDB tables.
Provides serialization, querying, and mutation utilities for Medical Vitals and EEG Sessions.
"""

import os
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional
import boto3
from boto3.dynamodb.conditions import Key, Attr

# Table names from environment variables (defined in template.yaml)
VITALS_TABLE_NAME = os.getenv("VITALS_TABLE", "HCMUT_VitalsTable")
SESSIONS_TABLE_NAME = os.getenv("SESSIONS_TABLE", "HCMUT_SessionsTable")
USERS_TABLE_NAME = os.getenv("USERS_TABLE", "HCMUT_UserProfilesTable")

_dynamodb = None


def get_dynamodb_resource():
    """Lazily initialize boto3 DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def get_vitals_table():
    return get_dynamodb_resource().Table(VITALS_TABLE_NAME)


def get_sessions_table():
    return get_dynamodb_resource().Table(SESSIONS_TABLE_NAME)


def get_users_table():
    return get_dynamodb_resource().Table(USERS_TABLE_NAME)


def float_to_decimal(obj: Any) -> Any:
    """Recursively converts float values to Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(v) for v in obj]
    return obj


def decimal_to_float(obj: Any) -> Any:
    """Recursively converts Decimal values back to float/int for JSON response."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(v) for v in obj]
    return obj


def save_vitals_record(user_id: str, timestamp: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a vital signs record for a user in DynamoDB."""
    table = get_vitals_table()
    item = {
        "user_id": user_id,
        "timestamp": timestamp,
        **data
    }
    decimal_item = float_to_decimal(item)
    table.put_item(Item=decimal_item)
    return item


def get_latest_vital(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent vital signs record for a user."""
    table = get_vitals_table()
    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,  # Descending order (latest first)
        Limit=1
    )
    items = response.get("Items", [])
    if items:
        return decimal_to_float(items[0])
    return None


def get_vitals_history(user_id: str, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Query vital signs history for a user within a time range."""
    table = get_vitals_table()
    if start_time and end_time:
        key_cond = Key("user_id").eq(user_id) & Key("timestamp").between(start_time, end_time)
    elif start_time:
        key_cond = Key("user_id").eq(user_id) & Key("timestamp").gte(start_time)
    else:
        key_cond = Key("user_id").eq(user_id)

    response = table.query(
        KeyConditionExpression=key_cond,
        ScanIndexForward=False,  # Newest first
        Limit=limit
    )
    items = response.get("Items", [])
    return [decimal_to_float(item) for item in items]


def save_session(user_id: str, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store or update a sleep / meditation EEG session in DynamoDB."""
    table = get_sessions_table()
    item = {
        "user_id": user_id,
        "session_id": session_id,
        **session_data
    }
    decimal_item = float_to_decimal(item)
    table.put_item(Item=decimal_item)
    return item


def get_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch details of a single session."""
    table = get_sessions_table()
    response = table.get_item(
        Key={
            "user_id": user_id,
            "session_id": session_id
        }
    )
    item = response.get("Item")
    if item:
        return decimal_to_float(item)
    return None


def list_sessions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """List recent sessions for a user."""
    table = get_sessions_table()
    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=limit
    )
    items = response.get("Items", [])
    return [decimal_to_float(item) for item in items]
