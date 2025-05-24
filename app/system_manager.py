from typing import Dict, Any, Optional, List
import logging
import os
import json
import time
from database_config import DatabaseConfigManager
from autogen_universal import UniversalNL2SQLOrchestrator

logger = logging.getLogger(__name__)

class DualSystemManager:
    """Enhanced system manager with universal multi-database support"""
    
    def __init__(self, initial_db_path: str = None):
        self.config_manager = DatabaseConfigManager()
        self.universal_orchestrator = UniversalNL2SQLOrchestrator(self.config_manager)
        
        # Initialize with database
        if initial_db_path:
            self.db_path = initial_db_path
            # Add SQLite config if it doesn't exist
            if initial_db_path.endswith('.sqlite'):
                if not any(config['name'] == 'Current_SQLite' 
                          for config in self.config_manager.list_configs()):
                    from database_config import DatabaseConfig
                    from datetime import datetime
                    sqlite_config = DatabaseConfig(
                        name="Current_SQLite",
                        db_type="sqlite",
                        connection_type="local",
                        database=initial_db_path,
                        created_at=datetime.now().isoformat(),
                        is_active=True
                    )
                    self.config_manager.configs['Current_SQLite'] = sqlite_config
                    self.config_manager._save_configs()
                
                # Connect to the database
                self.universal_orchestrator.connect_to_database('Current_SQLite')
        else:
            # Use active configuration
            active_config = self.config_manager.get_active_config()
            if active_config:
                self.db_path = active_config.database
                self.universal_orchestrator.connect_to_database()
            else:
                self.db_path = "Chinook_Sqlite.sqlite"  # Fallback
        
        logger.info(f"DUAL SYSTEM MANAGER: Initialized with universal support for: {self.db_path}")

    def process_query(self, query: str, system: str = "autogen") -> Dict[str, Any]:
        """Process query using universal orchestrator"""
        try:
            logger.info(f"DUAL SYSTEM: Processing query with {system}: '{query[:50]}...'")
            
            if system == "autogen":
                # Use universal orchestrator
                result = self.universal_orchestrator.process_query(query)
                
                # Add classification info for compatibility
                result["classification"] = {
                    "classification": result.get("intent", {}).get("intent_type", "data_query"),
                    "confidence": 0.9 if result.get("success") else 0.5
                }
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"System '{system}' not supported. Use 'autogen' for universal database support.",
                    "query": query
                }
        
        except Exception as e:
            logger.error(f"DUAL SYSTEM: Error processing query: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"System error: {str(e)}",
                "query": query
            }

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all systems"""
        # Test database connection
        db_connected = self.universal_orchestrator.db_manager.adapter.is_connected()
        
        return {
            "autogen": {
                "available": True,
                "status": "Ready - Universal Multi-DB Support",
                "database_connected": db_connected,
                "current_database": self.db_path
            },
            "langchain": {
                "available": False,
                "status": "Disabled - Using Universal AutoGen"
            }
        }

    def switch_database(self, new_db_path: str) -> Dict[str, Any]:
        """Switch to a different database"""
        try:
            logger.info(f"DUAL SYSTEM: Switching database from {self.db_path} to {new_db_path}")
            
            # Add new database configuration if needed
            config_name = f"DB_{os.path.basename(new_db_path)}"
            
            if new_db_path.endswith('.sqlite'):
                # Add SQLite configuration
                from database_config import DatabaseConfig
                from datetime import datetime
                new_config = DatabaseConfig(
                    name=config_name,
                    db_type="sqlite",
                    connection_type="local",
                    database=new_db_path,
                    created_at=datetime.now().isoformat(),
                    is_active=True
                )
                self.config_manager.configs[config_name] = new_config
                self.config_manager.set_active_config(config_name)
                self.config_manager._save_configs()
            
            # Connect to new database
            success = self.universal_orchestrator.connect_to_database(config_name)
            
            if success:
                self.db_path = new_db_path
                logger.info(f"DUAL SYSTEM: Successfully switched to {new_db_path}")
                return {"success": True, "database": new_db_path}
            else:
                logger.error(f"DUAL SYSTEM: Failed to connect to {new_db_path}")
                return {"success": False, "error": f"Failed to connect to {new_db_path}"}
        
        except Exception as e:
            logger.error(f"DUAL SYSTEM: Error switching database: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def get_available_databases(self) -> List[Dict[str, Any]]:
        """Get list of available database configurations"""
        databases = []
        
        # Get configured databases
        for config in self.config_manager.list_configs():
            databases.append({
                "name": config["name"],
                "display_name": f"{config['db_type'].upper()}: {config['database']}",
                "type": config["db_type"],
                "database": config["database"],
                "is_active": config["is_active"]
            })
        
        # Add any SQLite files in current directory
        for file in os.listdir('.'):
            if file.endswith('.sqlite') or file.endswith('.db'):
                # Check if already in configs
                if not any(db['database'] == file for db in databases):
                    databases.append({
                        "name": f"local_{file}",
                        "display_name": f"SQLite: {file}",
                        "type": "sqlite",
                        "database": file,
                        "is_active": False
                    })
        
        return databases

    def validate_database(self, db_path: str) -> Dict[str, Any]:
        """Validate database connection and get metadata"""
        try:
            # Test connection using config manager
            if db_path.endswith('.sqlite'):
                # Create temporary config for validation
                temp_config_name = f"temp_validate_{int(time.time())}"
                from database_config import DatabaseConfig
                from datetime import datetime
                
                temp_config = DatabaseConfig(
                    name=temp_config_name,
                    db_type="sqlite",
                    connection_type="local",
                    database=db_path,
                    created_at=datetime.now().isoformat()
                )
                
                self.config_manager.configs[temp_config_name] = temp_config
                
                # Test connection
                success, message, metadata = self.config_manager.test_connection(temp_config_name)
                
                # Clean up temp config
                del self.config_manager.configs[temp_config_name]
                
                if success:
                    return {
                        "valid": True,
                        "database_path": db_path,
                        "total_tables": metadata.get("table_count", 0),
                        "size_mb": metadata.get("database_size_mb", 0),
                        "sample_tables": [{"name": table, "rows": "N/A"} 
                                        for table in metadata.get("tables", [])[:3]]
                    }
                else:
                    return {"valid": False, "error": message}
            else:
                return {"valid": False, "error": "Unsupported database type for validation"}
                
        except Exception as e:
            logger.error(f"DUAL SYSTEM: Database validation error: {e}")
            return {"valid": False, "error": str(e)}

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self.universal_orchestrator, 'db_manager'):
                self.universal_orchestrator.db_manager.adapter.close()
            logger.info("DUAL SYSTEM: Cleanup completed")
        except Exception as e:
            logger.error(f"DUAL SYSTEM: Cleanup error: {e}") 