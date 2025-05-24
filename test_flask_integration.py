#!/usr/bin/env python3
"""Test Flask integration with database configurations"""
import sys
import os

# Add app directory to path like Flask app does
APP_DIR = os.path.dirname(os.path.abspath(__file__)) + '/app'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("🔧 Flask Integration Debug Test")
print("="*50)

print(f"🔍 PATH INFO:")
print(f"  Script location: {__file__}")
print(f"  APP_DIR: {APP_DIR}")
print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
print(f"  Current working directory: {os.getcwd()}")
print(f"  Python path includes: {sys.path[:3]}")

print(f"\n📁 FILE LOCATIONS:")
configs_in_cwd = os.path.exists('database_configs.json')
configs_in_root = os.path.exists(os.path.join(PROJECT_ROOT, 'database_configs.json'))
configs_in_app = os.path.exists(os.path.join(APP_DIR, 'database_configs.json'))

print(f"  database_configs.json in CWD: {configs_in_cwd}")
print(f"  database_configs.json in PROJECT_ROOT: {configs_in_root}")
print(f"  database_configs.json in APP_DIR: {configs_in_app}")

print(f"\n🔧 TESTING SYSTEM MANAGER:")
try:
    from system_manager import DualSystemManager
    
    # Test initialization
    manager = DualSystemManager("Chinook_Sqlite.sqlite")
    print(f"✅ DualSystemManager initialized")
    
    # Test database listing
    databases = manager.get_available_databases()
    print(f"✅ Found {len(databases)} databases:")
    
    for db in databases:
        print(f"  - {db['name']} ({db['type']}) - Active: {db.get('is_active', False)}")
        
except Exception as e:
    print(f"❌ Error testing system manager: {e}")
    import traceback
    traceback.print_exc()

print(f"\n🔧 TESTING DIRECT CONFIG MANAGER:")
try:
    from database_config import DatabaseConfigManager
    
    # Test with default filename
    dm = DatabaseConfigManager()
    configs = dm.list_configs()
    print(f"✅ DatabaseConfigManager found {len(configs)} configurations")
    
    for config in configs:
        print(f"  - {config['name']} ({config['db_type']})")
        
except Exception as e:
    print(f"❌ Error testing config manager: {e}")
    import traceback
    traceback.print_exc() 