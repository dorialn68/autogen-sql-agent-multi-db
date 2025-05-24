import requests
import json

# Test query for Bjorn
url = "http://localhost:5002/query"
data = {
    "query": "Where does Bjorn live?",
    "use_langchain": False
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"SQL: {result.get('sql')}")
        
        if 'result' in result and isinstance(result['result'], dict):
            rows = result['result'].get('rows', [])
            columns = result['result'].get('columns', [])
            
            print(f"\nColumns: {columns}")
            print(f"Number of rows: {len(rows)}")
            
            if rows:
                print("\nResults:")
                for row in rows:
                    print(f"  {row}")
            else:
                print("\nNo results found for Bjorn")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}") 