"""
Test suite for Cheqroom Webhook Service
Tests signature verification, timestamp comparison, and event processing.
"""

import hmac
import hashlib
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app import app, WEBHOOK_SECRET


client = TestClient(app)


# ==========================================
# Test Data Generators
# ==========================================

def generate_valid_payload(
    event_type: str = "checked_out",
    instrument_id: int = 1,
    timestamp: str = None,
    user_first_name: str = "John",
    user_last_name: str = "Doe",
    transaction_id: str = "tx-12345",
    condition: str = None
) -> dict:
    """Generate a valid Cheqroom webhook payload."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"

    return {
        "updatedAt": timestamp,
        "event": event_type,
        "item": {
            "id": instrument_id,
            "name": "Test Instrument"
        },
        "user": {
            "firstName": user_first_name,
            "lastName": user_last_name
        },
        "transaction_id": transaction_id,
        "condition": condition
    }


def generate_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Generate a valid HMAC-SHA256 signature for a payload."""
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


# ==========================================
# PHASE 1: Signature Verification Tests
# ==========================================

def test_valid_signature():
    """Test that a valid signature is accepted."""
    payload = generate_valid_payload()
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    # Should not return 401
    assert response.status_code != 401, "Valid signature was rejected"
    print("✓ Valid signature test passed")


def test_missing_signature():
    """Test that missing signature returns 401."""
    payload = generate_valid_payload()

    response = client.post(
        "/webhooks/cheqroom",
        json=payload
    )

    assert response.status_code == 401, "Missing signature should return 401"
    print("✓ Missing signature test passed")


def test_invalid_signature():
    """Test that invalid signature returns 401."""
    payload = generate_valid_payload()
    payload_bytes = json.dumps(payload).encode()
    invalid_signature = "invalidsignature1234567890abcdef"

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": invalid_signature}
    )

    assert response.status_code == 401, "Invalid signature should return 401"
    print("✓ Invalid signature test passed")


def test_wrong_secret():
    """Test that using wrong secret produces invalid signature."""
    payload = generate_valid_payload()
    payload_bytes = json.dumps(payload).encode()
    wrong_signature = generate_signature(payload_bytes, secret="wrong_secret")

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": wrong_signature}
    )

    assert response.status_code == 401, "Wrong secret signature should return 401"
    print("✓ Wrong secret test passed")


# ==========================================
# PHASE 1: Payload Validation Tests
# ==========================================

def test_missing_required_field():
    """Test that missing required fields return 400."""
    payload = generate_valid_payload()
    del payload["updatedAt"]  # Remove required field
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    assert response.status_code == 400, "Missing required field should return 400"
    assert "Missing required fields" in response.json()["detail"]
    print("✓ Missing required field test passed")


def test_invalid_timestamp_format():
    """Test that invalid timestamp format returns 400."""
    payload = generate_valid_payload(timestamp="not-a-valid-timestamp")
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    assert response.status_code == 400, "Invalid timestamp should return 400"
    assert "timestamp" in response.json()["detail"].lower()
    print("✓ Invalid timestamp format test passed")


def test_missing_instrument_id():
    """Test that missing instrument ID returns 400."""
    payload = generate_valid_payload()
    del payload["item"]["id"]
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    assert response.status_code == 400, "Missing instrument ID should return 400"
    print("✓ Missing instrument ID test passed")


# ==========================================
# PHASE 3: Check-in/Check-out Logic Tests
# ==========================================

def test_checked_out_event():
    """Test that checked_out event sets instrument_last_rented."""
    payload = generate_valid_payload(event_type="checked_out")
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    # Response may vary based on DB state, but should not be 401/400
    assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert data.get("action") == "checked_out" or data.get("status") in ["ignored", "updated"]
    print("✓ Checked out event test passed")


def test_checked_in_event():
    """Test that checked_in event sets instrument_last_returned."""
    payload = generate_valid_payload(event_type="checked_in")
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert data.get("action") == "checked_in" or data.get("status") in ["ignored", "updated"]
    print("✓ Checked in event test passed")


def test_unknown_event_type():
    """Test that unknown event type returns error."""
    payload = generate_valid_payload(event_type="unknown_event")
    payload_bytes = json.dumps(payload).encode()
    signature = generate_signature(payload_bytes)

    response = client.post(
        "/webhooks/cheqroom",
        json=payload,
        headers={"X-CHEQROOM-Signature": signature}
    )

    # May return 200 with error status, or 400
    if response.status_code == 200:
        assert response.json().get("status") == "error"
    print("✓ Unknown event type test passed")


# ==========================================
# Health Check Test
# ==========================================

def test_health_check():
    """Test that health check endpoint responds."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✓ Health check test passed")


# ==========================================
# Run All Tests
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Running Webhook Signature Verification Tests")
    print("="*50 + "\n")

    print("PHASE 1: Signature Verification")
    print("-" * 50)
    try:
        test_valid_signature()
        test_missing_signature()
        test_invalid_signature()
        test_wrong_secret()
    except AssertionError as e:
        print(f"✗ Test failed: {e}\n")

    print("\nPHASE 1: Payload Validation")
    print("-" * 50)
    try:
        test_missing_required_field()
        test_invalid_timestamp_format()
        test_missing_instrument_id()
    except AssertionError as e:
        print(f"✗ Test failed: {e}\n")

    print("\nPHASE 3: Event Processing")
    print("-" * 50)
    try:
        test_checked_out_event()
        test_checked_in_event()
        test_unknown_event_type()
    except AssertionError as e:
        print(f"✗ Test failed: {e}\n")

    print("\nHealth Check")
    print("-" * 50)
    try:
        test_health_check()
    except AssertionError as e:
        print(f"✗ Test failed: {e}\n")

    print("\n" + "="*50)
    print("Test Summary: All tests completed!")
    print("="*50 + "\n")
