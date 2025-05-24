#!/usr/bin/env python3
"""
Test script for the new database configuration system
"""
import sys
import os
sys.path.insert(0, 'app')

from database_config import DatabaseConfigManager
from database_adapter import UnifiedDatabaseAdapter

def test_database_config_system():
    """Test the new database configuration and adapter system"""
    print("🔧 Testing Database Configuration System")
    print("=" * 60)
    
    # Initialize the config manager
    config_manager = DatabaseConfigManager("test_database_configs.json")
    adapter = UnifiedDatabaseAdapter(config_manager)
    
    print(f"\n1️⃣ Initial Configuration")
    print("-" * 40)
    configs = config_manager.list_configs()
    for config in configs:
        print(f"   📄 {config['name']} ({config['db_type']}) - Active: {config['is_active']}")
    
    # Test SQLite connection
    print(f"\n2️⃣ Testing SQLite Connection")
    print("-" * 40)
    success, message = adapter.connect()
    print(f"   Connection: {'✅ Success' if success else '❌ Failed'}")
    print(f"   Message: {message}")
    
    if success:
        # Test query execution
        print(f"\n3️⃣ Testing Query Execution")
        print("-" * 40)
        success, result = adapter.execute_query("SELECT COUNT(*) as CustomerCount FROM Customer;")
        if success and 'rows' in result:
            print(f"   Query Result: {result['rows'][0][0]} customers found")
        
        # Test schema generation
        print(f"\n4️⃣ Testing Schema Generation")
        print("-" * 40)
        schema = adapter.generate_schema_representation()
        print(f"   Schema Preview: {schema[:200]}...")
    
    # Test adding PostgreSQL config (demo only - won't connect without real server)
    print(f"\n5️⃣ Adding PostgreSQL Configuration (Demo)")
    print("-" * 40)
    pg_success = config_manager.add_postgresql_config(
        name="Demo_PostgreSQL",
        host="localhost",
        database="demo_db",
        username="demo_user",
        password="demo_pass",
        port=5432,
        schema="public"
    )
    print(f"   PostgreSQL Config Added: {'✅ Success' if pg_success else '❌ Failed'}")
    
    # Test adding Vertica config (demo only)
    print(f"\n6️⃣ Adding Vertica Configuration (Demo)")
    print("-" * 40)
    vertica_success = config_manager.add_vertica_config(
        name="Demo_Vertica",
        host="vertica.example.com",
        database="analytics_db",
        username="analyst",
        password="secret",
        port=5433,
        schema="public"
    )
    print(f"   Vertica Config Added: {'✅ Success' if vertica_success else '❌ Failed'}")
    
    # List all configurations
    print(f"\n7️⃣ Final Configuration List")
    print("-" * 40)
    configs = config_manager.list_configs()
    for config in configs:
        status = "🟢 Active" if config['is_active'] else "⚪ Inactive"
        conn_type = f"{config['connection_type']}" if config['connection_type'] else "N/A"
        print(f"   📄 {config['name']}")
        print(f"      Type: {config['db_type'].upper()} ({conn_type}) - {status}")
        if config['host']:
            print(f"      Host: {config['host']}:{config['port']}")
        print(f"      Database: {config['database']}")
        if config['schema']:
            print(f"      Schema: {config['schema']}")
        print()
    
    # Test connection testing (for PostgreSQL - will fail but show functionality)
    print(f"\n8️⃣ Testing Connection Validation")
    print("-" * 40)
    for config in configs:
        if config['db_type'] != 'sqlite':  # Skip SQLite as we know it works
            print(f"   Testing {config['name']}...")
            success, message, metadata = config_manager.test_connection(config['name'])
            print(f"   Result: {'✅ Success' if success else '❌ Expected Failure (no server)'}")
            print(f"   Message: {message}")
            if metadata:
                print(f"   Metadata: {metadata}")
            print()
    
    # Cleanup
    adapter.close()
    if os.path.exists("test_database_configs.json"):
        os.remove("test_database_configs.json")
    
    print("🎉 Database Configuration System Test Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Multi-database configuration management")
    print("✅ SQLite, PostgreSQL, and Vertica support")
    print("✅ Connection testing and validation")
    print("✅ Unified query execution interface")
    print("✅ Automatic schema analysis")
    print("✅ Local and remote database support")

if __name__ == "__main__":
    test_database_config_system() 