"""
AWS Lambda handler for querying vital signs history and latest stats.
Endpoints:
  GET /vitals/latest?user_id={id}
  GET /vitals/history?user_id={id}&hours={hours}&limit={limit}
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db_helper import get_latest_vital, get_vitals_history

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type": "application/json"
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handles GET requests for vitals queries."""
    http_method = event.get("requestContext", {}).get("http", {}).get("method", event.get("httpMethod", ""))
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    raw_path = event.get("rawPath") or event.get("path", "")
    params = event.get("queryStringParameters") or {}

    user_id = params.get("user_id", "usr_default")

    try:
        # Route 1: Query Latest Vitals (/vitals/latest)
        if "latest" in raw_path:
            latest = get_latest_vital(user_id=user_id)
            if not latest:
                return {
                    "statusCode": 404,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"status": "not_found", "message": f"No vitals found for user '{user_id}'"})
                }
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "status": "success",
                    "user_id": user_id,
                    "data": latest
                })
            }

        # Route 2: Query Vitals History (/vitals/history or fallback)
        hours = int(params.get("hours", "24"))
        limit = min(int(params.get("limit", "100")), 500)

        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        records = get_vitals_history(user_id=user_id, start_time=start_time, limit=limit)

        # Calculate summary statistics
        hr_list = [r.get("vitals", {}).get("heart_rate") for r in records if r.get("vitals", {}).get("heart_rate") is not None]
        spo2_list = [r.get("vitals", {}).get("spo2") for r in records if r.get("vitals", {}).get("spo2") is not None]

        summary = {
            "total_records": len(records),
            "time_window_hours": hours,
            "hr_avg": round(sum(hr_list) / len(hr_list), 1) if hr_list else None,
            "hr_min": min(hr_list) if hr_list else None,
            "hr_max": max(hr_list) if hr_list else None,
            "spo2_avg": round(sum(spo2_list) / len(spo2_list), 1) if spo2_list else None,
        }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "status": "success",
                "user_id": user_id,
                "summary": summary,
                "records": records
            })
        }

    except ValueError as ve:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "error": f"Invalid query parameter: {str(ve)}"})
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "error": f"Internal server error: {str(exc)}"})
        }
