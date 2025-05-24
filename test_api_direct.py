#!/usr/bin/env python3
"""
Direct API test to diagnose the zero results issue
"""
import requests
import json

def test_api():
    print("Testing the API directly...")
    
    # Test 1: Direct SQL query (bypass NL-to-SQL)
    print("\n1. Testing direct SQL query:")
    try:
        response = requests.post('http://localhost:5002/query', 
                                json={
                                    "query": "SELECT COUNT(*) FROM Customer", 
                                    "use_langchain": False
                                }, 
                                timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Simple customer list query
    print("\n2. Testing simple customer query:")
    try:
        response = requests.post('http://localhost:5002/query', 
                                json={
                                    "query": "SELECT FirstName, LastName FROM Customer LIMIT 3", 
                                    "use_langchain": False
                                }, 
                                timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Natural language query with AutoGen
    print("\n3. Testing natural language query:")
    try:
        response = requests.post('http://localhost:5002/query', 
                                json={
                                    "query": "how many customers do we have", 
                                    "system": "autogen"
                                }, 
                                timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Test the Helena query that should work
    print("\n4. Testing Helena query:")
    try:
        response = requests.post('http://localhost:5002/query', 
                                json={
                                    "query": "where does Helena live", 
                                    "system": "autogen"
                                }, 
                                timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api() 