"""
PetStore REST API Tests

Demonstrates CRUD operations against PetStore API (https://petstore.swagger.io).
Covers: GET, POST, PUT, DELETE, status codes, headers, error handling.

Requirements: requests, pytest
Run: pytest api_tests/test_petstore.py -v
"""

import requests
import json

BASE_URL = "https://petstore.swagger.io/v2"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ─────────────────────────────────────────────────────────────────────
# 1. GET — Retrieve available pets
# ─────────────────────────────────────────────────────────────────────

def test_get_pets_by_status():
    """GET /pet/findByStatus — fetch pets by status (available/sold/pending)"""
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}: {response.text}"
    assert "application/json" in response.headers.get("Content-Type", ""), \
        "Response should be JSON"
    
    pets = response.json()
    assert isinstance(pets, list), "Expected a list of pets"
    assert len(pets) > 0, "Expected at least one available pet"
    
    # Validate structure of first pet
    first_pet = pets[0]
    assert "id" in first_pet, "Pet should have 'id'"
    assert "name" in first_pet, "Pet should have 'name'"
    assert "status" in first_pet, "Pet should have 'status'"
    assert first_pet["status"] == "available", \
        f"Expected status 'available', got '{first_pet['status']}'"
    
    print(f"  ✅ Found {len(pets)} available pets")
    print(f"  ✅ First pet: ID={first_pet['id']}, Name={first_pet['name']}")


def test_get_pet_by_id():
    """GET /pet/{petId} — fetch a single pet by ID"""
    # First get a known pet ID
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200
    pets = response.json()
    assert len(pets) > 0, "Need at least one pet to test GET by ID"
    
    pet_id = pets[0]["id"]
    
    # Now fetch by ID
    response = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}"
    
    pet = response.json()
    assert pet["id"] == pet_id, f"Expected ID {pet_id}, got {pet['id']}"
    assert "name" in pet, "Pet should have a name"
    assert "status" in pet, "Pet should have a status"
    
    print(f"  ✅ Retrieved pet ID={pet['id']}, Name={pet['name']}, Status={pet['status']}")


def test_get_pet_by_nonexistent_id():
    """GET /pet/{petId} with nonexistent ID — should return 404"""
    response = requests.get(f"{BASE_URL}/pet/-1", headers=HEADERS)
    assert response.status_code == 404, \
        f"Expected 404, got {response.status_code}"
    
    error = response.json()
    assert "message" in error, "Error should contain a message"
    print(f"  ✅ 404 correctly returned: {error['message']}")


# ─────────────────────────────────────────────────────────────────────
# 2. POST — Create a new pet
# ─────────────────────────────────────────────────────────────────────

def test_create_pet():
    """POST /pet — create a new pet and verify it exists"""
    import random
    pet_id = random.randint(100000, 999999)
    
    new_pet = {
        "id": pet_id,
        "name": "CortexBot",
        "status": "available",
        "category": {
            "id": 1,
            "name": "Robots"
        },
        "tags": [
            {"id": 1, "name": "AI-Powered"}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/pet", json=new_pet, headers=HEADERS)
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}: {response.text}"
    
    created_pet = response.json()
    assert created_pet["id"] == pet_id, "Pet ID should match"
    assert created_pet["name"] == "CortexBot", "Pet name should match"
    assert created_pet["status"] == "available", "Pet status should match"
    assert created_pet["category"]["name"] == "Robots", "Category should match"
    
    print(f"  ✅ Created pet ID={pet_id}, Name=CortexBot")
    
    # Cleanup: delete the created pet
    requests.delete(f"{BASE_URL}/pet/{pet_id}")


def test_create_pet_without_required_field():
    """POST /pet without required fields — should fail gracefully"""
    invalid_pet = {"status": "available"}  # Missing 'name' and 'id'
    
    response = requests.post(f"{BASE_URL}/pet", json=invalid_pet, headers=HEADERS)
    # PetStore may still return 200 (it auto-generates), but we document the behavior
    print(f"  ℹ️  POST with missing fields returned {response.status_code}")
    print(f"  ℹ️  Response: {response.text[:100]}")


# ─────────────────────────────────────────────────────────────────────
# 3. PUT — Update an existing pet
# ─────────────────────────────────────────────────────────────────────

def test_update_pet():
    """PUT /pet — update an existing pet's name and status"""
    # First create a pet
    pet_id = 888888
    create_response = requests.post(f"{BASE_URL}/pet", json={
        "id": pet_id,
        "name": "OldName",
        "status": "available"
    }, headers=HEADERS)
    assert create_response.status_code == 200
    
    # Now update it
    updated_pet = {
        "id": pet_id,
        "name": "NewName",
        "status": "sold"
    }
    response = requests.put(f"{BASE_URL}/pet", json=updated_pet, headers=HEADERS)
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}"
    
    pet = response.json()
    assert pet["name"] == "NewName", f"Expected 'NewName', got '{pet['name']}'"
    assert pet["status"] == "sold", f"Expected 'sold', got '{pet['status']}'"
    
    print(f"  ✅ Updated pet ID={pet_id}: name='NewName', status='sold'")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/pet/{pet_id}")


# ─────────────────────────────────────────────────────────────────────
# 4. DELETE — Remove a pet
# ─────────────────────────────────────────────────────────────────────

def test_delete_pet():
    """DELETE /pet/{petId} — delete a pet and verify it's gone"""
    # First create a pet to delete
    pet_id = 777777
    create_response = requests.post(f"{BASE_URL}/pet", json={
        "id": pet_id,
        "name": "DeleteMe",
        "status": "available"
    }, headers=HEADERS)
    assert create_response.status_code == 200
    
    # Delete it
    response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
    assert response.status_code == 200, \
        f"Expected 200 on delete, got {response.status_code}"
    
    # Verify it's gone
    get_response = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
    assert get_response.status_code == 404, \
        f"Expected 404 after delete, got {get_response.status_code}"
    
    print(f"  ✅ Deleted pet ID={pet_id} and confirmed 404 on re-fetch")


# ─────────────────────────────────────────────────────────────────────
# 5. Error Handling & Edge Cases
# ─────────────────────────────────────────────────────────────────────

def test_invalid_pet_id_type():
    """GET /pet/{petId} with invalid ID type (string) — should return 400"""
    response = requests.get(f"{BASE_URL}/pet/not-a-number", headers=HEADERS)
    # PetStore may return 400 or 404 depending on implementation
    assert response.status_code in (400, 404), \
        f"Expected 400 or 404, got {response.status_code}"
    print(f"  ✅ Invalid ID returns {response.status_code} as expected")


def test_response_headers():
    """Verify response headers contain expected fields"""
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200
    
    # Common security and caching headers
    headers = response.headers
    print(f"  ℹ️  Content-Type: {headers.get('Content-Type', 'N/A')}")
    print(f"  ℹ️  Cache-Control: {headers.get('Cache-Control', 'N/A')}")
    print(f"  ℹ️  Server: {headers.get('Server', 'N/A')}")
    print(f"  ℹ️  Date: {headers.get('Date', 'N/A')}")
    
    assert "Content-Type" in headers, "Response should have Content-Type header"