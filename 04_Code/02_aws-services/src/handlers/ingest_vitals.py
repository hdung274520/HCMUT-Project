"""
AWS Lambda handler for ingesting physiological vital signs.
Endpoint: POST /vitals
Sources: Raspberry Pi 4 (Muse 2 PPG/EEG) or Android Mobile App (Galaxy Fit 3 via Google Health Connect).
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

# Add parent directory to sys.path to resolve common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db_helper import save_vitals_record

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json"
}


def evaluate_vital_anomalies(vitals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates vital measurements against standard physiological thresholds.
    Returns list of detected health anomalies.
    """
    anomalies = []
    hr = vitals.get("heart_rate")
    hrv = vitals.get("hrv")
    spo2 = vitals.get("spo2")
    bp = vitals.get("blood_pressure", {})
    systolic = bp.get("systolic") if isinstance(bp, dict) else None
    diastolic = bp.get("diastolic") if isinstance(bp, dict) else None

    # Heart Rate checks
    if hr is not None:
        if hr > 120:
            anomalies.append({
                "type": "TACHYCARDIA",
                "severity": "WARNING",
                "message": f"Elevated resting heart rate detected: {hr} bpm (threshold: >120 bpm)"
            })
        elif hr < 45:
            anomalies.append({
                "type": "BRADYCARDIA",
                "severity": "WARNING",
                "message": f"Abnormally low resting heart rate detected: {hr} bpm (threshold: <45 bpm)"
            })

    # SpO2 checks
    if spo2 is not None:
        if spo2 < 90:
            anomalies.append({
                "type": "CRITICAL_HYPOXIA",
                "severity": "CRITICAL",
                "message": f"Critical blood oxygen drop detected: {spo2}% (threshold: <90%)"
            })
        elif spo2 < 95:
            anomalies.append({
                "type": "MILD_HYPOXIA",
                "severity": "WARNING",
                "message": f"Low blood oxygen saturation: {spo2}% (threshold: <95%)"
            })

    # Blood Pressure checks
    if systolic is not None and diastolic is not None:
        if systolic >= 140 or diastolic >= 90:
            anomalies.append({
                "type": "HYPERTENSION_STAGE_2",
                "severity": "WARNING",
                "message": f"High blood pressure detected: {systolic}/{diastolic} mmHg (threshold: >=140/90 mmHg)"
            })

    # HRV check (Stress Indicator)
    if hrv is not None and hrv < 20:
        anomalies.append({
            "type": "HIGH_STRESS_STATE",
            "severity": "INFO",
            "message": f"Low heart rate variability indicates elevated physical/mental fatigue: {hrv} ms"
        })

    return anomalies


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main entrypoint for AWS Lambda."""
    # Handle CORS Preflight
    http_method = event.get("requestContext", {}).get("http", {}).get("method", event.get("httpMethod", ""))
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    try:
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body) if body else {}
        else:
            payload = body

        user_id = payload.get("user_id") or payload.get("metadata", {}).get("user_id", "usr_default")
        timestamp = payload.get("timestamp") or payload.get("metadata", {}).get("timestamp") or datetime.now(timezone.utc).isoformat()
        
        # Extract sensor payload
        vitals_data = payload.get("vitals", payload)
        source = payload.get("source", "edge_pi4_muse2")

        # Evaluate anomalies
        anomalies = evaluate_vital_anomalies(vitals_data)
        
        record_data = {
            "source": source,
            "vitals": vitals_data,
            "anomalies": anomalies,
            "has_anomaly": len(anomalies) > 0,
            "received_at": datetime.now(timezone.utc).isoformat()
        }

        # Save to DynamoDB
        saved_record = save_vitals_record(user_id=user_id, timestamp=timestamp, data=record_data)

        response_body = {
            "status": "success",
            "message": "Vital signs recorded successfully",
            "user_id": user_id,
            "timestamp": timestamp,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }

        return {
            "statusCode": 201,
            "headers": CORS_HEADERS,
            "body": json.dumps(response_body)
        }

    except json.JSONDecodeError as err:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "error": f"Invalid JSON payload: {str(err)}"})
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "error", "error": f"Internal server error: {str(exc)}"})
        }
