"""
Cortex-SDET SQL Testing CLI

Interactive CLI for demonstrating SQL database testing with SQLite.
Allows running individual SQL queries with visual feedback.

Run: python3 sql_tests/sql_cli.py
"""

import sqlite3
import json
import os
import sys

# Allow importing the shared cli_utils module from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_utils import render_box


def create_database():
    """Create an in-memory SQLite database with sample data"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
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
            preferences TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        INSERT INTO users (id, name, email, status) VALUES
            (1, 'Alice Johnson', 'alice@example.com', 'active'),
            (2, 'Bob Smith', 'bob@example.com', 'active'),
            (3, 'Charlie Brown', 'charlie@example.com', 'inactive'),
            (4, 'Diana Prince', 'diana@example.com', 'active'),
            (5, 'Eve Wilson', 'eve@example.com', 'suspended');
        
        INSERT INTO orders (id, user_id, product, quantity, total) VALUES
            (1001, 1, 'Laptop', 1, 999.99),
            (1002, 1, 'Mouse', 2, 49.98),
            (1003, 2, 'Keyboard', 1, 79.99),
            (1004, 2, 'Monitor', 2, 599.98),
            (1005, 4, 'Headphones', 1, 149.99),
            (1006, 4, 'Webcam', 1, 89.99);
        
        INSERT INTO products (id, name, price, category, stock) VALUES
            (1, 'Laptop Pro', 1299.99, 'Electronics', 15),
            (2, 'Wireless Mouse', 29.99, 'Accessories', 50),
            (3, 'Mechanical Keyboard', 89.99, 'Accessories', 30),
            (4, '27-inch Monitor', 349.99, 'Electronics', 20),
            (5, 'USB-C Hub', 45.99, 'Accessories', 100);
        
        INSERT INTO user_preferences (user_id, preferences) VALUES
            (1, '{"theme": "dark", "notifications": true, "language": "en"}'),
            (2, '{"theme": "light", "notifications": false, "language": "en"}'),
            (4, '{"theme": "dark", "notifications": true, "language": "uk"}');
    """)
    
    conn.commit()
    return conn


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def print_table(cursor, results):
    """Print query results in a formatted table"""
    if not results:
        print("  (no results)")
        return
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Calculate column widths
    col_widths = {col: len(str(col)) for col in columns}
    for row in results:
        for col in columns:
            val = str(row[col]) if row[col] is not None else "NULL"
            col_widths[col] = max(col_widths[col], len(val))
    
    # Print header
    header = "  | " + " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "  |-" + "-+-".join("-" * col_widths[col] for col in columns) + "-|"
    
    print(f"\n{separator}")
    print(header)
    print(separator.replace("-", "="))
    
    # Print rows
    for row in results:
        vals = []
        for col in columns:
            val = str(row[col]) if row[col] is not None else "NULL"
            vals.append(val.ljust(col_widths[col]))
        print("  | " + " | ".join(vals) + " |")
    
    print(separator)
    print(f"\n  📊 {len(results)} row(s) returned")


# ─────────────────────────────────────────────────────────────────────
# Menu Actions
# ─────────────────────────────────────────────────────────────────────

def action_select_all(conn):
    """SELECT * FROM users — get all data"""
    print_header("📊 SELECT ALL USERS")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    
    print(f"\n  [*] SQL: SELECT * FROM users")
    print_table(cursor, results)


def action_select_where(conn):
    """SELECT with WHERE — filter data"""
    print_header("🔍 SELECT WITH FILTER")
    
    status_options = ["active", "inactive", "suspended"]
    print("\n  Status options: " + ", ".join(f"'{s}'" for s in status_options))
    status = input("  Filter by status [active]: ").strip() or "active"
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, status FROM users WHERE status = ?", (status,))
    results = cursor.fetchall()
    
    print(f"\n  [*] SQL: SELECT id, name, email, status FROM users WHERE status = '{status}'")
    print_table(cursor, results)


def action_join(conn):
    """JOIN — combine tables"""
    print_header("🔗 INNER JOIN USERS & ORDERS")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.name, orders.id AS order_id, orders.product, 
               orders.quantity, orders.total
        FROM users
        INNER JOIN orders ON users.id = orders.user_id
        ORDER BY users.name, orders.id
    """)
    results = cursor.fetchall()
    
    print("\n  [*] SQL: SELECT users.name, orders.product, orders.total")
    print("           FROM users")
    print("           INNER JOIN orders ON users.id = orders.user_id")
    print_table(cursor, results)


def action_left_join(conn):
    """LEFT JOIN — show all users even without orders"""
    print_header("🔗 LEFT JOIN USERS & ORDERS")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.id, users.name, users.status, 
               COUNT(orders.id) AS order_count,
               COALESCE(SUM(orders.total), 0) AS total_spent
        FROM users
        LEFT JOIN orders ON users.id = orders.user_id
        GROUP BY users.id
        ORDER BY total_spent DESC
    """)
    results = cursor.fetchall()
    
    print("\n  [*] SQL: SELECT users.name, COUNT(orders.id), SUM(orders.total)")
    print("           FROM users")
    print("           LEFT JOIN orders ON users.id = orders.user_id")
    print("           GROUP BY users.id")
    print_table(cursor, results)


def action_update(conn):
    """UPDATE — modify data"""
    print_header("✏️ UPDATE USER STATUS")
    
    cursor = conn.cursor()
    
    # Show current state
    cursor.execute("SELECT id, name, status FROM users")
    current = cursor.fetchall()
    print("\n  Current users:")
    for u in current:
        print(f"    ID={u['id']}: {u['name']} ({u['status']})")
    
    user_id = input("\n  Enter user ID to update [3]: ").strip() or "3"
    new_status = input("  New status (active/inactive/suspended) [active]: ").strip() or "active"
    
    # Execute update
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, int(user_id)))
    conn.commit()
    
    if cursor.rowcount > 0:
        print(f"\n  ✅ Updated {cursor.rowcount} row(s)")
        
        # Show updated user
        cursor.execute("SELECT id, name, status FROM users WHERE id = ?", (int(user_id),))
        updated = cursor.fetchone()
        print(f"  ✅ ID={updated['id']}: {updated['name']} → '{updated['status']}'")
    else:
        print("\n  ⚠️  No user found with that ID")
    
    # Restore
    cursor.execute("UPDATE users SET status = 'inactive' WHERE id = 3")
    conn.commit()


def action_insert(conn):
    """INSERT — create new record"""
    print_header("➕ INSERT NEW USER")
    
    name = input("  Name [Test User]: ").strip() or "Test User"
    email = input("  Email [test@example.com]: ").strip() or "test@example.com"
    status = input("  Status (active/inactive) [active]: ").strip() or "active"
    
    # Get next available ID
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) + 1 AS next_id FROM users")
    next_id = cursor.fetchone()["next_id"] or 1
    
    cursor.execute(
        "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
        (next_id, name, email, status)
    )
    conn.commit()
    
    print(f"\n  ✅ User created: ID={next_id}, Name='{name}'")
    
    # Verify
    cursor.execute("SELECT * FROM users WHERE id = ?", (next_id,))
    print_table(cursor, cursor.fetchall())
    
    # Cleanup
    cursor.execute("DELETE FROM users WHERE id = ?", (next_id,))
    conn.commit()
    print(f"  🗑️  Cleanup: temporary user deleted")


def action_delete(conn):
    """DELETE — remove record"""
    print_header("🗑️ DELETE USER")
    
    cursor = conn.cursor()
    
    # Create a temporary user
    cursor.execute(
        "INSERT INTO users (id, name, email, status) VALUES (99, 'TempUser', 'temp99@test.com', 'active')"
    )
    conn.commit()
    
    print("\n  Temporary user created (ID=99, Name='TempUser')")
    
    confirm = input("  Delete this user? (y/n): ").strip().lower()
    if confirm != "y":
        print("  ⏭️  Skipping...")
        cursor.execute("DELETE FROM users WHERE id = 99")
        conn.commit()
        return
    
    cursor.execute("DELETE FROM users WHERE id = 99")
    conn.commit()
    
    # Verify deletion
    cursor.execute("SELECT id FROM users WHERE id = 99")
    deleted = cursor.fetchone()
    
    if deleted is None:
        print("\n  ✅ User deleted and confirmed gone")
    else:
        print("\n  ⚠️  User still exists")


def action_group_by(conn):
    """GROUP BY — aggregation"""
    print_header("📈 GROUP BY — TOP SPENDERS")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.name, COUNT(orders.id) AS orders_count, 
               SUM(orders.total) AS total_spent
        FROM users
        JOIN orders ON users.id = orders.user_id
        GROUP BY users.id
        ORDER BY total_spent DESC
    """)
    results = cursor.fetchall()
    
    print("\n  [*] SQL: SELECT users.name, COUNT(orders.id), SUM(orders.total)")
    print("           FROM users JOIN orders ON users.id = orders.user_id")
    print("           GROUP BY users.id ORDER BY total_spent DESC")
    print_table(cursor, results)


def action_json_data(conn):
    """Show JSON data in database"""
    print_header("📋 JSON DATA IN DATABASE")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.name, user_preferences.preferences
        FROM users
        JOIN user_preferences ON users.id = user_preferences.user_id
    """)
    results = cursor.fetchall()
    
    print("\n  [*] SQL: SELECT users.name, user_preferences.preferences")
    print("           FROM users JOIN user_preferences")
    print()
    
    for row in results:
        prefs = json.loads(row["preferences"])
        print(f"  👤 {row['name']}:")
        print(f"     ├─ Theme: {prefs['theme']}")
        print(f"     ├─ Notifications: {prefs['notifications']}")
        print(f"     └─ Language: {prefs['language']}")
        print()


def action_custom_query(conn):
    """Run a custom SQL query"""
    print_header("⚡ CUSTOM SQL QUERY")
    print("\n  Enter any SQL query (e.g., SELECT * FROM products)")
    print("  Tables: users, orders, products, user_preferences")
    print("  To exit, type 'exit' or 'quit'")
    
    query = input("\n  SQL > ").strip()
    
    if query.lower() in ("exit", "quit"):
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("WITH"):
            results = cursor.fetchall()
            print_table(cursor, results)
        else:
            conn.commit()
            print(f"\n  ✅ Query executed. {cursor.rowcount} row(s) affected.")
    except Exception as e:
        print(f"\n  ❌ Error: {e}")


def action_run_all_sql(conn):
    """Run all SQL tests"""
    print_header("🏃 RUN ALL SQL TESTS")
    import subprocess
    
    print("\n  [*] Running: pytest sql_tests/ -v --tb=short\n")
    result = subprocess.run(
        ["pytest", "sql_tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"  stderr: {result.stderr[:500]}")
    
    if result.returncode == 0:
        print("\n  ✅ ALL SQL TESTS PASSED!")
    else:
        print(f"\n  ❌ Some tests failed (exit code {result.returncode})")


# ─────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────

def show_menu():
    """Display the interactive menu"""
    print(render_box([
        "📁 CORTEX-SDET SQL TESTING CLI",
        "Database Testing - SQLite Demo",
        "",
        "SELECT QUERIES:",
        "1. 📊 SELECT - Get all users",
        "2. 🔍 SELECT - Filter users by status",
        "",
        "JOINS:",
        "3. 🔗 INNER JOIN - Users with their orders",
        "4. 🔗 LEFT JOIN - All users (even without orders)",
        "",
        "DATA MODIFICATION:",
        "5. 🔧 UPDATE - Change user status",
        "6. 💾 INSERT - Add a new user",
        "7. ⛔ DELETE - Remove a user",
        "",
        "AGGREGATION & SPECIAL:",
        "8. 📈 GROUP BY - Top spenders",
        "9. 📋 JSON Data - Preferences in database",
        "10. 📝 Custom SQL - Run any query",
        "",
        "11. 🏃 Run All SQL Tests (pytest)",
        "0. ❌ Exit",
    ], 60))


def main():
    """Main CLI loop"""
    conn = create_database()
    print("\n  ✅ Database initialized with sample data (5 users, 6 orders, 5 products)")
    
    while True:
        show_menu()
        choice = input("\n  👉 Select action (0-11): ").strip()
        
        if choice == "1":
            action_select_all(conn)
        elif choice == "2":
            action_select_where(conn)
        elif choice == "3":
            action_join(conn)
        elif choice == "4":
            action_left_join(conn)
        elif choice == "5":
            action_update(conn)
        elif choice == "6":
            action_insert(conn)
        elif choice == "7":
            action_delete(conn)
        elif choice == "8":
            action_group_by(conn)
        elif choice == "9":
            action_json_data(conn)
        elif choice == "10":
            action_custom_query(conn)
        elif choice == "11":
            action_run_all_sql(conn)
        elif choice == "0":
            print("\n  👋 Exiting...")
            break
        else:
            print("\n  ⚠️  Invalid choice. Please enter 0-11.")
        
        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()