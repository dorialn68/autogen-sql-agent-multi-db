#!/usr/bin/env python3
"""
Test Vertica Connection and Setup Sample Data
Validates local Vertica CE is working and adds it to our multi-database system
"""
import sys
import os
sys.path.insert(0, 'app')

try:
    import vertica_python
    print("✅ vertica-python driver is available")
except ImportError:
    print("❌ vertica-python not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "vertica-python"])
    import vertica_python
    print("✅ vertica-python installed successfully")

from database_config import DatabaseConfigManager
import time

def test_vertica_connection():
    """Test direct connection to Vertica"""
    print("🐘 Testing Vertica Community Edition Connection")
    print("=" * 60)
    
    conn_info = {
        'host': 'localhost',
        'port': 5433,
        'user': 'dbadmin',
        'password': 'password123',
        'database': 'testdb',
        'connection_timeout': 30
    }
    
    print(f"🔗 Connecting to Vertica...")
    print(f"   Host: {conn_info['host']}:{conn_info['port']}")
    print(f"   Database: {conn_info['database']}")
    print(f"   User: {conn_info['user']}")
    
    try:
        # Test connection
        conn = vertica_python.connect(**conn_info)
        cursor = conn.cursor()
        
        # Get version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to Vertica!")
        print(f"   Version: {version.split(',')[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Existing tables: {len(tables)}")
        
        # Create sample data if not exists
        if 'customers' not in tables:
            print("📊 Creating sample data...")
            
            # Create customers table
            cursor.execute("""
                CREATE TABLE customers (
                    id INT PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    city VARCHAR(50),
                    country VARCHAR(50),
                    created_date DATE DEFAULT CURRENT_DATE
                );
            """)
            
            # Create orders table
            cursor.execute("""
                CREATE TABLE orders (
                    order_id INT PRIMARY KEY,
                    customer_id INT,
                    product_name VARCHAR(100),
                    amount DECIMAL(10,2),
                    order_date DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                );
            """)
            
            # Insert sample customers
            customers_data = [
                (1, 'John Doe', 'john@example.com', 'New York', 'USA'),
                (2, 'Jane Smith', 'jane@example.com', 'London', 'UK'),
                (3, 'Carlos Rodriguez', 'carlos@example.com', 'Madrid', 'Spain'),
                (4, 'Liu Wei', 'liu@example.com', 'Beijing', 'China'),
                (5, 'Priya Patel', 'priya@example.com', 'Mumbai', 'India'),
                (6, 'Hans Mueller', 'hans@example.com', 'Berlin', 'Germany'),
                (7, 'Marie Dubois', 'marie@example.com', 'Paris', 'France'),
                (8, 'Yuki Tanaka', 'yuki@example.com', 'Tokyo', 'Japan'),
                (9, 'Ahmed Hassan', 'ahmed@example.com', 'Cairo', 'Egypt'),
                (10, 'Isabella Costa', 'isabella@example.com', 'São Paulo', 'Brazil')
            ]
            
            cursor.executemany(
                "INSERT INTO customers (id, name, email, city, country) VALUES (?, ?, ?, ?, ?)",
                customers_data
            )
            
            # Insert sample orders
            orders_data = [
                (1, 1, 'Laptop Pro', 1299.99),
                (2, 1, 'Wireless Mouse', 29.99),
                (3, 2, 'Smartphone X', 899.99),
                (4, 3, 'Tablet Air', 549.99),
                (5, 3, 'Keyboard Mech', 159.99),
                (6, 4, 'Monitor 4K', 399.99),
                (7, 5, 'Headphones Pro', 199.99),
                (8, 2, 'Smart Watch', 299.99),
                (9, 6, 'Gaming Chair', 249.99),
                (10, 7, 'Webcam HD', 89.99),
                (11, 1, 'External SSD', 129.99),
                (12, 8, 'Power Bank', 49.99)
            ]
            
            cursor.executemany(
                "INSERT INTO orders (order_id, customer_id, product_name, amount) VALUES (?, ?, ?, ?)",
                orders_data
            )
            
            conn.commit()
            print("✅ Sample data created successfully!")
        
        # Test some analytical queries
        print("🔍 Testing analytical queries...")
        
        # Customer count by country
        cursor.execute("""
            SELECT country, COUNT(*) as customer_count, AVG(LENGTH(name)) as avg_name_length
            FROM customers 
            GROUP BY country 
            ORDER BY customer_count DESC;
        """)
        results = cursor.fetchall()
        print(f"   Countries with customers: {len(results)}")
        
        # Cross-customer purchase analysis
        cursor.execute("""
            SELECT 
                c.country,
                COUNT(DISTINCT c.id) as customers,
                COUNT(o.order_id) as total_orders,
                SUM(o.amount) as total_revenue
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.country
            ORDER BY total_revenue DESC NULLS LAST;
        """)
        revenue_results = cursor.fetchall()
        print(f"   Revenue analysis completed: {len(revenue_results)} countries")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def add_vertica_to_config():
    """Add Vertica configuration to our database system"""
    print("\n🔧 Adding Vertica to Database Configuration")
    print("-" * 40)
    
    try:
        # Initialize config manager
        config_manager = DatabaseConfigManager()
        
        # Add Vertica configuration
        success = config_manager.add_vertica_config(
            name="Local_Vertica_CE",
            host="localhost",
            database="testdb",
            username="dbadmin",
            password="password123",
            port=5433,
            schema="public"
        )
        
        if success:
            print("✅ Vertica configuration added successfully!")
            
            # List all configurations
            configs = config_manager.list_configs()
            print(f"📋 Total database configurations: {len(configs)}")
            
            for config in configs:
                status = "🟢 ACTIVE" if config["is_active"] else "⚪ Inactive"
                print(f"   - {config['name']} ({config['db_type'].upper()}) - {status}")
                
            return True
        else:
            print("❌ Failed to add Vertica configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error adding configuration: {e}")
        return False

def test_system_integration():
    """Test Vertica through our database system"""
    print("\n🚀 Testing System Integration")
    print("-" * 40)
    
    try:
        from system_manager import DualSystemManager
        
        # Initialize system manager
        manager = DualSystemManager("Chinook_Sqlite.sqlite")
        
        # Get available databases
        databases = manager.get_available_databases()
        vertica_dbs = [db for db in databases if db['type'] == 'vertica']
        
        print(f"📊 Available databases: {len(databases)}")
        print(f"🐘 Vertica databases: {len(vertica_dbs)}")
        
        if vertica_dbs:
            print(f"✅ Vertica database found: {vertica_dbs[0]['name']}")
            return True
        else:
            print("❌ No Vertica databases found in system")
            return False
            
    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🐘 VERTICA COMMUNITY EDITION VALIDATION")
    print("=" * 60)
    
    # Test 1: Direct connection
    if not test_vertica_connection():
        print("\n❌ Vertica connection test failed!")
        print("Make sure Vertica is running: docker ps")
        print("Check logs: docker logs vertica-ce")
        return False
    
    # Test 2: Add to configuration
    if not add_vertica_to_config():
        print("\n❌ Configuration setup failed!")
        return False
    
    # Test 3: System integration
    if not test_system_integration():
        print("\n⚠️  System integration test failed, but Vertica is configured")
    
    print("\n🎉 VERTICA SETUP COMPLETE!")
    print("=" * 60)
    print("✅ Vertica is running and configured")
    print("✅ Sample data is available")
    print("✅ Ready for multi-database testing")
    print("")
    print("🚀 Next Steps:")
    print("1. Restart Flask server: python app/app_dual_super_safe.py")
    print("2. Open web interface: http://localhost:5002")
    print("3. Select 'Local_Vertica_CE' from database dropdown")
    print("4. Test complex queries!")
    
    return True

if __name__ == "__main__":
    main() 