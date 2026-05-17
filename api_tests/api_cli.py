"""
Cortex-SDET API Testing CLI

Interactive CLI for demonstrating REST API testing with PetStore.
Allows running individual CRUD operations with visual feedback.

Run: python3 api_tests/api_cli.py
"""

import requests
import json
import random

BASE_URL = "https://petstore.swagger.io/v2"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def print_response(response, show_body=True):
    """Print formatted API response"""
    print(f"\n  Status Code: {response.status_code} ", end="")
    if response.status_code in (200, 201):
        print("✅")
    elif response.status_code in (400, 404, 405):
        print("⚠️")
    else:
        print("❌")
    
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"  Server: {response.headers.get('Server', 'N/A')}")
    
    if show_body and response.text:
        try:
            body = response.json()
            print(f"\n  Response Body:")
            print(f"  {json.dumps(body, indent=2)[:500]}")
        except:
            print(f"\n  Response: {response.text[:200]}")


# ─────────────────────────────────────────────────────────────────────
# Menu Actions
# ─────────────────────────────────────────────────────────────────────

def action_get_pets():
    """GET /pet/findByStatus — fetch pets by status"""
    print_header("📦 GET PETS BY STATUS")
    
    status = input("  Status (available/sold/pending) [available]: ").strip() or "available"
    
    print(f"\n  [*] GET {BASE_URL}/pet/findByStatus?status={status}")
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": status},
        headers=HEADERS
    )
    
    print_response(response)
    
    if response.status_code == 200:
        pets = response.json()
        print(f"\n  📊 Found {len(pets)} pets with status '{status}'")
        if pets:
            print(f"\n  First 3 pets:")
            for i, pet in enumerate(pets[:3]):
                pet_name = pet.get('name', 'N/A')
                pet_status = pet.get('status', 'N/A')
                pet_id = pet.get('id', 'N/A')
                print(f"    {i+1}. ID={pet_id}, Name='{pet_name}', Status='{pet_status}'")


def action_get_pet_by_id():
    """GET /pet/{petId} — fetch single pet"""
    print_header("🔍 GET PET BY ID")
    
    pet_id = input("  Enter pet ID [try 1]: ").strip() or "1"
    
    print(f"\n  [*] GET {BASE_URL}/pet/{pet_id}")
    response = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
    
    print_response(response)
    
    if response.status_code == 200:
        pet = response.json()
        pet_id = pet.get('id', 'N/A')
        pet_name = pet.get('name', 'N/A')
        pet_status = pet.get('status', 'N/A')
        print(f"\n  ✅ Retrieved: ID={pet_id}, Name='{pet_name}', Status='{pet_status}'")
        if "category" in pet and pet["category"]:
            print(f"  🏷️  Category: {pet['category'].get('name', 'N/A')}")
        if "tags" in pet and pet["tags"]:
            print(f"  🏷️  Tags: {', '.join(t.get('name', '') for t in pet['tags'])}")


def action_create_pet():
    """POST /pet — create a new pet"""
    print_header("➕ CREATE NEW PET")
    
    name = input("  Pet name [CortexBot]: ").strip() or "CortexBot"
    status = input("  Status (available/pending/sold) [available]: ").strip() or "available"
    pet_id = random.randint(100000, 999999)
    
    new_pet = {
        "id": pet_id,
        "name": name,
        "status": status,
        "category": {"id": 1, "name": "AI-Assistants"},
        "tags": [{"id": 1, "name": "Automated"}]
    }
    
    print(f"\n  [*] POST {BASE_URL}/pet")
    print(f"  [*] Request Body:")
    print(f"  {json.dumps(new_pet, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/pet", json=new_pet, headers=HEADERS)
    
    print_response(response)
    
    if response.status_code == 200:
        created = response.json()
        print(f"\n  ✅ Pet created: ID={created['id']}, Name='{created['name']}'")
        input("\n  Press Enter to delete this pet (cleanup)...")
        delete_response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
        print(f"  🗑️  Cleanup: DELETE returned {delete_response.status_code}")


def action_update_pet():
    """PUT /pet — update an existing pet"""
    print_header("✏️ UPDATE PET")
    
    # First create a pet to update
    temp_id = 444444
    print(f"\n  [*] First, creating a temporary pet (ID={temp_id})...")
    requests.post(f"{BASE_URL}/pet", json={
        "id": temp_id, "name": "BeforeUpdate", "status": "available"
    }, headers=HEADERS)
    
    new_name = input("  New name [AfterUpdate]: ").strip() or "AfterUpdate"
    new_status = input("  New status (available/pending/sold) [sold]: ").strip() or "sold"
    
    updated_pet = {
        "id": temp_id,
        "name": new_name,
        "status": new_status
    }
    
    print(f"\n  [*] PUT {BASE_URL}/pet")
    print(f"  [*] Request Body:")
    print(f"  {json.dumps(updated_pet, indent=2)}")
    
    response = requests.put(f"{BASE_URL}/pet", json=updated_pet, headers=HEADERS)
    
    print_response(response)
    
    if response.status_code == 200:
        pet = response.json()
        print(f"\n  ✅ Updated: ID={pet['id']}, Name='{pet['name']}', Status='{pet['status']}'")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/pet/{temp_id}")


def action_delete_pet():
    """DELETE /pet/{petId} — delete a pet"""
    print_header("🗑️ DELETE PET")
    
    # First create a pet to delete
    temp_id = 333333
    print(f"\n  [*] First, creating a temporary pet (ID={temp_id})...")
    requests.post(f"{BASE_URL}/pet", json={
        "id": temp_id, "name": "ToBeDeleted", "status": "available"
    }, headers=HEADERS)
    print(f"  ✅ Temporary pet created")
    
    confirm = input(f"\n  Delete pet ID={temp_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("  ⏭️  Skipping...")
        requests.delete(f"{BASE_URL}/pet/{temp_id}")
        return
    
    print(f"\n  [*] DELETE {BASE_URL}/pet/{temp_id}")
    response = requests.delete(f"{BASE_URL}/pet/{temp_id}", headers=HEADERS)
    
    print_response(response)
    
    if response.status_code == 200:
        # Verify deletion
        verify = requests.get(f"{BASE_URL}/pet/{temp_id}", headers=HEADERS)
        print(f"\n  [*] Verifying: GET {BASE_URL}/pet/{temp_id} → {verify.status_code}")
        if verify.status_code == 404:
            print(f"  ✅ Confirmed: Pet no longer exists (404)")
        else:
            print(f"  ⚠️  Pet still exists (status {verify.status_code})")


def action_json_schema_validation():
    """Run JSON Schema validation demo"""
    print_header("📋 JSON SCHEMA VALIDATION")
    
    print("\n  [*] Fetching pet list for schema validation...")
    response = requests.get(
        f"{BASE_URL}/pet/findByStatus",
        params={"status": "available"},
        headers=HEADERS
    )
    
    if response.status_code != 200:
        print("  ❌ Failed to fetch pets")
        return
    
    pets = response.json()
    first_pet = pets[0]
    
    print(f"\n  📄 Sample pet data:")
    print(f"  {json.dumps(first_pet, indent=2)[:300]}")
    
    print(f"\n  🔍 JSON Schema Validation Checklist:")
    print(f"  ┌────────────────────────────────────────────┬──────────┐")
    
    # Check required fields
    for field in ["id", "name", "status"]:
        present = field in first_pet
        status_icon = "✅" if present else "❌"
        field_type = type(first_pet[field]).__name__ if present else "N/A"
        print(f"  │ Required '{field}' ({field_type}){' ' * (15 - len(field))}│ {status_icon}        │")
    
    # Check optional fields
    for field in ["category", "tags", "photoUrls"]:
        present = field in first_pet
        status_icon = "✅" if present else "⬜"
        print(f"  │ Optional '{field}'{' ' * (21 - len(field))}│ {status_icon}        │")
    
    print(f"  └────────────────────────────────────────────┴──────────┘")
    
    # Check status enum
    status = first_pet.get("status", "")
    if status in ("available", "pending", "sold"):
        print(f"\n  ✅ Status '{status}' is valid (enum: available/pending/sold)")
    else:
        print(f"\n  ❌ Status '{status}' is NOT in enum")
    
    print(f"\n  📊 Summary: {len(pets)} pets fetched, first pet validated ✓")


def action_swagger_demo():
    """Show Swagger/OpenAPI spec"""
    print_header("📖 SWAGGER / OPENAPI SPECIFICATION")
    
    print("\n  [*] Fetching Swagger spec from PetStore...")
    response = requests.get("https://petstore.swagger.io/v2/swagger.json")
    
    if response.status_code != 200:
        print("  ❌ Failed to fetch Swagger spec")
        return
    
    spec = response.json()
    
    version = spec.get("swagger", spec.get("openapi", "N/A"))
    title = spec["info"].get("title", "N/A")
    api_version = spec["info"].get("version", "N/A")
    description = spec["info"].get("description", "")[:100]
    
    print(f"\n  📄 Specification:")
    print(f"     Version: {version}")
    print(f"     API: {title} v{api_version}")
    print(f"     Description: {description}...")
    
    paths = spec.get("paths", {})
    print(f"\n  📍 Endpoints ({len(paths)} total):")
    print(f"  ┌──────────────┬──────────────────────────────────────────┐")
    
    for path, methods in list(paths.items())[:8]:
        method = list(methods.keys())[0].upper() if methods else "?"
        short_path = path[:40] if len(path) > 40 else path
        print(f"  │ {method:<12} │ {short_path:<40} │")
    
    print(f"  └──────────────┴──────────────────────────────────────────┘")
    print(f"\n  🔗 Full spec: https://petstore.swagger.io/v2/swagger.json")


def action_run_all():
    """Run all API tests using pytest"""
    print_header("🏃 RUN ALL API TESTS")
    import subprocess
    
    print("\n  [*] Running: pytest api_tests/ -v --tb=short\n")
    result = subprocess.run(
        ["pytest", "api_tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"  stderr: {result.stderr[:500]}")
    
    if result.returncode == 0:
        print("\n  ✅ ALL TESTS PASSED!")
    else:
        print(f"\n  ❌ Some tests failed (exit code {result.returncode})")


# ─────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────

def show_menu():
    """Display the interactive menu"""
    print("\n" + "█" * 65)
    print("  🧠  CORTEX-SDET API TESTING CLI")
    print("  REST API Testing — PetStore Demo")
    print("█" * 65)
    print("""
  ┌─ ACTIONS ──────────────────────────────────────────┐
  │  1. 📦  GET      — List pets by status             │
  │  2. 🔍  GET      — Get pet by ID                   │
  │  3. ➕  POST     — Create a new pet                │
  │  4. ✏️  PUT      — Update an existing pet          │
  │  5. 🗑️  DELETE   — Delete a pet                    │
  │                                                     │
  │  6. 📋  JSON Schema Validation                     │
  │  7. 📖  Swagger / OpenAPI Spec                     │
  │                                                     │
  │  8. 🏃  Run All API Tests (pytest)                 │
  │  0. ❌  Exit                                       │
  └─────────────────────────────────────────────────────┘""")


def main():
    """Main CLI loop"""
    while True:
        show_menu()
        choice = input("\n  👉 Select action (0-8): ").strip()
        
        if choice == "1":
            action_get_pets()
        elif choice == "2":
            action_get_pet_by_id()
        elif choice == "3":
            action_create_pet()
        elif choice == "4":
            action_update_pet()
        elif choice == "5":
            action_delete_pet()
        elif choice == "6":
            action_json_schema_validation()
        elif choice == "7":
            action_swagger_demo()
        elif choice == "8":
            action_run_all()
        elif choice == "0":
            print("\n  👋 Exiting...")
            break
        else:
            print("\n  ⚠️  Invalid choice. Please enter 0-8.")
        
        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()