"""
Authentication & Security Testing

Demonstrates testing of authentication mechanisms, API keys,
and permission validation.

Requirements: requests
Run: pytest api_tests/test_auth.py -v
"""

import requests

BASE_URL = "https://petstore.swagger.io/v2"

# Some PetStore endpoints require authentication via API key
# We use the default PetStore headers for unauthenticated access

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# ─────────────────────────────────────────────────────────────────────
# 1. Unauthenticated Access
# ─────────────────────────────────────────────────────────────────────

def test_public_endpoint_access():
    """Verify that public endpoints are accessible without auth"""
    # PetStore's findByStatus is a public endpoint
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200, \
        f"Public endpoint should be accessible: got {response.status_code}"
    print(f"  ✅ Public endpoint accessible without auth (200)")


def test_store_orders_without_auth():
    """Verify that store endpoints can be accessed (PetStore is open)"""
    # PetStore /store/inventory is publicly accessible
    response = requests.get(
        f"{BASE_URL}/store/inventory",
        headers=HEADERS
    )
    assert response.status_code == 200, \
        f"Store inventory should be accessible: got {response.status_code}"
    
    inventory = response.json()
    print(f"  ✅ Store inventory accessible. Status counts: {dict(list(inventory.items())[:5])}")


# ─────────────────────────────────────────────────────────────────────
# 2. Invalid / Malformed Requests (Security Edge Cases)
# ─────────────────────────────────────────────────────────────────────

def test_sql_injection_attempt():
    """Attempt SQL injection via pet ID — verify API handles it gracefully"""
    malicious_id = "1; DROP TABLE pets;--"
    response = requests.get(
        f"{BASE_URL}/pet/{malicious_id}",
        headers=HEADERS
    )
    # PetStore is a demo API — it may return 200 (mock server) or 400/404 (real server)
    # We document the behavior rather than assert a specific code
    print(f"  ℹ️  SQL injection attempt returned {response.status_code}")
    if response.status_code in (400, 404):
        print(f"  ✅ API correctly rejected the malicious input")
    elif response.status_code == 200:
        print(f"  ℹ️  PetStore demo API accepted the input (mock server limitation)")
        print(f"  ℹ️  In production, this should be caught by input validation")
    else:
        print(f"  ℹ️  Unexpected status code — API behavior noted")


def test_xss_attempt():
    """Attempt XSS via pet name — ensure proper handling"""
    xss_payload = "<script>alert('XSS')</script>"
    
    # Random ID to avoid collisions on shared PetStore API (parallel CI runs / other users)
    import random
    response = requests.post(f"{BASE_URL}/pet", json={
        "id": random.randint(100000, 999999),
        "name": xss_payload,
        "status": "available"
    }, headers=HEADERS)
    
    # PetStore allows it (demo API), but we verify the response structure
    if response.status_code == 200:
        pet = response.json()
        assert pet["name"] == xss_payload, "Name should match what was sent"
        print(f"  ✅ XSS payload accepted (demo API) — name contains: {pet['name'][:50]}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/pet/{pet['id']}")
    else:
        print(f"  ℹ️  XSS payload rejected with status {response.status_code}")


# ─────────────────────────────────────────────────────────────────────
# 3. API Key / Header Validation
# ─────────────────────────────────────────────────────────────────────

def test_invalid_api_key():
    """Test with invalid API key — PetStore may not enforce, but we demonstrate"""
    bad_headers = {
        **HEADERS,
        "api_key": "invalid-key-12345"
    }
    
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=bad_headers
    )
    # PetStore is open — still returns 200, but we document this
    print(f"  ℹ️  Invalid API key: returned {response.status_code}")
    print(f"  ℹ️  PetStore is a demo API and does not enforce authentication")


def test_missing_content_type():
    """Test request without Content-Type header"""
    bad_headers = {"Accept": "application/json"}
    
    response = requests.post(f"{BASE_URL}/pet", 
        data="not-json-data",
        headers=bad_headers
    )
    # Should handle gracefully
    print(f"  ℹ️  Missing Content-Type: returned {response.status_code}")
    print(f"  ℹ️  Response: {response.text[:100]}")


# ─────────────────────────────────────────────────────────────────────
# 4. HTTP Method Overriding & Unexpected Methods
# ─────────────────────────────────────────────────────────────────────

def test_unexpected_http_method():
    """Test PATCH method on endpoint that doesn't support it"""
    response = requests.patch(
        f"{BASE_URL}/pet/1",
        headers=HEADERS,
        json={"name": "Patched"}
    )
    # Should return 405 Method Not Allowed or similar
    print(f"  ℹ️  PATCH on /pet returned {response.status_code}")
    if response.status_code == 405:
        print(f"  ✅ Correctly rejected with 405 Method Not Allowed")


def test_head_request():
    """Test HEAD request — verify headers without body"""
    response = requests.head(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    print(f"  ℹ️  HEAD request returned {response.status_code}")
    print(f"  ℹ️  Response headers: {dict(response.headers)}")