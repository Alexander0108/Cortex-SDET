"""
Cortex-SDET Data-Driven Testing CLI

Interactive CLI for demonstrating data-driven testing with CSV and JSON.
Loads test data files and runs validation with visual feedback.

Run: python3 data_driven_tests/data_cli.py
"""

import csv
import json
import os
import subprocess
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_CSV = os.path.join(DATA_DIR, "test_users.csv")
PRODUCTS_JSON = os.path.join(DATA_DIR, "test_products.json")


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


# ─────────────────────────────────────────────────────────────────────
# Menu Actions
# ─────────────────────────────────────────────────────────────────────

def action_show_csv_data():
    """Show CSV test data in a readable format"""
    print_header("📄 CSV TEST DATA — Users")
    
    with open(USERS_CSV, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n  File: data/test_users.csv")
    print(f"  Columns: {', '.join(reader.fieldnames)}")
    print(f"  Total test scenarios: {len(rows)}")
    print()
    
    for i, row in enumerate(rows, 1):
        status_icon = "✅" if row["expected_status"] == "valid" else "❌"
        print(f"  {status_icon} #{i}: {row['email']} | role={row['role']} | "
              f"pwd_len={len(row['password'])} | expected={row['expected_status']}")


def action_show_json_data():
    """Show JSON test data in a readable format"""
    print_header("📄 JSON TEST DATA — Products")
    
    with open(PRODUCTS_JSON, "r") as f:
        products = json.load(f)
    
    print(f"\n  File: data/test_products.json")
    print(f"  Total products: {len(products)}")
    print()
    
    for product in products:
        # Determine expected validity
        issues = []
        if not product.get("name"):
            issues.append("empty name")
        if product.get("price", 0) <= 0:
            issues.append(f"bad price (${product.get('price', 0)})")
        if product.get("stock", 0) < 0:
            issues.append(f"negative stock ({product.get('stock', 0)})")
        
        status_icon = "⚠️" if issues else "✅"
        issue_text = f" — {'; '.join(issues)}" if issues else ""
        
        print(f"  {status_icon} #{product['id']}: {product['name'] or 'EMPTY'} | "
              f"${product['price']} | stock={product['stock']}{issue_text}")


def action_run_csv_tests():
    """Run CSV data-driven tests via pytest"""
    print_header("🏃 RUN CSV DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(os.path.dirname(__file__), "test_csv_reader.py"),
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print("\n" + result.stdout[:500])
    if result.stderr:
        print(f"  stderr: {result.stderr[:200]}")
    
    # Parse pass/fail count
    passed = result.stdout.count("PASSED")
    failed = result.stdout.count("FAILED")
    total = passed + failed
    
    if result.returncode == 0:
        print(f"\n  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"\n  ❌ {failed}/{total} TESTS FAILED")


def action_run_json_tests():
    """Run JSON data-driven tests via pytest"""
    print_header("🏃 RUN JSON DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(os.path.dirname(__file__), "test_json_reader.py"),
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print("\n" + result.stdout[:500])
    if result.stderr:
        print(f"  stderr: {result.stderr[:200]}")
    
    # Parse pass/fail count
    passed = result.stdout.count("PASSED")
    failed = result.stdout.count("FAILED")
    total = passed + failed
    
    if result.returncode == 0:
        print(f"\n  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"\n  ❌ {failed}/{total} TESTS FAILED")


def action_run_all():
    """Run all data-driven tests"""
    print_header("🏃 RUN ALL DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.dirname(__file__),
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print("\n" + result.stdout[:800])
    if result.stderr:
        print(f"  stderr: {result.stderr[:200]}")
    
    passed = result.stdout.count("PASSED")
    failed = result.stdout.count("FAILED")
    total = passed + failed
    
    if result.returncode == 0:
        print(f"\n  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"\n  ❌ {failed}/{total} TESTS FAILED — see details above")


# ─────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────

def show_menu():
    """Display the interactive menu"""
    print("\n" + "█" * 65)
    print("  📊  CORTEX-SDET DATA-DRIVEN TESTING CLI")
    print("  CSV / JSON Data Validation — Parameterized Tests")
    print("█" * 65)
    print("""
  ┌─ ACTIONS ──────────────────────────────────────┐
  │  1. 📄  Show CSV test data (users)             │
  │  2. 📄  Show JSON test data (products)         │
  │  3. 🏃  Run CSV data-driven tests (pytest)     │
  │  4. 🏃  Run JSON data-driven tests (pytest)    │
  │  5. 🏃  Run ALL data-driven tests (pytest)     │
  │  0. ❌  Exit                                   │
  └─────────────────────────────────────────────────┘""")


def main():
    """Main CLI loop"""
    while True:
        show_menu()
        choice = input("\n  👉 Select action (0-5): ").strip()
        
        if choice == "1":
            action_show_csv_data()
        elif choice == "2":
            action_show_json_data()
        elif choice == "3":
            action_run_csv_tests()
        elif choice == "4":
            action_run_json_tests()
        elif choice == "5":
            action_run_all()
        elif choice == "0":
            print("\n  👋 Exiting...")
            break
        else:
            print("\n  ⚠️  Invalid choice. Please enter 0-5.")
        
        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()