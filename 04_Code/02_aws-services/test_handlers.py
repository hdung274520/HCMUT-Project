#!/usr/bin/env python3
"""
Unit tests for AWS Lambda handlers with mocked DynamoDB tables.
Runs in CI/CD or local test harness without needing real AWS credentials.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from handlers.ingest_vitals import evaluate_vital_anomalies, lambda_handler as ingest_handler
from handlers.query_vitals import lambda_handler as query_handler
from handlers.session_handler import lambda_handler as session_handler
from common.db_helper import float_to_decimal, decimal_to_float
from decimal import Decimal


def test_float_decimal_conversion():
    print("Test 1: Float <-> Decimal conversions...")
    data = {"hr": 75.5, "bands": [0.1, 0.4, 0.5], "name": "user"}
    dec = float_to_decimal(data)
    assert isinstance(dec["hr"], Decimal)
    assert isinstance(dec["bands"][0], Decimal)
    
    back = decimal_to_float(dec)
    assert back["hr"] == 75.5
    assert back["bands"] == [0.1, 0.4, 0.5]
    print(" -> SUCCESS: Float/Decimal round-trip passed.")


def test_anomaly_detection():
    print("Test 2: Anomaly detection logic...")
    # Normal vitals
    normal = {"heart_rate": 72, "spo2": 98, "blood_pressure": {"systolic": 120, "diastolic": 80}}
    anomalies = evaluate_vital_anomalies(normal)
    assert len(anomalies) == 0

    # High HR (Tachycardia) & Low SpO2 (Hypoxia)
    abnormal = {"heart_rate": 135, "spo2": 88, "blood_pressure": {"systolic": 150, "diastolic": 95}, "hrv": 15}
    anomalies = evaluate_vital_anomalies(abnormal)
    types = [a["type"] for a in anomalies]
    assert "TACHYCARDIA" in types
    assert "CRITICAL_HYPOXIA" in types
    assert "HYPERTENSION_STAGE_2" in types
    assert "HIGH_STRESS_STATE" in types
    print(f" -> SUCCESS: Detected {len(anomalies)} anomalies correctly.")


@patch("handlers.ingest_vitals.save_vitals_record")
def test_ingest_vitals_handler(mock_save):
    print("Test 3: Ingest Vitals Lambda Handler...")
    mock_save.return_value = {"user_id": "usr_test"}

    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "user_id": "usr_001",
            "timestamp": "2026-09-20T10:00:00Z",
            "vitals": {
                "heart_rate": 80,
                "hrv": 50.0,
                "spo2": 99.0
            }
        })
    }
    response = ingest_handler(event, None)
    if response["statusCode"] != 201:
        print("Response error:", response)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert body["user_id"] == "usr_001"
    print(" -> SUCCESS: Ingest handler returned 201.")


@patch("handlers.query_vitals.get_latest_vital")
def test_query_vitals_handler(mock_get_latest):
    print("Test 4: Query Vitals Lambda Handler...")
    mock_get_latest.return_value = {
        "user_id": "usr_001",
        "timestamp": "2026-09-20T10:00:00Z",
        "vitals": {"heart_rate": 75}
    }

    event = {
        "httpMethod": "GET",
        "rawPath": "/vitals/latest",
        "queryStringParameters": {"user_id": "usr_001"}
    }
    response = query_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert body["data"]["vitals"]["heart_rate"] == 75
    print(" -> SUCCESS: Query handler returned 200.")


@patch("handlers.session_handler.save_session")
def test_session_handler(mock_save_session):
    print("Test 5: Session Manager Lambda Handler...")
    mock_save_session.return_value = {}

    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "user_id": "usr_001",
            "session_type": "sleep",
            "metrics": {"sleep_score": 90}
        })
    }
    response = session_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["status"] == "success"
    print(" -> SUCCESS: Session handler returned 201.")



if __name__ == "__main__":
    print("=== BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG CHO AWS LAMBDA ===")
    test_float_decimal_conversion()
    test_anomaly_detection()
    test_ingest_vitals_handler()
    test_query_vitals_handler()
    test_session_handler()
    print("=== TẤT CẢ KIỂM THỬ ĐÃ ĐẠT (100% OK) ===")
