"""
Test PostgreSQL and Vertica Database Connections

This script tests the database connectors for enterprise databases.
You'll need to provide actual connection details for your databases.
"""

from app.langchain_integration import DatabaseConnectorFactory
import logging

logging.basicConfig(level=logging.INFO)

def test_postgresql():
    """Test PostgreSQL connection."""
    print("Testing PostgreSQL Connection:")
    print("-" * 40)
    
    # Example PostgreSQL connection string
    # Replace with your actual PostgreSQL credentials
    postgresql_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'testdb',
        'user': 'postgres',
        'password': 'password'
    }
    
    connection_string = f"postgresql://{postgresql_config['user']}:{postgresql_config['password']}@{postgresql_config['host']}:{postgresql_config['port']}/{postgresql_config['database']}"
    
    try:
        connector = DatabaseConnectorFactory.create_connector(connection_string, 'postgresql')
        success, message = connector.test_connection()
        
        if success:
            print("✅ PostgreSQL connection successful")
            
            if connector.connect():
                schema = connector.get_schema()
                print(f"✅ Schema loaded: {len(schema['tables'])} tables")
                print(f"   Tables: {list(schema['tables'].keys())[:5]}...")
                connector.disconnect()
        else:
            print(f"❌ PostgreSQL connection failed: {message}")
            
    except Exception as e:
        print(f"❌ PostgreSQL test error: {e}")

def show_setup_instructions():
    """Show setup instructions for PostgreSQL and Vertica."""
    print("\n" + "="*60)
    print("🔧 SETUP INSTRUCTIONS FOR ENTERPRISE DATABASES")
    print("="*60)
    
    print("\n📊 PostgreSQL Setup:")
    print("1. Install PostgreSQL: https://www.postgresql.org/download/")
    print("2. Create a test database:")
    print("   createdb testdb")
    print("3. Update connection string in this script")
    print("4. Install psycopg2: pip install psycopg2-binary")
    
    print("\n📊 Vertica Setup:")
    print("1. Install Vertica Community Edition: https://www.vertica.com/download/")
    print("2. Create a test database")
    print("3. Update connection string in this script")
    print("4. Install vertica-python: pip install vertica-python")
    
    print("\n🔗 Connection String Examples:")
    print("PostgreSQL: postgresql://user:password@host:port/database")
    print("Vertica:    vertica://user:password@host:port/database")

if __name__ == "__main__":
    print("🚀 Testing Enterprise Database Connections")
    print("="*60)
    
    # Show supported databases
    supported = DatabaseConnectorFactory.get_supported_databases()
    print(f"Supported databases: {supported}")
    
    # Test connections (will fail without actual database instances)
    test_postgresql()
    
    # Show setup instructions
    show_setup_instructions()