#!/usr/bin/env python3
"""
Direct test of AutoGen system to debug the schema loading issue.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app directory to path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

print(f"Testing AutoGen system directly...")
print(f"App directory: {app_dir}")
print(f"Current directory: {os.getcwd()}")
print("-" * 50)

try:
    # Test 1: Check if database exists
    db_path = "Chinook_Sqlite.sqlite"
    if os.path.exists(db_path):
        print(f"✅ Database found: {db_path}")
        print(f"   Size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    else:
        print(f"❌ Database NOT found: {db_path}")
        sys.exit(1)
    
    # Test 2: Check if database module exists and works
    print("\nTesting database module...")
    from database import get_schema_representation, test_database_connection
    
    conn_test = test_database_connection(db_path)
    print(f"✅ Database connection test: {conn_test}")
    
    schema = get_schema_representation(db_path)
    print(f"✅ Schema loaded successfully. Length: {len(schema)} characters")
    print("First 500 characters of schema:")
    print(schema[:500])
    
    # Test 3: Initialize AutoGen orchestrator
    print("\n\nTesting AutoGen initialization...")
    from autogen_iterative import IterativeNL2SQLOrchestrator
    
    orchestrator = IterativeNL2SQLOrchestrator(db_path)
    print("✅ AutoGen orchestrator initialized successfully!")
    
    # Test 4: Process a simple query
    print("\n\nTesting query processing...")
    test_query = "Show me all customers"
    print(f"Query: {test_query}")
    
    result = orchestrator.process_query_iteratively(test_query)
    print(f"\nResult: {result}")
    
    # Test 5: Process Helena and Bjorn query
    print("\n\nTesting Helena and Bjorn query...")
    helena_query = "Where do Helena and Bjorn live?"
    print(f"Query: {helena_query}")
    
    result2 = orchestrator.process_query_iteratively(helena_query)
    print(f"\nResult: {result2}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed!")
