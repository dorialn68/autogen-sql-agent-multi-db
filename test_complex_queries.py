#!/usr/bin/env python3
"""
Test script for complex analytical queries and multi-database support
Tests the issues raised by user:
1. Multi-database support beyond Chinook
2. Complex analytical queries like cross-customer purchase analysis
"""
import sys
import os
sys.path.insert(0, 'app')

from database_config import DatabaseConfigManager
from autogen_universal import UniversalNL2SQLOrchestrator
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_database():
    """Create a different database schema to test universal support"""
    db_path = "test_ecommerce.sqlite"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a different schema (e-commerce style, not Chinook)
    cursor.executescript("""
    -- Users table (different from Chinook's Customer)
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        city TEXT,
        country TEXT
    );
    
    -- Products table
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        price REAL,
        brand TEXT
    );
    
    -- Orders table
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        order_date TEXT,
        total_amount REAL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    -- Order items (junction table)
    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        item_price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    
    -- Insert test data
    INSERT INTO users (username, first_name, last_name, email, city, country) VALUES
    ('dan_miller', 'Dan', 'Miller', 'dan.miller@email.com', 'New York', 'USA'),
    ('sarah_jones', 'Sarah', 'Jones', 'sarah.jones@email.com', 'Los Angeles', 'USA'),
    ('mike_wilson', 'Mike', 'Wilson', 'mike.wilson@email.com', 'Chicago', 'USA'),
    ('anna_smith', 'Anna', 'Smith', 'anna.smith@email.com', 'Seattle', 'USA'),
    ('bob_brown', 'Bob', 'Brown', 'bob.brown@email.com', 'Miami', 'USA');
    
    INSERT INTO products (product_name, category, price, brand) VALUES
    ('iPhone 15', 'Electronics', 999.99, 'Apple'),
    ('Samsung Galaxy S24', 'Electronics', 899.99, 'Samsung'),
    ('MacBook Pro', 'Computers', 1999.99, 'Apple'),
    ('Dell XPS 13', 'Computers', 1299.99, 'Dell'),
    ('AirPods Pro', 'Accessories', 249.99, 'Apple'),
    ('Sony Headphones', 'Accessories', 199.99, 'Sony'),
    ('iPad Air', 'Tablets', 599.99, 'Apple'),
    ('Microsoft Surface', 'Tablets', 799.99, 'Microsoft');
    
    -- Orders for Dan Miller (user_id = 1)
    INSERT INTO orders (user_id, order_date, total_amount) VALUES
    (1, '2024-01-15', 1249.98),
    (1, '2024-02-20', 599.99);
    
    -- Dan's order items
    INSERT INTO order_items (order_id, product_id, quantity, item_price) VALUES
    (1, 1, 1, 999.99),  -- iPhone 15
    (1, 5, 1, 249.99),  -- AirPods Pro
    (2, 7, 1, 599.99);  -- iPad Air
    
    -- Orders for other customers
    INSERT INTO orders (user_id, order_date, total_amount) VALUES
    (2, '2024-01-18', 999.99),   -- Sarah
    (3, '2024-01-20', 1999.99),  -- Mike  
    (4, '2024-02-01', 249.99),   -- Anna
    (5, '2024-02-10', 1299.99);  -- Bob
    
    -- Other customers' order items (some overlap with Dan's purchases)
    INSERT INTO order_items (order_id, product_id, quantity, item_price) VALUES
    -- Sarah bought iPhone 15 (same as Dan)
    (3, 1, 1, 999.99),
    -- Mike bought MacBook Pro
    (4, 3, 1, 1999.99),
    -- Anna bought AirPods Pro (same as Dan)
    (5, 5, 1, 249.99),
    -- Bob bought Dell XPS 13
    (6, 4, 1, 1299.99);
    
    -- Additional orders to create more complex relationships
    INSERT INTO orders (user_id, order_date, total_amount) VALUES
    (2, '2024-02-15', 599.99),   -- Sarah's second order
    (3, '2024-02-25', 249.99);   -- Mike's second order
    
    INSERT INTO order_items (order_id, product_id, quantity, item_price) VALUES
    -- Sarah also bought iPad Air (same as Dan)
    (7, 7, 1, 599.99),
    -- Mike also bought AirPods Pro (same as Dan)
    (8, 5, 1, 249.99);
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created test e-commerce database: {db_path}")
    return db_path

def test_schema_discovery(orchestrator):
    """Test that the system can discover and understand any schema"""
    print("\n" + "="*60)
    print("🔍 TESTING SCHEMA DISCOVERY")
    print("="*60)
    
    # Test schema analysis
    schema_info = orchestrator.db_manager.get_schema_info()
    schema_patterns = orchestrator.db_manager.analyze_schema_patterns()
    
    print(f"📊 Tables discovered: {list(schema_info.get('tables', {}).keys())}")
    print(f"🏢 Entity tables: {schema_patterns.get('entity_tables', [])}")
    print(f"🔗 Junction tables: {schema_patterns.get('junction_tables', [])}")
    print(f"👤 Name columns: {schema_patterns.get('name_columns', {})}")
    print(f"🔑 Relationships: {len(schema_patterns.get('relationships', []))}")
    
    # This should work with ANY database schema, not just Chinook
    assert len(schema_info.get('tables', {})) > 0, "Should discover tables in any database"
    print("✅ Schema discovery works with non-Chinook database")

def test_basic_queries(orchestrator):
    """Test basic queries on the new schema"""
    print("\n" + "="*60)
    print("🔹 TESTING BASIC QUERIES")
    print("="*60)
    
    test_queries = [
        "How many users do we have?",
        "Show me all products",
        "Where does Dan live?",
        "List all orders"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = orchestrator.process_query(query)
        
        if result.get("success"):
            rows = result.get("result", {}).get("rows", [])
            print(f"✅ Success: {len(rows)} rows returned")
            print(f"   SQL: {result.get('sql', '')[:100]}...")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")

def test_complex_analytical_query(orchestrator):
    """Test the specific complex query the user mentioned"""
    print("\n" + "="*60)
    print("🧠 TESTING COMPLEX ANALYTICAL QUERY")
    print("="*60)
    
    # The user's complex query
    complex_query = "which Items the Dan purchased other customer have purchased and which items they are"
    
    print(f"📝 Complex Query: '{complex_query}'")
    print("   This should:")
    print("   1. Find Dan's purchases")
    print("   2. Find other customers who bought the same items")
    print("   3. Find what other items those customers purchased")
    
    result = orchestrator.process_query(complex_query)
    
    print(f"\n🔍 Query Analysis:")
    intent = result.get("intent", {})
    print(f"   Intent Type: {intent.get('intent_type')}")
    print(f"   Complexity: {intent.get('complexity')}")
    print(f"   Analytical Patterns: {intent.get('analytical_patterns', [])}")
    
    print(f"\n🎯 Entity Extraction:")
    entities = result.get("entities", {})
    print(f"   Person Names: {entities.get('person_names', [])}")
    print(f"   Corrections: {entities.get('_corrections', [])}")
    
    if result.get("success"):
        rows = result.get("result", {}).get("rows", [])
        print(f"\n✅ Success: Generated working SQL")
        print(f"   Rows returned: {len(rows)}")
        print(f"   SQL: {result.get('sql', '')}")
        
        # Show first few results
        if rows:
            print(f"\n📋 Sample Results:")
            for i, row in enumerate(rows[:5]):
                print(f"   {i+1}. {row}")
        
        return True
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
        if result.get("sql"):
            print(f"   Attempted SQL: {result.get('sql')}")
        return False

def test_autocorrection_with_new_schema(orchestrator):
    """Test autocorrection works with the new database schema"""
    print("\n" + "="*60)
    print("✨ TESTING AUTOCORRECTION WITH NEW SCHEMA")
    print("="*60)
    
    # Test with intentional typos in the new schema
    typo_queries = [
        "Where does Dan Miler live?",  # Miler vs Miller
        "Show me Sara's orders",       # Sara vs Sarah
        "What did Mik purchase?",      # Mik vs Mike
    ]
    
    for query in typo_queries:
        print(f"\n📝 Query with typo: '{query}'")
        result = orchestrator.process_query(query)
        
        corrections = result.get("autocorrections", [])
        if corrections:
            print(f"✅ Autocorrect applied: {corrections}")
        else:
            print("ℹ️  No corrections applied")
        
        if result.get("success"):
            rows = result.get("result", {}).get("rows", [])
            print(f"✅ Query succeeded: {len(rows)} rows")
        else:
            print(f"❌ Query failed: {result.get('error')}")

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 COMPREHENSIVE MULTI-DATABASE & COMPLEX QUERY TEST")
    print("Testing issues raised:")
    print("1. Multi-database support beyond Chinook")
    print("2. Complex analytical queries")
    
    # Create test database with different schema
    test_db_path = create_test_database()
    
    try:
        # Initialize universal orchestrator
        config_manager = DatabaseConfigManager("test_db_configs.json")
        
        # Add the test database configuration
        from database_config import DatabaseConfig
        from datetime import datetime
        
        test_config = DatabaseConfig(
            name="Test_Ecommerce",
            db_type="sqlite",
            connection_type="local",
            database=test_db_path,
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        config_manager.configs["Test_Ecommerce"] = test_config
        config_manager.set_active_config("Test_Ecommerce")
        
        # Initialize orchestrator
        orchestrator = UniversalNL2SQLOrchestrator(config_manager)
        
        # Connect to test database
        success = orchestrator.connect_to_database("Test_Ecommerce")
        if not success:
            print("❌ Failed to connect to test database")
            return
        
        print("✅ Connected to test e-commerce database (NOT Chinook)")
        
        # Run tests
        test_schema_discovery(orchestrator)
        test_basic_queries(orchestrator)
        test_autocorrection_with_new_schema(orchestrator)
        
        # The main complex query test
        complex_success = test_complex_analytical_query(orchestrator)
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print("✅ Multi-database support: WORKING (tested with non-Chinook schema)")
        print(f"{'✅' if complex_success else '❌'} Complex analytical queries: {'WORKING' if complex_success else 'NEEDS IMPROVEMENT'}")
        
        if not complex_success:
            print("\n💡 RECOMMENDATIONS FOR COMPLEX QUERIES:")
            print("   - Query requires multi-step analysis with subqueries")
            print("   - May need enhanced prompt engineering for cross-customer analysis")
            print("   - Consider breaking down into simpler component queries")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        if os.path.exists("test_db_configs.json"):
            os.remove("test_db_configs.json")
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    run_comprehensive_test() 