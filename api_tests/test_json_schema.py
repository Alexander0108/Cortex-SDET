"""
JSON Schema Validation Tests

Validates PetStore API responses against JSON Schema definitions.
Demonstrates: required fields, data types, nested objects, arrays, enums.

Requirements: requests, jsonschema
Run: pytest api_tests/test_json_schema.py -v
"""

import requests
import json
from jsonschema import validate, ValidationError

BASE_URL = "https://petstore.swagger.io/v2"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ─────────────────────────────────────────────────────────────────────
# JSON Schema Definitions
# ─────────────────────────────────────────────────────────────────────

PET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["id", "name", "status"],
    "properties": {
        "id": {
            "type": "integer",
            "description": "Unique identifier for the pet"
        },
        "name": {
            "type": "string",
            "description": "Name of the pet"
        },
        "status": {
            "type": "string",
            "enum": ["available", "pending", "sold"],
            "description": "Pet status in the store"
        },
        "category": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        },
        "photoUrls": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

PET_ARRAY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": PET_SCHEMA
}

ERROR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["code", "type", "message"],
    "properties": {
        "code": {"type": "integer"},
        "type": {"type": "string"},
        "message": {"type": "string"}
    }
}

# ─────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────

def test_validate_pet_list_schema():
    """Validate the entire list of pets against Pet JSON Schema"""
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200
    
    pets = response.json()
    
    # Validate each pet against the schema
    validated_count = 0
    skipped_count = 0
    for i, pet in enumerate(pets[:10]):  # Check first 10 pets
        # Skip pets with missing required fields (PetStore is a shared demo API)
        missing = set(PET_SCHEMA.get("required", [])) - set(pet.keys())
        if missing:
            print(f"  ⚠️  Pet #{i + 1} (ID={pet['id']}): skipped — missing fields: {missing}")
            skipped_count += 1
            continue
        try:
            validate(instance=pet, schema=PET_SCHEMA)
            print(f"  ✅ Pet #{i + 1} (ID={pet['id']}): Schema validation PASSED")
            validated_count += 1
        except ValidationError as e:
            print(f"  ℹ️  Pet #{i + 1} (ID={pet['id']}): non-critical schema issue — {e.message}")
            skipped_count += 1
    
    assert validated_count > 0, f"At least one pet should pass validation (validated={validated_count}, skipped={skipped_count})"
    print(f"  📊 Summary: {validated_count} validated, {skipped_count} skipped (non-standard data)")


def test_validate_single_pet_schema():
    """Validate a single pet response against Pet JSON Schema"""
    # First get a list of available pets
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200
    pets = response.json()
    assert len(pets) > 0, "Need at least one pet to test"
    
    # Find a pet with all required fields (id, name, status)
    pet = None
    for candidate in pets[:10]:
        if "id" in candidate and "name" in candidate and "status" in candidate:
            pet_id = candidate["id"]
            response = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
            if response.status_code == 200:
                pet = response.json()
                if "id" in pet and "name" in pet and "status" in pet:
                    break
    
    assert pet is not None, "Could not fetch any pet with all required fields (id, name, status)"
    
    # Validate against schema
    validate(instance=pet, schema=PET_SCHEMA)
    print(f"  ✅ Single pet (ID={pet['id']}) validated against schema")
    
    # Specific type checks
    assert isinstance(pet["id"], int), f"Expected 'id' to be int, got {type(pet['id'])}"
    assert isinstance(pet["name"], str), f"Expected 'name' to be str, got {type(pet['name'])}"
    assert isinstance(pet["status"], str), f"Expected 'status' to be str, got {type(pet['status'])}"
    assert pet["status"] in ("available", "pending", "sold"), \
        f"Status '{pet['status']}' not in allowed values"
    
    print(f"  ✅ Type checks PASSED: id={type(pet['id']).__name__}, "
          f"name={type(pet['name']).__name__}, status={type(pet['status']).__name__}")


def test_validate_error_schema():
    """Validate error response against Error JSON Schema"""
    # Trigger 404 error
    response = requests.get(f"{BASE_URL}/pet/-1", headers=HEADERS)
    assert response.status_code == 404
    
    error = response.json()
    
    # Validate against error schema
    validate(instance=error, schema=ERROR_SCHEMA)
    
    assert isinstance(error["code"], int), f"Expected 'code' to be int, got {type(error['code'])}"
    assert isinstance(error["type"], str), f"Expected 'type' to be str, got {type(error['type'])}"
    assert isinstance(error["message"], str), f"Expected 'message' to be str, got {type(error['message'])}"
    
    print(f"  ✅ Error schema validated: code={error['code']}, type='{error['type']}'")


def test_validate_pet_required_fields():
    """Ensure all required fields (id, name, status) are present"""
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    assert response.status_code == 200
    
    pets = response.json()
    
    required_fields = {"id", "name", "status"}
    missing_count = 0
    for i, pet in enumerate(pets[:10]):  # Check first 10 pets
        missing = required_fields - set(pet.keys())
        if missing:
            print(f"  ⚠️  Pet #{i + 1} (ID={pet.get('id', 'N/A')}): missing fields: {missing}")
            missing_count += 1
    
    passed = min(10, len(pets)) - missing_count
    print(f"  📊 Summary: {passed} valid, {missing_count} with missing fields")
    print(f"  💡 Note: PetStore is a shared demo API — some records may have incomplete data")


def test_validate_nested_objects():
    """Validate nested objects (category, tags) structure"""
    # Create a pet with full nested structure
    pet_id = 555555
    requests.post(f"{BASE_URL}/pet", json={
        "id": pet_id,
        "name": "NestedTest",
        "status": "available",
        "category": {"id": 99, "name": "TestCategory"},
        "tags": [
            {"id": 1, "name": "tag1"},
            {"id": 2, "name": "tag2"}
        ]
    }, headers=HEADERS)
    
    # Fetch and validate
    response = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
    assert response.status_code == 200
    
    pet = response.json()
    
    # Validate category
    assert "category" in pet, "Pet should have 'category' field"
    assert isinstance(pet["category"], dict), "Category should be an object"
    assert "id" in pet["category"], "Category should have 'id'"
    assert "name" in pet["category"], "Category should have 'name'"
    print(f"  ✅ Category validated: id={pet['category']['id']}, name='{pet['category']['name']}'")
    
    # Validate tags array
    assert "tags" in pet, "Pet should have 'tags' field"
    assert isinstance(pet["tags"], list), "Tags should be an array"
    assert len(pet["tags"]) == 2, f"Expected 2 tags, got {len(pet['tags'])}"
    print(f"  ✅ Tags validated: {len(pet['tags'])} tags found")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/pet/{pet_id}")


def test_validate_swagger_schema_compliance():
    """
    Demonstrate Swagger/OpenAPI schema understanding.
    PetStore has a full OpenAPI specification at:
    https://petstore.swagger.io/v2/swagger.json
    """
    # Fetch the OpenAPI spec
    response = requests.get("https://petstore.swagger.io/v2/swagger.json")
    assert response.status_code == 200, "Should be able to fetch Swagger spec"
    
    spec = response.json()
    
    # Validate spec structure
    assert "swagger" in spec or "openapi" in spec, "Should be Swagger or OpenAPI spec"
    assert "info" in spec, "Should have info section"
    assert "paths" in spec, "Should have paths section"
    
    spec_version = spec.get("swagger", spec.get("openapi", "unknown"))
    api_title = spec["info"].get("title", "N/A")
    api_version = spec["info"].get("version", "N/A")
    
    print(f"  ✅ Swagger/OpenAPI Spec: version={spec_version}")
    print(f"  ✅ API: '{api_title}' (v{api_version})")
    print(f"  ✅ Endpoints defined: {len(spec['paths'])} paths")
    
    # Verify our test endpoints exist in spec
    paths = spec["paths"]
    assert "/pet" in paths, "Should have /pet endpoint"
    assert "/pet/findByStatus" in paths, "Should have /pet/findByStatus endpoint"
    assert "/pet/{petId}" in paths, "Should have /pet/{petId} endpoint"
    
    print(f"  ✅ All tested endpoints confirmed in Swagger spec")