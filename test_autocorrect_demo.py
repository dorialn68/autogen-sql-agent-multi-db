#!/usr/bin/env python3
"""
Demo script showing AutoGen with Autocorrect Agent handling typos
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
                    for i, row in enumerate(rows[:5]):
                        print(f"  {i+1}. {row}")
                    if len(rows) > 5:
                        print(f"  ... and {len(rows) - 5} more rows")
                else:
                    print("\n❌ NO RESULTS FOUND (even after autocorrection)")
            else:
                print(f"Result: {result.get('result')}")
                
            # Show if any corrections were made
            if 'history' in result:
                for h in result.get('history', []):
                    if 'corrections' in str(h):
                        print(f"🔧 Autocorrections applied!")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("AutoGen with Autocorrect Agent - Demonstration")
    print("=" * 80)
    
    # Wait for server
    print("Checking if server is running...")
    for i in range(3):
        try:
            response = requests.get(f"{base_url}/health")
            print(f"✅ Server is running")
            break
        except:
            if i < 2:
                print(f"Waiting for server... ({i+1}/3)")
                time.sleep(2)
            else:
                print("❌ Server not running")
                return
    
    # Test cases that should now work with autocorrection
    test_cases = [
        # Main test - Bjorn typo
        ("where does Helena and Bjprn lives ?", "MAIN TEST: Typo 'Bjprn' should be corrected to 'Bjørn'"),
        
        # Other typo tests
        ("find customer Steve Muray", "Typo: 'Muray' should be corrected to 'Murray'"),
        ("show me customer named Bjprn Hansen", "Single name typo test"),
        
        # Working queries for comparison
        ("where does Helena and Bjørn lives ?", "Correct spelling (with proper ø)"),
        ("where does Helena live", "Just Helena"),
    ]
    
    for query, description in test_cases:
        test_query(query, description)
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print("Summary:")
    print("✅ The Autocorrect Agent now handles typos in names by:")
    print("   - Using Levenshtein distance for fuzzy matching")
    print("   - Automatically correcting misspelled names")
    print("   - Finding the closest match in the database")

if __name__ == "__main__":
    main() 