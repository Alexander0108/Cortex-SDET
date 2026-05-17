"""
Data Format Testing Examples

Demonstrates testing of various data formats: JSON, CSV, XML.
Simulates real-world scenarios where data is serialized/deserialized.

Requirements: pytest, csv (built-in), json (built-in), xml (built-in)
Run: pytest sql_tests/test_data_formats.py -v
"""

import json
import csv
import xml.etree.ElementTree as ET
import io
import pytest


# ─────────────────────────────────────────────────────────────────────
# 1. JSON Data Testing
# ─────────────────────────────────────────────────────────────────────

class TestJSONData:
    """Tests for JSON data structures and validation"""

    def test_parse_valid_json(self):
        """Parse a valid JSON string and verify its structure"""
        json_data = """
        {
            "order": {
                "id": 1001,
                "customer": "Alice Johnson",
                "items": [
                    {"product": "Laptop", "quantity": 1, "price": 999.99},
                    {"product": "Mouse", "quantity": 2, "price": 24.99}
                ],
                "total": 1049.97,
                "shipping": {
                    "address": "123 Main St",
                    "city": "New York",
                    "zip": "10001"
                }
            }
        }
        """
        
        parsed = json.loads(json_data)
        
        # Validate structure
        order = parsed["order"]
        assert order["id"] == 1001
        assert order["customer"] == "Alice Johnson"
        assert len(order["items"]) == 2
        assert order["total"] == 1049.97
        
        # Validate nested objects
        assert order["shipping"]["city"] == "New York"
        
        print(f"  ✅ JSON parsed: Order #{order['id']} — {order['customer']}")
        print(f"  ✅ Items: {len(order['items'])}, Total: ${order['total']:.2f}")

    def test_json_array_validation(self):
        """Validate an array of JSON objects"""
        users_data = """
        [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
            {"id": 3, "name": "Charlie", "role": "editor"}
        ]
        """
        
        users = json.loads(users_data)
        
        # Validate each user
        for user in users:
            assert "id" in user, "Each user must have 'id'"
            assert "name" in user, "Each user must have 'name'"
            assert "role" in user, "Each user must have 'role'"
            assert isinstance(user["id"], int), "ID must be integer"
            assert isinstance(user["name"], str), "Name must be string"
        
        # Verify specific values
        assert users[0]["name"] == "Alice"
        assert users[2]["role"] == "editor"
        
        print(f"  ✅ JSON array validated: {len(users)} users")

    def test_json_nested_arrays(self):
        """Validate deeply nested JSON structures"""
        data = {
            "company": "TechCorp",
            "departments": [
                {
                    "name": "Engineering",
                    "employees": [
                        {"name": "Alice", "skills": ["Python", "SQL", "API"]},
                        {"name": "Bob", "skills": ["Java", "SQL"]}
                    ]
                },
                {
                    "name": "QA",
                    "employees": [
                        {"name": "Charlie", "skills": ["Selenium", "Python", "Postman"]}
                    ]
                }
            ]
        }
        
        # Validate nesting
        assert data["company"] == "TechCorp"
        assert len(data["departments"]) == 2
        
        # Count total employees
        total_employees = sum(
            len(dept["employees"])
            for dept in data["departments"]
        )
        assert total_employees == 3
        
        # Check skills
        qa_skills = data["departments"][1]["employees"][0]["skills"]
        assert "Postman" in qa_skills
        assert "Python" in qa_skills
        
        print(f"  ✅ Nested JSON: {len(data['departments'])} departments, {total_employees} employees")

    def test_invalid_json_raises_error(self):
        """Attempt to parse invalid JSON — should raise exception"""
        invalid_json = '{"name": "Alice", "age": }'  # Malformed
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
        
        print(f"  ✅ Invalid JSON correctly raises JSONDecodeError")


# ─────────────────────────────────────────────────────────────────────
# 2. CSV Data Testing
# ─────────────────────────────────────────────────────────────────────

class TestCSVData:
    """Tests for CSV data parsing and validation"""

    def test_parse_csv_with_headers(self):
        """Parse a CSV string with headers"""
        csv_data = """name,email,role,active
Alice Johnson,alice@example.com,Admin,true
Bob Smith,bob@example.com,User,true
Charlie Brown,charlie@example.com,User,false
Diana Prince,diana@example.com,Editor,true
"""
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        # Validate number of rows
        assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"
        
        # Validate structure
        for row in rows:
            assert "name" in row, "Each row must have 'name'"
            assert "email" in row, "Each row must have 'email'"
            assert "role" in row, "Each row must have 'role'"
            assert "active" in row, "Each row must have 'active'"
        
        # Validate specific values
        assert rows[0]["name"] == "Alice Johnson"
        assert rows[0]["role"] == "Admin"
        
        # Count active users
        active_users = [r for r in rows if r["active"] == "true"]
        assert len(active_users) == 3, f"Expected 3 active users, got {len(active_users)}"
        
        print(f"  ✅ CSV parsed: {len(rows)} rows, {len(active_users)} active users")

    def test_csv_without_headers(self):
        """Parse CSV without headers using fieldnames"""
        csv_data = """1,Alice,alice@example.com
2,Bob,bob@example.com
3,Charlie,charlie@example.com
"""
        fieldnames = ["id", "name", "email"]
        reader = csv.DictReader(io.StringIO(csv_data), fieldnames=fieldnames)
        rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[1]["email"] == "bob@example.com"
        assert rows[2]["id"] == "3"
        
        print(f"  ✅ CSV without headers: {len(rows)} rows with custom fieldnames")

    def test_csv_validation(self):
        """Validate CSV data types and constraints"""
        csv_data = """id,product,quantity,price
101,Laptop,1,999.99
102,Mouse,2,24.99
103,Keyboard,-1,79.99
"""
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        # Convert and validate types
        for row in rows:
            row["id"] = int(row["id"])
            row["quantity"] = int(row["quantity"])
            row["price"] = float(row["price"])
        
        # Validate quantity > 0
        negative_quantity = [r for r in rows if r["quantity"] < 0]
        assert len(negative_quantity) == 1, "Should detect 1 item with negative quantity"
        
        print(f"  ✅ CSV validation: {len(rows)} rows processed")
        print(f"  ⚠️  Found {len(negative_quantity)} item(s) with negative quantity")

    def test_empty_csv(self):
        """Handle empty CSV gracefully"""
        csv_data = "header1,header2,header3\n"
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        assert len(rows) == 0, "Empty CSV should have 0 data rows"
        print(f"  ✅ Empty CSV correctly parsed: 0 data rows")


# ─────────────────────────────────────────────────────────────────────
# 3. XML Data Testing
# ─────────────────────────────────────────────────────────────────────

class TestXMLData:
    """Tests for XML data parsing and validation"""

    def test_parse_valid_xml(self):
        """Parse a valid XML string and verify structure"""
        xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<order>
    <id>1001</id>
    <customer>Alice Johnson</customer>
    <items>
        <item>
            <product>Laptop</product>
            <quantity>1</quantity>
            <price>999.99</price>
        </item>
        <item>
            <product>Mouse</product>
            <quantity>2</quantity>
            <price>24.99</price>
        </item>
    </items>
    <total>1049.97</total>
</order>
"""
        root = ET.fromstring(xml_data)
        
        # Validate root
        assert root.tag == "order"
        
        # Validate fields
        assert root.find("id").text == "1001"
        assert root.find("customer").text == "Alice Johnson"
        assert root.find("total").text == "1049.97"
        
        # Validate items
        items = root.findall("items/item")
        assert len(items) == 2, f"Expected 2 items, got {len(items)}"
        assert items[0].find("product").text == "Laptop"
        assert items[1].find("product").text == "Mouse"
        
        print(f"  ✅ XML parsed: Order #{root.find('id').text} — {root.find('customer').text}")
        print(f"  ✅ Items: {len(items)}")

    def test_xml_attribute_parsing(self):
        """Parse XML with attributes"""
        xml_data = """<?xml version="1.0"?>
<users>
    <user id="1" role="admin">
        <name>Alice</name>
        <email>alice@example.com</email>
    </user>
    <user id="2" role="user">
        <name>Bob</name>
        <email>bob@example.com</email>
    </user>
</users>
"""
        root = ET.fromstring(xml_data)
        users = root.findall("user")
        
        assert len(users) == 2
        
        # Check attributes
        assert users[0].get("id") == "1"
        assert users[0].get("role") == "admin"
        assert users[1].get("id") == "2"
        assert users[1].get("role") == "user"
        
        # Check child elements
        assert users[0].find("name").text == "Alice"
        assert users[1].find("email").text == "bob@example.com"
        
        print(f"  ✅ XML attributes parsed: {len(users)} users")

    def test_invalid_xml_raises_error(self):
        """Attempt to parse invalid XML — should raise exception"""
        invalid_xml = "<root><element>Unclosed>"
        
        with pytest.raises(ET.ParseError):
            ET.fromstring(invalid_xml)
        
        print(f"  ✅ Invalid XML correctly raises ParseError")


# ─────────────────────────────────────────────────────────────────────
# 4. Cross-Format Testing (JSON + CSV)
# ─────────────────────────────────────────────────────────────────────

class TestCrossFormat:
    """Tests that convert between data formats"""

    def test_json_to_csv_conversion(self):
        """Convert JSON data to CSV format and verify"""
        users = [
            {"id": 1, "name": "Alice", "score": 95},
            {"id": 2, "name": "Bob", "score": 87},
            {"id": 3, "name": "Charlie", "score": 92}
        ]
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "name", "score"])
        writer.writeheader()
        writer.writerows(users)
        
        csv_result = output.getvalue()
        
        # Verify CSV content
        reader = csv.DictReader(io.StringIO(csv_result))
        rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[1]["score"] == "87"
        
        # Verify scores > 90
        high_scorers = [r for r in rows if int(r["score"]) > 90]
        assert len(high_scorers) == 2, "Alice and Charlie have scores > 90"
        
        print(f"  ✅ JSON → CSV conversion: {len(rows)} rows")
        print(f"  ✅ High scorers (>90): {[r['name'] for r in high_scorers]}")

    def test_csv_with_nested_data_limitation(self):
        """Demonstrate CSV limitation with nested data"""
        # CSV cannot represent nested structures; JSON is better
        csv_data = "id,name,preferences\n1,Alice,\"{'theme': 'dark'}\"\n"
        reader = csv.DictReader(io.StringIO(csv_data))
        row = list(reader)[0]
        
        preferences = row["preferences"]
        
        # CSV stores nested data as string — need JSON for proper structure
        print(f"  ✅ CSV stores nested data as string: {preferences}")
        print(f"  ℹ️  Note: JSON is better for nested structures")