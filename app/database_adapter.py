#!/usr/bin/env python3
"""
Unified Database Adapter
Provides consistent interface for SQLite, PostgreSQL, and Vertica databases
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from database_config import DatabaseConfig, DatabaseConfigManager

logger = logging.getLogger(__name__)

class UnifiedDatabaseAdapter:
    """Unified database adapter for multiple database types"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self.active_connection = None
        self._current_config = None
    
    def connect(self, config_name: Optional[str] = None) -> Tuple[bool, str]:
        """Connect to database using specified or active configuration"""
        if config_name:
            config = self.config_manager.configs.get(config_name)
        else:
            config = self.config_manager.get_active_config()
        
        if not config:
            return False, "No database configuration found"
        
        try:
            if config.db_type == "sqlite":
                success, message = self._connect_sqlite(config)
            elif config.db_type == "postgresql":
                success, message = self._connect_postgresql(config)
            elif config.db_type == "vertica":
                success, message = self._connect_vertica(config)
            else:
                return False, f"Unsupported database type: {config.db_type}"
            
            if success:
                self._current_config = config
                logger.info(f"DATABASE ADAPTER: Connected to {config.db_type} database '{config.name}'")
            
            return success, message
            
        except Exception as e:
            logger.error(f"DATABASE ADAPTER: Connection failed: {e}")
            return False, str(e)
    
    def _connect_sqlite(self, config: DatabaseConfig) -> Tuple[bool, str]:
        """Connect to SQLite database"""
        import sqlite3
        import os
        
        if not os.path.exists(config.database):
            return False, f"SQLite file not found: {config.database}"
        
        try:
            self.active_connection = sqlite3.connect(config.database)
            return True, "SQLite connection established"
        except Exception as e:
            return False, f"SQLite connection failed: {e}"
    
    def _connect_postgresql(self, config: DatabaseConfig) -> Tuple[bool, str]:
        """Connect to PostgreSQL database"""
        try:
            import psycopg2
        except ImportError:
            return False, "psycopg2 not installed. Run: pip install psycopg2-binary"
        
        try:
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
            
            self.active_connection = psycopg2.connect(**conn_params)
            return True, "PostgreSQL connection established"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {e}"
    
    def _connect_vertica(self, config: DatabaseConfig) -> Tuple[bool, str]:
        """Connect to Vertica database"""
        try:
            import vertica_python
        except ImportError:
            return False, "vertica-python not installed. Run: pip install vertica-python"
        
        try:
            conn_info = {
                'host': config.host,
                'port': config.port,
                'user': config.username,
                'password': config.password,
                'database': config.database,
                'connection_timeout': config.connection_timeout
            }
            
            self.active_connection = vertica_python.connect(**conn_info)
            return True, "Vertica connection established"
        except Exception as e:
            return False, f"Vertica connection failed: {e}"
    
    def execute_query(self, sql: str) -> Tuple[bool, Any]:
        """Execute SQL query on the active connection"""
        if not self.active_connection or not self._current_config:
            return False, "No active database connection"
        
        try:
            cursor = self.active_connection.cursor()
            cursor.execute(sql)
            
            # Handle different query types
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                
                # Get column names
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return True, {'columns': columns, 'rows': results}
                return True, {'columns': [], 'rows': results}
            else:
                # For INSERT, UPDATE, DELETE, etc.
                if self._current_config.db_type != "sqlite":
                    self.active_connection.commit()
                affected_rows = cursor.rowcount
                return True, {'affected_rows': affected_rows}
                
        except Exception as e:
            logger.error(f"DATABASE ADAPTER: Query execution failed: {e}")
            return False, str(e)
        finally:
            if cursor:
                cursor.close()
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information for the current database"""
        if not self.active_connection or not self._current_config:
            return {}
        
        try:
            if self._current_config.db_type == "sqlite":
                return self._get_sqlite_schema()
            elif self._current_config.db_type == "postgresql":
                return self._get_postgresql_schema()
            elif self._current_config.db_type == "vertica":
                return self._get_vertica_schema()
        except Exception as e:
            logger.error(f"DATABASE ADAPTER: Schema retrieval failed: {e}")
            return {}
    
    def _get_sqlite_schema(self) -> Dict[str, Any]:
        """Get SQLite schema information"""
        cursor = self.active_connection.cursor()
        schema_info = {"tables": {}, "database_type": "sqlite"}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            table_info = {
                "columns": [],
                "primary_keys": [],
                "foreign_keys": []
            }
            
            for col in columns:
                cid, name, data_type, not_null, default_value, pk = col
                table_info["columns"].append({
                    "name": name,
                    "type": data_type,
                    "not_null": bool(not_null),
                    "default": default_value,
                    "primary_key": bool(pk)
                })
                if pk:
                    table_info["primary_keys"].append(name)
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            foreign_keys = cursor.fetchall()
            for fk in foreign_keys:
                table_info["foreign_keys"].append({
                    "column": fk[3],
                    "references_table": fk[2],
                    "references_column": fk[4]
                })
            
            schema_info["tables"][table] = table_info
        
        return schema_info
    
    def _get_postgresql_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema information"""
        cursor = self.active_connection.cursor()
        schema_name = self._current_config.schema or 'public'
        schema_info = {"tables": {}, "database_type": "postgresql", "schema": schema_name}
        
        # Get all tables in schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """, (schema_name,))
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, (schema_name, table))
            columns = cursor.fetchall()
            
            # Get primary keys
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = %s AND tc.table_name = %s 
                AND tc.constraint_type = 'PRIMARY KEY';
            """, (schema_name, table))
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            table_info = {
                "columns": [],
                "primary_keys": primary_keys,
                "foreign_keys": []
            }
            
            for col in columns:
                column_name, data_type, is_nullable, default_value = col
                table_info["columns"].append({
                    "name": column_name,
                    "type": data_type,
                    "not_null": is_nullable == 'NO',
                    "default": default_value,
                    "primary_key": column_name in primary_keys
                })
            
            schema_info["tables"][table] = table_info
        
        return schema_info
    
    def _get_vertica_schema(self) -> Dict[str, Any]:
        """Get Vertica schema information"""
        cursor = self.active_connection.cursor()
        schema_name = self._current_config.schema or 'public'
        schema_info = {"tables": {}, "database_type": "vertica", "schema": schema_name}
        
        # Get all tables in schema
        cursor.execute("""
            SELECT table_name 
            FROM tables 
            WHERE table_schema = ?
            ORDER BY table_name;
        """, (schema_name,))
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM columns
                WHERE table_schema = ? AND table_name = ?
                ORDER BY ordinal_position;
            """, (schema_name, table))
            columns = cursor.fetchall()
            
            table_info = {
                "columns": [],
                "primary_keys": [],
                "foreign_keys": []
            }
            
            for col in columns:
                column_name, data_type, is_nullable, default_value = col
                table_info["columns"].append({
                    "name": column_name,
                    "type": data_type,
                    "not_null": not is_nullable,
                    "default": default_value,
                    "primary_key": False  # Vertica primary keys need separate query
                })
            
            schema_info["tables"][table] = table_info
        
        return schema_info
    
    def generate_schema_representation(self) -> str:
        """Generate a text representation of the database schema for AI"""
        schema_info = self.get_schema_info()
        if not schema_info:
            return "Error: Could not retrieve schema information"
        
        lines = []
        db_type = schema_info.get("database_type", "unknown")
        lines.append(f"Database Type: {db_type.upper()}")
        
        if "schema" in schema_info:
            lines.append(f"Schema: {schema_info['schema']}")
        
        lines.append("\nTables and Columns:")
        lines.append("=" * 50)
        
        for table_name, table_info in schema_info["tables"].items():
            lines.append(f"\nTable: {table_name}")
            lines.append("-" * (len(table_name) + 7))
            
            for column in table_info["columns"]:
                constraints = []
                if column["primary_key"]:
                    constraints.append("PK")
                if column["not_null"]:
                    constraints.append("NOT NULL")
                if column["default"]:
                    constraints.append(f"DEFAULT {column['default']}")
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                lines.append(f"  {column['name']}: {column['type']}{constraint_str}")
            
            if table_info["foreign_keys"]:
                lines.append("  Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    lines.append(f"    {fk['column']} -> {fk['references_table']}.{fk['references_column']}")
        
        return "\n".join(lines)
    
    def close(self):
        """Close the active database connection"""
        if self.active_connection:
            try:
                self.active_connection.close()
                logger.info("DATABASE ADAPTER: Connection closed")
            except Exception as e:
                logger.error(f"DATABASE ADAPTER: Error closing connection: {e}")
            finally:
                self.active_connection = None
                self._current_config = None
    
    def get_current_config(self) -> Optional[DatabaseConfig]:
        """Get current database configuration"""
        return self._current_config
    
    def is_connected(self) -> bool:
        """Check if adapter is connected to a database"""
        return self.active_connection is not None and self._current_config is not None 