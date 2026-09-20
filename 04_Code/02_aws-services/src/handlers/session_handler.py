"""
AWS Lambda handler for managing Active Sessions (Sleep, Meditation, EEG Monitoring).
Endpoints:
  POST /sessions
  GET /sessions?user_id={id}
  GET /sessions/{sessionId}?user_id={id}
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db_helper import get_session, list_sessions, save_session

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json"
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handles requests for Session Management."""
    http_method = event.get("requestContext", {}).get("http", {}).get("method", event.get("httpMethod", ""))
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    try:
        if http_method == "POST":
            body = event.get("body", "{}")
            payload = json.loads(body) if isinstance(body, str) else body

            user_id = payload.get("user_id") or payload.get("metadata", {}).get("user_id", "usr_default")
            session_id = payload.get("session_id") or payload.get("metadata", {}).get("session_id")
            if not session_id:
                session_id = f"sess_{int(datetime.now(timezone.utc).timestamp())}"

            session_data = {
                "session_type": payload.get("session_type", "sleep"),
                "timestamp_start": payload.get("timestamp_start", datetime.now(timezone.utc).isoformat()),
                "timestamp_end": payload.get("timestamp_end"),
                "duration_seconds": payload.get("duration_seconds"),
                "metrics": payload.get("metrics", {}),
                "eeg_summary": payload.get("eeg_summary", {}),
                "sleep_stages": payload.get("sleep_stages", {}),
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            save_session(user_id=user_id, session_id=session_id, session_data=session_data)

            return {
                "statusCode": 201,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "status": "success",
                    "message": "Session recorded successfully",
                    "session_id": session_id,
                    "user_id": user_id
                })
            }

        elif http_method == "GET":
            session_id = path_params.get("sessionId")
            user_id = query_params.get("user_id", "usr_default")

            if session_id:
                session = get_session(user_id=user_id, session_id=session_id)
                if not session:
                    return {
                        "statusCode": 404,
                        "headers": CORS_HEADERS,
                        "body": json.dumps({"status": "not_found", "message": f"Session '{session_id}' not found"})
                    }
                return {
                    "statusCode": 200,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"status": "success", "session": session})
                }
            else:
                limit = min(int(query_params.get("limit", "20")), 50)
                sessions = list_sessions(user_id=user_id, limit=limit)
                return {
                    "statusCode": 200,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({
                        "status": "success",
                        "user_id": user_id,
                        "count": len(sessions),
                        "sessions": sessions
                    })
                }

        return {
            "statusCode": 405,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "message": f"Method {http_method} not allowed"})
        }

    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "error": f"Internal server error: {str(exc)}"})
        }
