#!/usr/bin/env python3
"""
Test script to demonstrate AutoGen system issues with typos and misspellings
"""
import requests
import json
import time

base_url = "http://localhost:5002"

def test_query(query_text, description):
    """Test a single query and display results"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Query: '{query_text}'")
    print("-" * 60)
    
    data = {
        "query": query_text,
        "use_langchain": False
    }
    
    try:
        response = requests.post(f"{base_url}/query", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"SQL Generated: {result.get('sql')}")
            
            if 'result' in result and isinstance(result['result'], dict):
                rows = result['result'].get('rows', [])
                columns = result['result'].get('columns', [])
                
                print(f"\nColumns: {columns}")
                print(f"Rows found: {len(rows)}")
                
                if rows:
                    print("\nResults:")
                    for i, row in enumerate(rows[:5]):  # Show first 5 results
                        print(f"  {i+1}. {row}")
                    if len(rows) > 5:
                        print(f"  ... and {len(rows) - 5} more rows")
                else:
                    print("\n❌ NO RESULTS FOUND")
            else:
                print(f"Result: {result.get('result')}")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("Testing AutoGen System - Typo and Query Issues")
    print("=" * 80)
    
    # Wait for server
    print("Checking if server is running...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Server is running. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return
    
    # Test cases showing current issues
    test_cases = [
        # Typo in names
        ("where does Helena and Bjprn lives ?", "Typo in name 'Bjorn' → 'Bjprn'"),
        ("where does Helena and Bjorn lives ?", "Correct spelling of both names"),
        ("show me customer named Heléna", "Typo with accent in 'Helena'"),
        ("find customer Steve Muray", "Typo in last name 'Murray' → 'Muray'"),
        
        # Case sensitivity issues
        ("find customer steve murray", "Lowercase names"),
        ("WHERE DOES HELENA LIVE", "Uppercase query"),
        
        # Partial name matches
        ("find customers with first name starting with Hel", "Partial name match"),
        ("show me all customers from Prage", "Typo in city 'Prague' → 'Prage'"),
        
        # Common misspellings
        ("list all costumers", "Misspelling 'customers' → 'costumers'"),
        ("show me the custmer table", "Misspelling 'customer' → 'custmer'"),
    ]
    
    for query, description in test_cases:
        test_query(query, description)
        time.sleep(1)  # Avoid overwhelming the server
    
    print(f"\n{'='*80}")
    print("Test Summary:")
    print("The current AutoGen system has issues with:")
    print("1. Typos in names (Bjprn vs Bjorn)")
    print("2. Case sensitivity")
    print("3. Partial matches")
    print("4. Common misspellings of entities")
    print("5. No fuzzy matching or autocorrection")

if __name__ == "__main__":
    main() 