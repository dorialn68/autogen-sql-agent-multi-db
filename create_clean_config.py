#!/usr/bin/env python3
"""Create clean database configuration file"""
import json
import os

# Database configurations
configs = {
    "Chinook_SQLite": {
        "name": "Chinook_SQLite",
        "db_type": "sqlite",
        "connection_type": "local",
        "database": "Chinook_Sqlite.sqlite",
        "schema": None,
        "host": None,
        "port": None,
        "username": None,
        "password": None,
        "ssl_mode": None,
        "connection_timeout": 30,
        "created_at": "2025-05-24T22:00:00.000000",
        "last_tested": None,
        "is_active": True
    },
    "Test_PostgreSQL": {
        "name": "Test_PostgreSQL",
        "db_type": "postgresql",
        "connection_type": "remote",
        "database": "test_db",
        "schema": "public",
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
        "password": "password",
        "ssl_mode": None,
        "connection_timeout": 30,
        "created_at": "2025-05-24T22:00:00.000000",
        "last_tested": None,
        "is_active": False
    },
    "Demo_Vertica": {
        "name": "Demo_Vertica",
        "db_type": "vertica",
        "connection_type": "remote",
        "database": "analytics_db",
        "schema": "public",
        "host": "vertica.example.com",
        "port": 5433,
        "username": "vertica_user",
        "password": "vertica_pass",
        "ssl_mode": None,
        "connection_timeout": 30,
        "created_at": "2025-05-24T22:00:00.000000",
        "last_tested": None,
        "is_active": False
    },
    "Local_PostgreSQL": {
        "name": "Local_PostgreSQL",
        "db_type": "postgresql",
        "connection_type": "remote",
        "database": "postgres",
        "schema": "public",
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
        "password": "postgres",
        "ssl_mode": None,
        "connection_timeout": 30,
        "created_at": "2025-05-24T22:00:00.000000",
        "last_tested": None,
        "is_active": False
    }
}

# Write clean UTF-8 file
print("🔧 Creating Clean Database Configuration File")
print("="*50)

with open('database_configs.json', 'w', encoding='utf-8') as f:
    json.dump(configs, f, indent=2, ensure_ascii=False)

print(f"✅ Created database_configs.json with {len(configs)} configurations")
print(f"File size: {os.path.getsize('database_configs.json')} bytes")

# Verify it's readable
try:
    with open('database_configs.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    print(f"✅ File is valid JSON with {len(test_data)} entries")
    print(f"Configurations: {list(test_data.keys())}")
except Exception as e:
    print(f"❌ Verification failed: {e}") 