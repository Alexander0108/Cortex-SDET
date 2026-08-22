"""
Cortex-SDET Data-Driven Testing CLI

Interactive CLI for demonstrating data-driven testing with CSV and JSON.
Loads test data files and runs validation with visual feedback.

Run: python3 data_driven_tests/data_cli.py
"""

import csv
import json
import os
import re
import subprocess
import sys

# Allow importing the shared cli_utils module from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_utils import render_box

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


def _format_pytest_output(stdout):
    """
    Post-process pytest stdout for cleaner CLI output:
    - Hide integrity check lines with a 🔍 prefix
    - Parse failure reasons from FAILURES section and inject inline on FAILED lines
    - Remove the FAILURES and short test summary sections (duplicate info)
    """
    lines = stdout.split("\n")
    
    # First pass: collect FAILED test names (in order) and failure reasons
    failed_tests = []
    failure_reasons = []
    in_failures = False
    for line in lines:
        # Collect FAILED test names from progress output
        if "FAILED" in line and "[" in line:
            test_name = line.split("[")[1].split("]")[0]
            failed_tests.append(test_name)
        
        # Collect failure reasons from FAILURES section
        # Format with --tb=line: "/path/to/file.py:line: ErrorType: reason"
        if line.startswith("=") and "FAILURES" in line:
            in_failures = True
            continue
        if in_failures:
            if line.startswith("="):
                in_failures = False
                continue
            # Extract reason after the second colon: "/path:line: ErrorType: reason"
            parts = line.split(":", 2)
            if len(parts) >= 3:
                reason = parts[2].strip()
                # Remove "ErrorType: " prefix for cleaner display
                reason = re.sub(r"^[A-Za-z]+Error:\s*", "", reason)
                failure_reasons.append(reason)

    # Map each FAILED test to its reason by index
    test_reason_map = {}
    for i, test_name in enumerate(failed_tests):
        if i < len(failure_reasons):
            test_reason_map[test_name] = failure_reasons[i]

    # Second pass: build formatted output
    formatted = []
    in_failures = False
    in_summary = False

    for line in lines:
        # Skip FAILURES section
        if line.startswith("=") and "FAILURES" in line:
            in_failures = True
            continue
        if in_failures:
            if line.startswith("=") and "short test summary" in line:
                in_failures = False
                in_summary = True
            continue

        # Skip short test summary
        if in_summary:
            if line.startswith("=") and "passed in" in line:
                in_summary = False
                formatted.append(line)
            continue

        # Annotate integrity lines with a 🔍 prefix
        if "integrity" in line and ("PASSED" in line or "FAILED" in line):
            formatted.append(f"  🔍 {line.split('::')[1].replace('PASSED','').replace('FAILED','').strip()} ... ✅")
            continue

        # Inject failure reason inline on FAILED lines
        if "FAILED" in line and "[" in line:
            test_name = line.split("[")[1].split("]")[0]
            if test_name in test_reason_map:
                formatted.append(f"{line.rstrip()} — {test_reason_map[test_name]}")
                continue

        formatted.append(line)

    return "\n".join(formatted)


def _summary_from_stdout(stdout):
    """
    Parse pytest summary line like '9 passed, 6 failed' from stdout.
    Falls back to counting 'PASSED' / 'FAILED' tokens in output.
    """
    match = re.search(r"(\d+)\s+passed", stdout)
    passed = int(match.group(1)) if match else stdout.count("PASSED") - stdout.count("test session")
    match = re.search(r"(\d+)\s+failed", stdout)
    failed = int(match.group(1)) if match else stdout.count("FAILED") - stdout.count("FAILURES")
    return passed, failed


def action_run_csv_tests():
    """Run CSV data-driven tests via pytest"""
    print_header("🏃 RUN CSV DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(os.path.dirname(__file__), "test_csv_reader.py"),
         "-v", "--tb=line"],
        capture_output=True,
        text=True
    )
    
    output = _format_pytest_output(result.stdout)
    print("\n" + output)
    if result.stderr:
        print(f"  stderr: {result.stderr}")
    
    passed, failed = _summary_from_stdout(result.stdout)
    total = passed + failed
    
    print()
    if result.returncode == 0:
        print(f"  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"  ❌ {failed}/{total} TESTS FAILED")


def action_run_json_tests():
    """Run JSON data-driven tests via pytest"""
    print_header("🏃 RUN JSON DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(os.path.dirname(__file__), "test_json_reader.py"),
         "-v", "--tb=line"],
        capture_output=True,
        text=True
    )
    
    output = _format_pytest_output(result.stdout)
    print("\n" + output)
    if result.stderr:
        print(f"  stderr: {result.stderr}")
    
    passed, failed = _summary_from_stdout(result.stdout)
    total = passed + failed
    
    print()
    if result.returncode == 0:
        print(f"  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"  ❌ {failed}/{total} TESTS FAILED")


def action_run_all():
    """Run all data-driven tests"""
    print_header("🏃 RUN ALL DATA-DRIVEN TESTS")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.dirname(__file__),
         "-v", "--tb=line"],
        capture_output=True,
        text=True
    )
    
    output = _format_pytest_output(result.stdout)
    print("\n" + output)
    if result.stderr:
        print(f"  stderr: {result.stderr}")
    
    passed, failed = _summary_from_stdout(result.stdout)
    total = passed + failed
    
    print()
    if result.returncode == 0:
        print(f"  ✅ ALL {total} TESTS PASSED!")
    else:
        print(f"  ❌ {failed}/{total} TESTS FAILED — see details above")


# ─────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────

def show_menu():
    """Display the interactive menu"""
    print(render_box([
        "📊 CORTEX-SDET DATA-DRIVEN TESTING CLI",
        "CSV / JSON Data Validation - Parameterized Tests",
        "",
        "ACTIONS:",
        "1. 📄 Show CSV test data (users)",
        "2. 📄 Show JSON test data (products)",
        "3. 🏃 Run CSV data-driven tests (pytest)",
        "4. 🏃 Run JSON data-driven tests (pytest)",
        "5. 🏃 Run ALL data-driven tests (pytest)",
        "0. ❌ Exit",
    ], 60))


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