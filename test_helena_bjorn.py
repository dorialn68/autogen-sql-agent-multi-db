#!/usr/bin/env python3
"""
Test script to validate the AutoGen system with Helena and Bjorn query.
"""
import requests
import json
import time

base_url = "http://localhost:5002"

print("Testing AutoGen SQL Agent")
print("=" * 50)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(3)

# Test 1: Check if server is running
try:
    response = requests.get(f"{base_url}/status")
    print(f"✅ Server is running. Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"❌ Server not running: {e}")
    exit(1)

# Test 2: Simple query first
print("\n\nTest 2: Simple query - List all customers")
print("-" * 50)
test_query = {
    "query": "Show me all customers",
    "use_langchain": False
}

response = requests.post(f"{base_url}/query", json=test_query)
if response.status_code == 200:
    result = response.json()
    print(f"✅ Query successful!")
    print(f"SQL: {result.get('sql', 'N/A')}")
    if 'result' in result and isinstance(result['result'], dict) and 'rows' in result['result']:
        print(f"Found {len(result['result']['rows'])} customers")
else:
    print(f"❌ Query failed: {response.status_code}")
    print(response.text)

# Test 3: Helena and Bjorn query
print("\n\nTest 3: Helena and Bjorn query")
print("-" * 50)
helena_query = {
    "query": "Where do Helena and Bjorn live?",
    "use_langchain": False
}

print("Sending query: 'Where do Helena and Bjorn live?'")
response = requests.post(f"{base_url}/query", json=helena_query)
if response.status_code == 200:
    result = response.json()
    print(f"✅ Query successful!")
    print(f"SQL: {result.get('sql', 'N/A')}")
    if 'result' in result:
        if isinstance(result['result'], dict) and 'rows' in result['result']:
            rows = result['result']['rows']
            if rows:
                print(f"\nResults found ({len(rows)} customers):")
                for row in rows:
                    print(f"  - {row}")
            else:
                print("No results found for Helena and Bjorn")
        else:
            print(f"Result: {result['result']}")
else:
    print(f"❌ Query failed: {response.status_code}")
    print(response.text)

print("\n" + "=" * 50)
print("Test completed!")
