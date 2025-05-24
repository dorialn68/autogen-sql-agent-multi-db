#!/usr/bin/env python3
"""Direct JSON test"""
import json
import os

print("🔧 Direct JSON Test")
print("="*40)

print(f"Current directory: {os.getcwd()}")
print(f"File exists: {os.path.exists('database_configs.json')}")

try:
    with open('database_configs.json', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"File size: {len(content)} chars")
        print(f"First 100 chars: {repr(content[:100])}")
        
        # Try to parse JSON
        data = json.loads(content)
        print(f"✅ JSON is valid!")
        print(f"Keys: {list(data.keys())}")
        
        for key, config in data.items():
            print(f"  {key}: {config['db_type']} ({config.get('is_active', False)})")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 