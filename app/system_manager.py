from typing import Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class DualSystemManager:
    def __init__(self, db_path: str = "Chinook_Sqlite.sqlite"):
        """
        Initialize systems. LangChain initialization will be skipped.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.autogen_orchestrator = None
        self.langchain_agent = None
        
        self._init_autogen_system()
        logger.info("LangChain system initialization is currently SKIPPED to focus on AutoGen.")

    def _init_autogen_system(self):
        """Initialize the existing AutoGen system."""
        try:
            from autogen_iterative import IterativeNL2SQLOrchestrator
            self.autogen_orchestrator = IterativeNL2SQLOrchestrator(self.db_path)
            logger.info("✅ AutoGen system initialized successfully by DualSystemManager")
        except Exception as e:
            logger.error(f"❌ DualSystemManager: Failed to initialize AutoGen system: {e}", exc_info=True)
            self.autogen_orchestrator = None

    def _init_langchain_system(self):
        """Initialize the new LangChain system. CURRENTLY DISABLED."""
        logger.warning("LangChain system initialization is SKIPPED in the current configuration.")
        self.langchain_agent = None
        return

    def process_query(self, query: str, system: str = "autogen", **kwargs) -> Dict[str, Any]:
        """
        Process query using specified system. LangChain will be ignored if chosen.
        """
        if system.lower() == "langchain":
            logger.warning("LangChain was requested, but it is currently disabled. Returning error.")
            return {
                'success': False,
                'error': 'LangChain system is currently disabled. Please use AutoGen.',
                'system': 'langchain_disabled',
                'query': query
            }
        # The check for self.autogen_orchestrator is handled in _process_with_autogen
        return self._process_with_autogen(query, **kwargs)

    def _process_with_autogen(self, query: str, **kwargs) -> Dict[str, Any]:
        logger.debug("DualSystemManager._process_with_autogen called.")
        if not self.autogen_orchestrator:
            return {
                'success': False, 'error': 'AutoGen system not available',
                'system': 'autogen', 'query': query
            }
        return self.autogen_orchestrator.process_query_iteratively(query, **kwargs)

    def compare_systems(self, query: str) -> Dict[str, Any]:
        """
        Run the same query on AutoGen. LangChain part will show as disabled.
        """
        autogen_result = self._process_with_autogen(query) # Changed from self.process_query
        langchain_result = { 
            'success': False,
            'error': 'LangChain system is currently disabled.',
            'system': 'langchain_disabled',
            'query': query
        }
        return {
            'query': query, 'autogen': autogen_result, 'langchain': langchain_result,
            'comparison': {'both_successful': False, 'sql_match': False, 'result_count_match': False }
        }

    def switch_database(self, new_db_path: str) -> Dict[str, Any]:
        """
        Switch to a different database and reinitialize AutoGen. LangChain remains disabled.
        """
        logger.info(f"DualSystemManager: Attempting to switch database to: {new_db_path}")
        try:
            validation = self.validate_database(new_db_path)
            if not validation['valid']:
                logger.error(f"Validation failed for new DB path {new_db_path}: {validation['error']}")
                return {'success': False, 'error': validation['error'], 'validation': validation}
            
            self.db_path = new_db_path
            logger.info(f"Re-initializing AutoGen system for new database: {self.db_path}")
            self._init_autogen_system() 
            
            self.langchain_agent = None # Added as per guide
            logger.info("LangChain remains disabled after database switch.") # Added as per guide

            logger.info(f"✅ Database switched to {self.db_path}. AutoGen re-initialized. LangChain remains disabled.") # Updated log
            return {'success': True, 'message': f'Database switched to {self.db_path}. AutoGen re-initialized. LangChain disabled.'}
        except Exception as e:
            logger.error(f"Database switch to {new_db_path} failed critically: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Database switch failed: {str(e)}', 'validation': {'valid': False, 'error': str(e)}}

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both systems."""
        return {
            'autogen': {
                'available': self.autogen_orchestrator is not None,
                'status': 'ready' if self.autogen_orchestrator else 'AutoGen not initialized'
            },
            'langchain': {
                'available': False, # Hardcode as false
                'status': 'disabled'
            },
            'database': self.db_path
        }

    def cleanup(self):
        logger.info("DualSystemManager cleanup called. Currently no specific cleanup for AutoGen here. LangChain is disabled.")
        pass # LangChain agent is None

    def validate_database(self, db_path: str) -> Dict[str, Any]:
        logger.info(f"DualSystemManager.validate_database for {db_path}")
        try:
            # Ensure db_path is absolute or correctly relative to PROJECT_ROOT if not absolute
            # This logic assumes db_path might be just a filename intended to be in PROJECT_ROOT
            if not os.path.isabs(db_path) and not os.path.exists(db_path):
                # This assumes system_manager.py is in app/ and db_path is relative to project root.
                # To get to project_root from app/system_manager.py: os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # However, simpler if db_path is consistently provided as absolute or relative to a known base.
                # For now, let's assume db_path needs to be checked relative to where DBs are stored (e.g., project root)
                # This path resolution should ideally be handled by the caller or consistently.
                # If this script (system_manager.py) is in app/, and db_path is "Chinook_Sqlite.sqlite",
                # we need to construct path from project root.
                project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Assuming app/system_manager.py
                candidate_path = os.path.join(project_root_path, db_path)
                if os.path.exists(candidate_path):
                    db_path_to_check = candidate_path
                    logger.info(f"Adjusted relative DB path to: {db_path_to_check}")
                else:
                    db_path_to_check = db_path # proceed with original if not found relative to root
            else:
                db_path_to_check = db_path

            if not os.path.exists(db_path_to_check):
                logger.warning(f"Database file not found at: {db_path_to_check}")
                return {'valid': False, 'error': f'Database file not found: {db_path_to_check}'}
            
            # Try to connect and get basic info
            # This part should ideally use your existing database.py or db_connector if they have validation logic
            # For simplicity here, direct sqlite3 connection for basic validation
            import sqlite3 # Local import for this method
            conn = sqlite3.connect(db_path_to_check)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return {
                'valid': True, 
                'database_path': db_path_to_check, # Return the path that was validated
                'total_tables': len(tables),
                'sample_tables': tables[:5], # Return first 5 table names as sample
                'size_mb': round(os.path.getsize(db_path_to_check) / (1024*1024), 2)
            }
        except Exception as e:
            logger.error(f"Database validation for {db_path} failed: {e}", exc_info=True)
            return {'valid': False, 'error': f'Validation failed: {str(e)}'}

    def get_available_databases(self) -> list:
        logger.info("DualSystemManager.get_available_databases called.")
        databases = []
        # Scan relative to where db_path is expected (e.g., project root)
        # This assumes system_manager.py is in 'app' directory.
        scan_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        try:
            for file in os.listdir(scan_dir):
                 if file.endswith(('.sqlite', '.db', '.sqlite3')):
                    full_path = os.path.join(scan_dir, file)
                    # Use the name relative to scan_dir (which should be project root) for consistency
                    databases.append({'name': file, 
                                      'display_name': os.path.splitext(file)[0].replace('_',' '), 
                                      'validation': self.validate_database(full_path)}) # Validate with full path
        except Exception as e:
            logger.error(f"Error scanning for databases in {scan_dir}: {e}")
        
        if not databases and os.path.exists(self.db_path):
             logger.warning(f"No databases found by scanning {scan_dir}, adding current default: {self.db_path}")
             databases.append({'name': os.path.basename(self.db_path), 
                               'display_name': os.path.splitext(os.path.basename(self.db_path))[0].replace('_',' '), 
                               'validation': self.validate_database(self.db_path)})
        elif not databases:
            logger.warning(f"No databases found by scanning {scan_dir} and default {self.db_path} also not found.")
        
        return databases 