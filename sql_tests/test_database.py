"""
SQL Database Testing Examples

Demonstrates SQL queries using SQLite:
- SELECT, JOIN, UPDATE, INSERT, DELETE
- GROUP BY, ORDER BY, Subqueries
- Data validation after CRUD operations

Requirements: sqlite3 (built-in Python), pytest
Run: pytest sql_tests/test_database.py -v
"""

import sqlite3
import json
import pytest
import os

# Use a temporary in-memory database for testing
# This ensures tests are isolated and repeatable


@pytest.fixture
def db():
    """
    Fixture: Creates an in-memory SQLite database with sample tables.
    Tables: users, orders, products, user_preferences
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ── Create tables ──────────────────────────────────────────────
    cursor.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            total REAL NOT NULL,
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            stock INTEGER DEFAULT 0
        );
        
        CREATE TABLE user_preferences (
            user_id INTEGER PRIMARY KEY,
            preferences TEXT NOT NULL,  -- JSON string
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    
    # ── Insert sample data ─────────────────────────────────────────
    cursor.executemany(
        "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
        [
            (1, "Alice Johnson", "alice@example.com", "active"),
            (2, "Bob Smith", "bob@example.com", "active"),
            (3, "Charlie Brown", "charlie@example.com", "inactive"),
            (4, "Diana Prince", "diana@example.com", "active"),
            (5, "Eve Wilson", "eve@example.com", "suspended"),
        ]
    )
    
    cursor.executemany(
        "INSERT INTO orders (id, user_id, product, quantity, total) VALUES (?, ?, ?, ?, ?)",
        [
            (1001, 1, "Laptop", 1, 999.99),
            (1002, 1, "Mouse", 2, 49.98),
            (1003, 2, "Keyboard", 1, 79.99),
            (1004, 2, "Monitor", 2, 599.98),
            (1005, 4, "Headphones", 1, 149.99),
            (1006, 4, "Webcam", 1, 89.99),
        ]
    )
    
    cursor.executemany(
        "INSERT INTO products (id, name, price, category, stock) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Laptop Pro", 1299.99, "Electronics", 15),
            (2, "Wireless Mouse", 29.99, "Accessories", 50),
            (3, "Mechanical Keyboard", 89.99, "Accessories", 30),
            (4, "27-inch Monitor", 349.99, "Electronics", 20),
            (5, "USB-C Hub", 45.99, "Accessories", 100),
        ]
    )
    
    cursor.executemany(
        "INSERT INTO user_preferences (user_id, preferences) VALUES (?, ?)",
        [
            (1, json.dumps({"theme": "dark", "notifications": True, "language": "en"})),
            (2, json.dumps({"theme": "light", "notifications": False, "language": "en"})),
            (4, json.dumps({"theme": "dark", "notifications": True, "language": "uk"})),
        ]
    )
    
    conn.commit()
    yield conn
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# 1. SELECT — Basic Queries
# ─────────────────────────────────────────────────────────────────────

def test_select_all_active_users(db):
    """SELECT with WHERE clause — fetch active users"""
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE status = 'active'")
    users = cursor.fetchall()
    
    assert len(users) == 3, f"Expected 3 active users, got {len(users)}"
    assert users[0]["name"] == "Alice Johnson"
    assert users[1]["name"] == "Bob Smith"
    assert users[2]["name"] == "Diana Prince"
    
    print(f"  ✅ Found {len(users)} active users:")
    for user in users:
        print(f"     ID={user['id']}, Name='{user['name']}', Email='{user['email']}'")


def test_select_single_user(db):
    """SELECT a single user by ID"""
    cursor = db.cursor()
    
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (1,))
    user = cursor.fetchone()
    
    assert user is not None, "User should exist"
    assert user["id"] == 1
    assert user["name"] == "Alice Johnson"
    assert user["email"] == "alice@example.com"
    
    print(f"  ✅ Found: ID={user['id']}, Name='{user['name']}', Email='{user['email']}'")


def test_select_with_multiple_conditions(db):
    """SELECT with multiple WHERE conditions"""
    cursor = db.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE status = 'active' AND email LIKE '%@example.com'"
    )
    users = cursor.fetchall()
    
    assert len(users) == 3, "Should find 3 active @example.com users"
    print(f"  ✅ Found {len(users)} users matching both conditions")


# ─────────────────────────────────────────────────────────────────────
# 2. JOIN — Table Relationships
# ─────────────────────────────────────────────────────────────────────

def test_inner_join_users_orders(db):
    """INNER JOIN — get users with their orders"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT users.name, orders.id AS order_id, orders.product, orders.total
        FROM users
        INNER JOIN orders ON users.id = orders.user_id
        ORDER BY users.name
    """)
    results = cursor.fetchall()
    
    assert len(results) == 6, f"Expected 6 order records, got {len(results)}"
    
    print(f"  ✅ INNER JOIN returned {len(results)} records:")
    for row in results:
        print(f"     {row['name']} — Order #{row['order_id']}: {row['product']} (${row['total']:.2f})")
    
    # Alice has 2 orders, Bob has 2, Diana has 2
    alice_orders = [r for r in results if r["name"] == "Alice Johnson"]
    bob_orders = [r for r in results if r["name"] == "Bob Smith"]
    diana_orders = [r for r in results if r["name"] == "Diana Prince"]
    
    assert len(alice_orders) == 2, "Alice should have 2 orders"
    assert len(bob_orders) == 2, "Bob should have 2 orders"
    assert len(diana_orders) == 2, "Diana should have 2 orders"


def test_left_join_users_orders(db):
    """LEFT JOIN — get all users, even those without orders"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT users.name, COUNT(orders.id) AS order_count
        FROM users
        LEFT JOIN orders ON users.id = orders.user_id
        GROUP BY users.id
        ORDER BY order_count DESC
    """)
    results = cursor.fetchall()
    
    print(f"  ✅ LEFT JOIN — users with their order counts:")
    for row in results:
        print(f"     {row['name']}: {row['order_count']} order(s)")
    
    # Charlie and Eve have 0 orders
    no_orders = [r for r in results if r["order_count"] == 0]
    assert len(no_orders) == 2, "Charlie and Eve should have 0 orders"
    assert no_orders[0]["name"] in ("Charlie Brown", "Eve Wilson")


# ─────────────────────────────────────────────────────────────────────
# 3. UPDATE — Modify Data
# ─────────────────────────────────────────────────────────────────────

def test_update_user_status(db):
    """UPDATE — change user status and verify"""
    cursor = db.cursor()
    
    # Update Charlie from 'inactive' to 'active'
    cursor.execute("UPDATE users SET status = 'active' WHERE id = 3")
    db.commit()
    
    assert cursor.rowcount == 1, "Should update exactly 1 row"
    
    # Verify
    cursor.execute("SELECT status FROM users WHERE id = 3")
    user = cursor.fetchone()
    assert user["status"] == "active", "Status should be updated to 'active'"
    
    print(f"  ✅ User #3 status updated to '{user['status']}'")
    
    # Restore for other tests
    cursor.execute("UPDATE users SET status = 'inactive' WHERE id = 3")
    db.commit()


def test_update_with_condition(db):
    """UPDATE with WHERE — update multiple rows"""
    cursor = db.cursor()
    
    # Give 10% discount on all orders above $100
    cursor.execute("""
        UPDATE orders 
        SET total = total * 0.9 
        WHERE total > 100
    """)
    db.commit()
    
    updated_count = cursor.rowcount
    assert updated_count == 3, "Should update 3 orders (Laptop $999.99, Monitor $599.98, Headphones $149.99)"
    
    # Verify
    cursor.execute("SELECT id, total FROM orders WHERE id IN (1001, 1004, 1005)")
    orders = cursor.fetchall()
    
    for order in orders:
        print(f"  ✅ Order #{order['id']}: new total = ${order['total']:.2f}")
    
    # Restore all modified orders
    cursor.execute("""
        UPDATE orders SET total = CASE id 
            WHEN 1001 THEN 999.99 
            WHEN 1004 THEN 599.98 
            WHEN 1005 THEN 149.99 
        END WHERE id IN (1001, 1004, 1005)
    """)
    db.commit()


# ─────────────────────────────────────────────────────────────────────
# 4. INSERT — Add New Data
# ─────────────────────────────────────────────────────────────────────

def test_insert_new_user(db):
    """INSERT — add a new user and verify"""
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
        (6, "Frank Castle", "frank@example.com", "active")
    )
    db.commit()
    
    # Verify insertion
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    count = cursor.fetchone()["count"]
    assert count == 6, f"Expected 6 users, got {count}"
    
    # Verify data
    cursor.execute("SELECT * FROM users WHERE id = 6")
    user = cursor.fetchone()
    assert user["name"] == "Frank Castle"
    assert user["status"] == "active"
    
    print(f"  ✅ New user created: ID={user['id']}, Name='{user['name']}', Status='{user['status']}'")
    
    # Cleanup
    cursor.execute("DELETE FROM users WHERE id = 6")
    db.commit()


def test_insert_duplicate_email_fails(db):
    """INSERT with duplicate email — should fail (UNIQUE constraint)"""
    cursor = db.cursor()
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
            (7, "Ghost User", "alice@example.com", "active")  # Duplicate email!
        )
    
    print(f"  ✅ UNIQUE constraint correctly prevents duplicate emails")


# ─────────────────────────────────────────────────────────────────────
# 5. DELETE — Remove Data
# ─────────────────────────────────────────────────────────────────────

def test_delete_user_and_verify(db):
    """DELETE — remove a user and verify with SELECT"""
    cursor = db.cursor()
    
    # Add a temporary user
    cursor.execute(
        "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
        (99, "Temp User", "temp@example.com", "active")
    )
    db.commit()
    
    # Verify it exists
    cursor.execute("SELECT id FROM users WHERE id = 99")
    assert cursor.fetchone() is not None, "Temp user should exist"
    
    # Delete it
    cursor.execute("DELETE FROM users WHERE id = 99")
    db.commit()
    
    # Verify it's gone
    cursor.execute("SELECT id FROM users WHERE id = 99")
    assert cursor.fetchone() is None, "Temp user should be deleted"
    
    print(f"  ✅ User #99 deleted and confirmed gone")


# ─────────────────────────────────────────────────────────────────────
# 6. GROUP BY / ORDER BY — Aggregation & Sorting
# ─────────────────────────────────────────────────────────────────────

def test_group_by_user_spending(db):
    """GROUP BY with SUM — total spending per user"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT users.name, SUM(orders.total) AS total_spent
        FROM users
        JOIN orders ON users.id = orders.user_id
        GROUP BY users.id
        ORDER BY total_spent DESC
    """)
    results = cursor.fetchall()
    
    print(f"  ✅ Top spenders:")
    for row in results:
        print(f"     {row['name']}: ${row['total_spent']:.2f}")
    
    assert len(results) == 3, "Should have 3 users with orders"
    assert results[0]["total_spent"] >= results[1]["total_spent"], \
        "Results should be sorted DESC"


def test_order_by_multiple_columns(db):
    """ORDER BY multiple columns"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT name, status, email FROM users
        ORDER BY status ASC, name ASC
    """)
    results = cursor.fetchall()
    
    print(f"  ✅ Users sorted by status, then name:")
    for row in results:
        print(f"     {row['name']} ({row['status']})")
    
    # First should be 'active' users, then 'inactive', then 'suspended'
    assert results[0]["status"] == "active"
    assert results[-1]["status"] == "suspended"


# ─────────────────────────────────────────────────────────────────────
# 7. Subqueries
# ─────────────────────────────────────────────────────────────────────

def test_subquery_in_where(db):
    """Subquery — users who have placed orders"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT name, email FROM users
        WHERE id IN (SELECT DISTINCT user_id FROM orders)
        ORDER BY name
    """)
    results = cursor.fetchall()
    
    assert len(results) == 3, "Should be 3 users with orders"
    
    print(f"  ✅ Users with orders ({len(results)}):")
    for row in results:
        print(f"     {row['name']} — {row['email']}")


def test_subquery_in_select(db):
    """Subquery in SELECT — count orders per user alongside user data"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            u.name,
            u.status,
            (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count
        FROM users u
        ORDER BY order_count DESC
    """)
    results = cursor.fetchall()
    
    print(f"  ✅ Users with order counts (subquery):")
    for row in results:
        print(f"     {row['name']}: {row['order_count']} order(s), status='{row['status']}'")
    
    assert results[0]["order_count"] >= 1, "First user should have orders"
    assert results[-1]["order_count"] == 0, "Last user should have 0 orders"


# ─────────────────────────────────────────────────────────────────────
# 8. JSON Data in Database
# ─────────────────────────────────────────────────────────────────────

def test_json_data_in_db(db):
    """SELECT + JSON parse — verify data in JSON format"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT users.name, user_preferences.preferences
        FROM users
        JOIN user_preferences ON users.id = user_preferences.user_id
    """)
    results = cursor.fetchall()
    
    print(f"  ✅ Users with JSON preferences:")
    for row in results:
        prefs = json.loads(row["preferences"])
        print(f"     {row['name']}: theme={prefs['theme']}, "
              f"notifications={prefs['notifications']}, lang={prefs['language']}")
    
    # Validate JSON structure
    for row in results:
        prefs = json.loads(row["preferences"])
        assert "theme" in prefs, "Should have theme"
        assert "notifications" in prefs, "Should have notifications"
        assert "language" in prefs, "Should have language"
    
    print(f"  ✅ All preference JSON structures validated")


def test_update_json_field(db):
    """UPDATE JSON data in database"""
    cursor = db.cursor()
    
    # Update Alice's preferences
    new_prefs = json.dumps({"theme": "light", "notifications": False, "language": "en"})
    cursor.execute(
        "UPDATE user_preferences SET preferences = ? WHERE user_id = 1",
        (new_prefs,)
    )
    db.commit()
    
    # Verify
    cursor.execute("SELECT preferences FROM user_preferences WHERE user_id = 1")
    updated = json.loads(cursor.fetchone()["preferences"])
    assert updated["theme"] == "light", "Theme should be updated to 'light'"
    assert updated["notifications"] is False, "Notifications should be False"
    
    print(f"  ✅ Updated preferences: theme={updated['theme']}")
    
    # Restore
    original_prefs = json.dumps({"theme": "dark", "notifications": True, "language": "en"})
    cursor.execute(
        "UPDATE user_preferences SET preferences = ? WHERE user_id = 1",
        (original_prefs,)
    )
    db.commit()