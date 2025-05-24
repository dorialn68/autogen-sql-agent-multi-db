#!/usr/bin/env python3
"""
Advanced Database Configuration Manager
Supports SQLite, PostgreSQL, and Vertica with local and remote connections
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration structure"""
    name: str
    db_type: str  # 'sqlite', 'postgresql', 'vertica'
    connection_type: str  # 'local', 'remote'
    
    # Common fields
    database: str
    schema: Optional[str] = None
    
    # For PostgreSQL/Vertica
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Additional options
    ssl_mode: Optional[str] = None
    connection_timeout: int = 30
    
    # Metadata
    created_at: Optional[str] = None
    last_tested: Optional[str] = None
    is_active: bool = False

class DatabaseConfigManager:
    """Manages database configurations and connections"""
    
    def __init__(self, config_file: str = "database_configs.json"):
        self.config_file = config_file
        self.configs: Dict[str, DatabaseConfig] = {}
        self.active_config: Optional[DatabaseConfig] = None
        self._load_configs()
        
    def _load_configs(self):
        """Load configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config_dict in data.items():
                        self.configs[name] = DatabaseConfig(**config_dict)
                logger.info(f"DATABASE CONFIG: Loaded {len(self.configs)} configurations")
            except Exception as e:
                logger.error(f"DATABASE CONFIG: Error loading configs: {e}")
        else:
            # Create default SQLite config
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default SQLite configuration"""
        default_config = DatabaseConfig(
            name="Chinook_SQLite",
            db_type="sqlite",
            connection_type="local",
            database="Chinook_Sqlite.sqlite",
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        self.configs[default_config.name] = default_config
        self.active_config = default_config
        self._save_configs()
        logger.info("DATABASE CONFIG: Created default SQLite configuration")
    
    def _save_configs(self):
        """Save configurations to file"""
        try:
            config_dict = {}
            for name, config in self.configs.items():
                config_dict[name] = {
                    'name': config.name,
                    'db_type': config.db_type,
                    'connection_type': config.connection_type,
                    'database': config.database,
                    'schema': config.schema,
                    'host': config.host,
                    'port': config.port,
                    'username': config.username,
                    'password': config.password,  # Note: In production, encrypt this
                    'ssl_mode': config.ssl_mode,
                    'connection_timeout': config.connection_timeout,
                    'created_at': config.created_at,
                    'last_tested': config.last_tested,
                    'is_active': config.is_active
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logger.info("DATABASE CONFIG: Configurations saved")
        except Exception as e:
            logger.error(f"DATABASE CONFIG: Error saving configs: {e}")
    
    def add_postgresql_config(self, name: str, host: str, database: str, username: str, 
                            password: str, port: int = 5432, schema: str = "public",
                            connection_type: str = "remote", ssl_mode: str = "prefer") -> bool:
        """Add PostgreSQL configuration"""
        try:
            config = DatabaseConfig(
                name=name,
                db_type="postgresql",
                connection_type=connection_type,
                database=database,
                schema=schema,
                host=host,
                port=port,
                username=username,
                password=password,
                ssl_mode=ssl_mode,
                created_at=datetime.now().isoformat()
            )
            
            self.configs[name] = config
            self._save_configs()
            logger.info(f"DATABASE CONFIG: Added PostgreSQL config '{name}'")
            return True
        except Exception as e:
            logger.error(f"DATABASE CONFIG: Error adding PostgreSQL config: {e}")
            return False
    
    def add_vertica_config(self, name: str, host: str, database: str, username: str,
                          password: str, port: int = 5433, schema: str = "public",
                          connection_type: str = "remote") -> bool:
        """Add Vertica configuration"""
        try:
            config = DatabaseConfig(
                name=name,
                db_type="vertica",
                connection_type=connection_type,
                database=database,
                schema=schema,
                host=host,
                port=port,
                username=username,
                password=password,
                created_at=datetime.now().isoformat()
            )
            
            self.configs[name] = config
            self._save_configs()
            logger.info(f"DATABASE CONFIG: Added Vertica config '{name}'")
            return True
        except Exception as e:
            logger.error(f"DATABASE CONFIG: Error adding Vertica config: {e}")
            return False
    
    def test_connection(self, config_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Test database connection and gather metadata"""
        if config_name not in self.configs:
            return False, f"Configuration '{config_name}' not found", {}
        
        config = self.configs[config_name]
        metadata = {}
        
        try:
            if config.db_type == "sqlite":
                return self._test_sqlite_connection(config, metadata)
            elif config.db_type == "postgresql":
                return self._test_postgresql_connection(config, metadata)
            elif config.db_type == "vertica":
                return self._test_vertica_connection(config, metadata)
            else:
                return False, f"Unsupported database type: {config.db_type}", {}
                
        except Exception as e:
            logger.error(f"DATABASE CONFIG: Connection test failed for '{config_name}': {e}")
            return False, str(e), {}
    
    def _test_sqlite_connection(self, config: DatabaseConfig, metadata: Dict) -> Tuple[bool, str, Dict]:
        """Test SQLite connection"""
        import sqlite3
        
        if not os.path.exists(config.database):
            return False, f"SQLite file not found: {config.database}", {}
        
        try:
            conn = sqlite3.connect(config.database)
            cursor = conn.cursor()
            
            # Get basic metadata
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get database size
            db_size = os.path.getsize(config.database) / (1024 * 1024)  # MB
            
            metadata.update({
                'tables': tables,
                'table_count': len(tables),
                'database_size_mb': round(db_size, 2),
                'connection_type': 'SQLite File'
            })
            
            conn.close()
            config.last_tested = datetime.now().isoformat()
            self._save_configs()
            
            return True, "SQLite connection successful", metadata
            
        except Exception as e:
            return False, f"SQLite connection failed: {e}", {}
    
    def _test_postgresql_connection(self, config: DatabaseConfig, metadata: Dict) -> Tuple[bool, str, Dict]:
        """Test PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2 import sql
        except ImportError:
            return False, "psycopg2 not installed. Run: pip install psycopg2-binary", {}
        
        try:
            # Build connection string
            conn_params = {
                'host': config.host,
                'port': config.port,
                'database': config.database,
                'user': config.username,
                'password': config.password,
                'connect_timeout': config.connection_timeout
            }
            
            if config.ssl_mode:
                conn_params['sslmode'] = config.ssl_mode
            
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Get server version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Get schema tables
            schema = config.schema or 'public'
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """, (schema,))
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(%s));", (config.database,))
            db_size = cursor.fetchone()[0]
            
            metadata.update({
                'server_version': version.split(',')[0],
                'schema': schema,
                'tables': tables,
                'table_count': len(tables),
                'database_size': db_size,
                'connection_type': 'PostgreSQL'
            })
            
            conn.close()
            config.last_tested = datetime.now().isoformat()
            self._save_configs()
            
            return True, "PostgreSQL connection successful", metadata
            
        except Exception as e:
            return False, f"PostgreSQL connection failed: {e}", {}
    
    def _test_vertica_connection(self, config: DatabaseConfig, metadata: Dict) -> Tuple[bool, str, Dict]:
        """Test Vertica connection"""
        try:
            import vertica_python
        except ImportError:
            return False, "vertica-python not installed. Run: pip install vertica-python", {}
        
        try:
            conn_info = {
                'host': config.host,
                'port': config.port,
                'user': config.username,
                'password': config.password,
                'database': config.database,
                'connection_timeout': config.connection_timeout
            }
            
            conn = vertica_python.connect(**conn_info)
            cursor = conn.cursor()
            
            # Get server version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Get schema tables
            schema = config.schema or 'public'
            cursor.execute("""
                SELECT table_name 
                FROM tables 
                WHERE table_schema = ? 
                ORDER BY table_name;
            """, (schema,))
            tables = [row[0] for row in cursor.fetchall()]
            
            metadata.update({
                'server_version': version,
                'schema': schema,
                'tables': tables,
                'table_count': len(tables),
                'connection_type': 'Vertica'
            })
            
            conn.close()
            config.last_tested = datetime.now().isoformat()
            self._save_configs()
            
            return True, "Vertica connection successful", metadata
            
        except Exception as e:
            return False, f"Vertica connection failed: {e}", {}
    
    def set_active_config(self, config_name: str) -> bool:
        """Set active database configuration"""
        if config_name not in self.configs:
            return False
        
        # Deactivate all configs
        for config in self.configs.values():
            config.is_active = False
        
        # Activate selected config
        self.configs[config_name].is_active = True
        self.active_config = self.configs[config_name]
        self._save_configs()
        
        logger.info(f"DATABASE CONFIG: Activated configuration '{config_name}'")
        return True
    
    def get_active_config(self) -> Optional[DatabaseConfig]:
        """Get currently active configuration"""
        return self.active_config
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """List all configurations with metadata"""
        configs_list = []
        for name, config in self.configs.items():
            configs_list.append({
                'name': name,
                'db_type': config.db_type,
                'connection_type': config.connection_type,
                'database': config.database,
                'host': config.host,
                'port': config.port,
                'schema': config.schema,
                'is_active': config.is_active,
                'last_tested': config.last_tested,
                'created_at': config.created_at
            })
        return configs_list
    
    def delete_config(self, config_name: str) -> bool:
        """Delete a configuration"""
        if config_name not in self.configs:
            return False
        
        # Don't delete if it's the only config
        if len(self.configs) == 1:
            logger.warning("DATABASE CONFIG: Cannot delete the only configuration")
            return False
        
        # If deleting active config, activate another one
        if self.configs[config_name].is_active and len(self.configs) > 1:
            for name, config in self.configs.items():
                if name != config_name:
                    self.set_active_config(name)
                    break
        
        del self.configs[config_name]
        self._save_configs()
        logger.info(f"DATABASE CONFIG: Deleted configuration '{config_name}'")
        return True 