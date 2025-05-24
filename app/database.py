#!/usr/bin/env python3
"""
Database utilities for schema representation and connection management.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_schema_representation(db_path: str) -> str:
    """
    Generate a comprehensive schema representation for the database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        String representation of the database schema
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        schema_parts = []
        schema_parts.append("=== DATABASE SCHEMA ===\n")
        
        for table_name, in tables:
            schema_parts.append(f"\n--- TABLE: {table_name} ---")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            schema_parts.append("Columns:")
            for col in columns:
                cid, name, data_type, not_null, default_value, pk = col
                pk_indicator = " (PRIMARY KEY)" if pk else ""
                not_null_indicator = " NOT NULL" if not_null else ""
                default_indicator = f" DEFAULT {default_value}" if default_value else ""
                schema_parts.append(f"  - {name}: {data_type}{pk_indicator}{not_null_indicator}{default_indicator}")
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                schema_parts.append("Foreign Keys:")
                for fk in foreign_keys:
                    id, seq, table, from_col, to_col, on_update, on_delete, match = fk
                    schema_parts.append(f"  - {from_col} -> {table}.{to_col}")
            
            # Get sample data (first 3 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_rows = cursor.fetchall()
            if sample_rows:
                schema_parts.append("Sample Data:")
                column_names = [description[0] for description in cursor.description]
                schema_parts.append(f"  Headers: {', '.join(column_names)}")
                for i, row in enumerate(sample_rows, 1):
                    row_str = ', '.join([str(val) if val is not None else 'NULL' for val in row])
                    schema_parts.append(f"  Row {i}: {row_str}")
        
        conn.close()
        
        schema_text = "\n".join(schema_parts)
        logger.info(f"Schema representation generated for {db_path}. Total length: {len(schema_text)} characters")
        return schema_text
        
    except Exception as e:
        error_msg = f"Failed to generate schema representation for {db_path}: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

def test_database_connection(db_path: str) -> dict:
    """
    Test database connection and return basic info.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Dictionary with connection test results
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        table_count = cursor.fetchone()[0]
        
        # Get database size
        import os
        db_size = os.path.getsize(db_path)
        
        conn.close()
        
        return {
            'success': True,
            'table_count': table_count,
            'size_bytes': db_size,
            'size_mb': round(db_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def execute_query(sql: str, db_path: str) -> list:
    """
    Execute a SQL query and return results.
    
    Args:
        sql: SQL query to execute
        db_path: Path to the SQLite database file
        
    Returns:
        List of tuples containing query results
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # For SELECT queries, fetch results
        if sql.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            # Also get column names
            if cursor.description:
                columns = [description[0] for description in cursor.description]
                # Return results with column information
                return {'columns': columns, 'rows': results}
            return results
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            return {'affected_rows': cursor.rowcount}
            
    except Exception as e:
        logger.error(f"Error executing query: {sql[:100]}... Error: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Test the schema representation
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        print("Testing database connection...")
        result = test_database_connection(db_path)
        print(f"Connection test: {result}")
        
        print("\nGenerating schema representation...")
        schema = get_schema_representation(db_path)
        print(schema)
    else:
        print("Usage: python database.py <path_to_database>")
