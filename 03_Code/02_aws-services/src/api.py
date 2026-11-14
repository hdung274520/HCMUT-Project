import json


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=lambda d: int(d) if d == int(d) else float(d)),  # Decimal -> number
    }
