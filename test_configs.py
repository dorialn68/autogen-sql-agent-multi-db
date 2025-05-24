#!/usr/bin/env python3
"""Test database configurations"""
import sys
import os
sys.path.insert(0, 'app')

from database_config import DatabaseConfigManager

# Test configuration loading
print("🔧 Testing Database Configuration Loading")
print("="*50)

# Debug information
print(f"🔍 DEBUG INFO:")
print(f"  Current Working Directory: {os.getcwd()}")
print(f"  Expected config file: database_configs.json")
print(f"  Config file exists: {os.path.exists('database_configs.json')}")

if os.path.exists('database_configs.json'):
    import json
    try:
        with open('database_configs.json', 'r') as f:
            data = json.load(f)
        print(f"  JSON file is valid with {len(data)} entries")
        print(f"  Entries: {list(data.keys())}")
    except Exception as e:
        print(f"  JSON file error: {e}")

print("\n" + "="*50)

dm = DatabaseConfigManager()
configs = dm.list_configs()

print(f"✅ Found {len(configs)} configurations:")
for config in configs:
    status = "🟢 ACTIVE" if config["is_active"] else "⚪ Inactive"
    print(f"  - {config['name']} ({config['db_type'].upper()}) - {status}")
    if config['db_type'] != 'sqlite':
        print(f"    Host: {config.get('host')}:{config.get('port')}")
        print(f"    Database: {config.get('database')}")

print(f"\n📊 Configuration Summary:")
print(f"  SQLite configs: {len([c for c in configs if c['db_type'] == 'sqlite'])}")
print(f"  PostgreSQL configs: {len([c for c in configs if c['db_type'] == 'postgresql'])}")
print(f"  Vertica configs: {len([c for c in configs if c['db_type'] == 'vertica'])}")

active_config = dm.get_active_config()
if active_config:
    print(f"\n🎯 Active Configuration: {active_config.name} ({active_config.db_type})")
else:
    print(f"\n❌ No active configuration found!") 