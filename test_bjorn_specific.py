#!/usr/bin/env python3
"""
Test script specifically for Bjorn autocorrection
"""
import requests
import json

def test_bjorn_autocorrect():
    """Test the specific case of Bjorn -> Bjørn autocorrection"""
    print("Testing Bjorn Autocorrection")
    print("=" * 50)
    
    url = "http://localhost:5002/query"
    
    # Test queries with different spellings of Bjorn
    test_cases = [
        "where does Helena and Bjorn live",
        "where does Helena and Bjorn lives",  
        "where does Helena and Bjprn live",  # typo
        "show me Bjorn",
        "find customer Bjorn Hansen"
    ]
    
    for query in test_cases:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 30)
        
        try:
            response = requests.post(url, json={
                "query": query,
                "system": "autogen"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Success: {result.get('success')}")
                print(f"SQL: {result.get('sql', 'N/A')}")
                
                # Check for autocorrections
                if result.get('autocorrections'):
                    print(f"🔧 Autocorrections: {result['autocorrections']}")
                
                if result.get('message'):
                    print(f"💬 Message: {result['message']}")
                
                # Check results
                if result.get('result') and result['result'].get('rows'):
                    rows = result['result']['rows']
                    print(f"📊 Results: {len(rows)} rows found")
                    for row in rows:
                        print(f"   {row}")
                else:
                    print("❌ No results found")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    # Test database content directly
    print("\n📋 Direct database check for names with 'j':")
    print("-" * 40)
    try:
        response = requests.post(url, json={
            "query": "SELECT FirstName FROM Customer WHERE FirstName LIKE '%j%'",
            "use_langchain": False
        }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('result') and result['result'].get('rows'):
                rows = result['result']['rows']
                print(f"Names containing 'j': {[row[0] for row in rows]}")
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    test_bjorn_autocorrect() 