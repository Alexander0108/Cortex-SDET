"""
Data-Driven Tests from JSON

Reads product data from JSON files and runs parameterized pytest tests.
Demonstrates JSON data loading and business rule validation.

Requirements: pytest
Run: pytest data_driven_tests/test_json_reader.py -v
"""

import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PRODUCTS_JSON = os.path.join(DATA_DIR, "test_products.json")


def load_test_products():
    """
    Load product test data from JSON file.
    
    json.load() parses the JSON array into a Python list of dictionaries.
    Example: [{"id": 1, "name": "Laptop", "price": 999.99, ...}, ...]
    """
    with open(PRODUCTS_JSON, "r") as f:
        return json.load(f)


@pytest.mark.parametrize("product", load_test_products())
def test_product_validation(product):
    """
    Validate product data against business rules.
    
    This test runs ONCE for each product in the JSON array.
    
    Validation rules:
    1. Product name must not be empty
    2. Price must be greater than 0
    3. Stock must be 0 or greater
    4. Category must be a non-empty string
    """
    product_id = product.get("id", "N/A")
    name = product.get("name", "")
    price = product.get("price", 0)
    stock = product.get("stock", 0)
    category = product.get("category", "")
    
    errors = []
    
    # Rule 1: Name validation
    if not name or not name.strip():
        errors.append(f"Product #{product_id}: name is empty")
    
    # Rule: 2: Price validation
    if price <= 0:
        errors.append(f"Product '{name or product_id}': invalid price ${price} (must be > 0)")
    
    # Rule 3: Stock validation
    if stock < 0:
        errors.append(f"Product '{name}': negative stock ({stock})")
    
    # Rule 4: Category validation
    if not category:
        errors.append(f"Product '{name}': category is missing")
    
    assert len(errors) == 0, f"Validation failed: {'; '.join(errors)}"


def test_json_data_integrity():
    """
    Verify the JSON file structure itself.
    Ensures all required fields exist before running data tests.
    """
    with open(PRODUCTS_JSON, "r") as f:
        products = json.load(f)
    
    # Verify it's a list
    assert isinstance(products, list), "JSON root must be an array"
    
    # Verify data exists
    assert len(products) > 0, "JSON file contains no products"
    
    # Verify all products have required fields
    required_fields = {"id", "name", "price", "stock", "category"}
    for product in products:
        product_id = product.get("id", "N/A")
        missing = required_fields - set(product.keys())
        assert not missing, \
            f"Product #{product_id} missing fields: {missing}"
    
    print(f"  ✅ JSON integrity check passed: {len(products)} products, fields OK")