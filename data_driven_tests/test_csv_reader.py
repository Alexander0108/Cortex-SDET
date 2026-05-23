"""
Data-Driven Tests from CSV

Reads test scenarios from CSV files and runs parameterized pytest tests.
Demonstrates external data loading and validation.

Requirements: pytest
Run: pytest data_driven_tests/test_csv_reader.py -v
"""

import csv
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_CSV = os.path.join(DATA_DIR, "test_users.csv")


def load_test_users():
    """
    Load user test data from CSV file.
    
    csv.DictReader reads each row as a dictionary with column headers as keys.
    Example: {"email": "alice@test.com", "password": "pass12345", ...}
    """
    with open(USERS_CSV, "r") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("user", load_test_users())
def test_user_validation(user):
    """
    Validate user data against business rules.
    
    This test runs ONCE for each row in the CSV file.
    pytest.parametrize handles iteration automatically.
    
    Validation rules:
    1. Email must contain '@'
    2. Password must be at least 8 characters
    3. Role must be one of: admin, user, editor
    """
    email = user["email"]
    password = user["password"]
    role = user["role"]
    
    errors = []
    
    # Rule 1: Email format
    if "@" not in email:
        errors.append(f"Invalid email format: '{email}'")
    
    # Rule 2: Password length
    if len(password) < 8:
        errors.append(f"Weak password ({len(password)} chars, min 8): '{password}'")
    
    # Rule 3: Allowed roles
    allowed_roles = {"admin", "user", "editor"}
    if role not in allowed_roles:
        errors.append(f"Invalid role '{role}'. Allowed: {allowed_roles}")
    
    # If any validation failed — assert fails with all error details
    assert len(errors) == 0, f"User '{email}': {'; '.join(errors)}"


def test_csv_data_integrity():
    """
    Verify the CSV file structure itself.
    Ensures all required columns exist before running data tests.
    """
    with open(USERS_CSV, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Verify column headers
    expected_columns = {"email", "password", "role", "expected_status"}
    actual_columns = set(reader.fieldnames)
    missing = expected_columns - actual_columns
    assert not missing, f"CSV missing columns: {missing}"
    
    # Verify data exists
    assert len(rows) > 0, "CSV file is empty"
    
    # Verify no empty rows
    for i, row in enumerate(rows):
        for col in expected_columns:
            assert row[col].strip(), f"Row {i+1}: column '{col}' is empty"
    
    print(f"  ✅ CSV integrity check passed: {len(rows)} rows, {len(actual_columns)} columns")