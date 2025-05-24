#!/usr/bin/env python3
"""
Super Safe version of app_dual.py with full web UI, global AI manager,
and enhanced resource protection.
"""
from flask import Flask, request, jsonify, render_template
import sqlite3
import json
import sys
import os
import psutil
import time
import threading
from contextlib import contextmanager
import logging
import traceback
import atexit # Ensures atexit is imported

# Determine project root and app directory for robust pathing
# __file__ is app/app_dual_super_safe.py
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Add app directory to sys.path for local module imports if needed
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
# Add project root to sys.path if system_manager or other modules are there directly
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from system_manager import DualSystemManager 
    # If autogen_iterative and natural_language_responder are in the same dir as system_manager (e.g. app/)
    # they should be importable by system_manager itself, or system_manager handles their paths.
except ImportError as e:
    logger = logging.getLogger(__name__) # Basic logger if full config not yet run
    logger.critical(f"Failed to import DualSystemManager: {e}. Ensure system_manager.py is in PYTHONPATH or app directory.", exc_info=True)
    sys.exit(1)

# Correct template folder path: if this script is in app/, templates/ is ../templates/
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
app = Flask(__name__, template_folder=TEMPLATES_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Global AI System Manager ---
# DEFAULT_DATABASE path needs to be relative to where DualSystemManager expects it,
# usually project root for top-level DB files.
DEFAULT_DATABASE = 'Chinook_Sqlite.sqlite' 
dual_manager = None
dual_manager_lock = threading.Lock()
current_database_path_global = DEFAULT_DATABASE # Tracks the DB for the UI and general app context

def get_dual_manager(db_path_to_load: str = None) -> DualSystemManager:
    global dual_manager, current_database_path_global
    
    # If a specific db_path is requested, that's the target.
    # Otherwise, use the current global context.
    target_db_for_manager = db_path_to_load or current_database_path_global

    # Ensure the database path used for DualSystemManager is resolvable from project root
    # If db_path_to_load is just a filename, assume it's in project root.
    if target_db_for_manager and not os.path.isabs(target_db_for_manager) and not os.path.exists(target_db_for_manager):
        candidate_path = os.path.join(PROJECT_ROOT, target_db_for_manager)
        if os.path.exists(candidate_path):
            target_db_for_manager = candidate_path
        else:
            logger.warning(f"Database file {target_db_for_manager} not found directly or in project root {PROJECT_ROOT}.")
            # Proceeding, DualSystemManager might handle it or fail.

    with dual_manager_lock:
        if dual_manager is None or (target_db_for_manager and dual_manager.db_path != target_db_for_manager):
            action = "Initializing" if dual_manager is None else "Switching"
            old_db_path_for_log = dual_manager.db_path if dual_manager else "None"
            logger.info(f"{action} global DualSystemManager. Old DB: {old_db_path_for_log}, New Target DB: {target_db_for_manager}")
            
            try:
                if dual_manager is not None and target_db_for_manager and dual_manager.db_path != target_db_for_manager:
                    # This is a switch operation
                    switch_result = dual_manager.switch_database(target_db_for_manager)
                    if not switch_result.get('success'):
                        logger.error(f"Failed to switch DualSystemManager DB from {old_db_path_for_log} to {target_db_for_manager}: {switch_result.get('error')}")
                        # If switch fails, dual_manager might be in previous state or inconsistent. Error should be raised by switch_database.
                        # Here, we might want to prevent current_database_path_global from changing if the switch in the manager failed.
                    else:
                        logger.info(f"Global DualSystemManager successfully switched to DB: {target_db_for_manager}")
                        current_database_path_global = target_db_for_manager # Critical: Update global context *after* successful switch in manager
                else: # dual_manager is None, initial creation
                    dual_manager = DualSystemManager(target_db_for_manager)
                    logger.info(f"Global DualSystemManager initialized successfully with DB: {target_db_for_manager}")
                    current_database_path_global = target_db_for_manager # Set after initial creation
            
            except Exception as e:
                logger.error(f"FATAL: Failed to {action.lower()} global DualSystemManager for DB {target_db_for_manager}: {e}", exc_info=True)
                dual_manager = None # Ensure manager is None if init/switch fails
                raise RuntimeError(f"Could not {action.lower()} AI Systems for DB {target_db_for_manager}: {e}")
    
    if dual_manager is None:
        # This means initialization failed critically and was caught above.
        raise RuntimeError("DualSystemManager is None after get_dual_manager call, initialization likely failed.")
    return dual_manager

class ResourceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.lock = threading.Lock()
        logger.info("ResourceMonitor initialized.")

    def check_resources(self, high_threshold=85, critical_threshold=95):
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if memory.percent > critical_threshold or cpu_percent > critical_threshold:
            logger.critical(f"CRITICAL RESOURCE USAGE! Memory: {memory.percent}%, CPU: {cpu_percent}%.")
            return False, "Critical resource usage. System unstable."
        if memory.percent > high_threshold or cpu_percent > high_threshold:
            logger.warning(f"High resource usage! Memory: {memory.percent}%, CPU: {cpu_percent}%. Performance may degrade.")
        return True, "Resources nominal."

    def increment_request(self):
        with self.lock:
            self.request_count += 1
            if self.request_count % 50 == 0:
                logger.info(f"Total requests served: {self.request_count}")
monitor = ResourceMonitor()

@app.after_request
def add_safety_headers(response):
    response.headers['Connection'] = 'close'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.before_request
def before_request_checks():
    if dual_manager is None and request.endpoint not in ['health_check', 'static']:
        try:
            logger.info(f"Attempting to implicitly initialize DualSystemManager via before_request_checks for DB: {current_database_path_global}")
            get_dual_manager(current_database_path_global)
            logger.info(f"DualSystemManager implicitly initialized successfully for DB: {current_database_path_global}")
        except RuntimeError as e:
            logger.error(f"Deferred AI Manager initialization failed in before_request: {e}", exc_info=True)
    
    if request.endpoint not in ['health_check', 'static']:
        ok, msg = monitor.check_resources()
        if not ok:
            return jsonify({'success': False, 'error': f"Server overloaded: {msg}"}), 503
        monitor.increment_request()

@app.route('/health')
def health_check():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    ai_systems_status_dict = "NOT_ATTEMPTED"
    current_db_for_ai_manager = "Unknown (Manager not queried)"
    manager_ready = False
    try:
        dm = get_dual_manager() # This ensures it's initialized or tries to init
        if dm: 
            ai_systems_status_dict = dm.get_system_status()
            current_db_for_ai_manager = dm.db_path
            manager_ready = True
        else:
            ai_systems_status_dict = {"error": "DualManager instance is None after get_dual_manager call."}
    except RuntimeError as e: 
        ai_systems_status_dict = {"error": f"AI System Manager initialization/access error: {str(e)}"}
    except Exception as e:
        ai_systems_status_dict = {"error": f"Unexpected error getting AI system status: {str(e)}"}
        logger.error("Health Check: Unexpected error during AI status fetch.", exc_info=True)

    return jsonify({
        'application_status': 'healthy',
        'uptime_seconds': round(time.time() - monitor.start_time, 2),
        'total_requests_served_by_worker': monitor.request_count,
        'memory_percent_system': mem.percent,
        'cpu_percent_system': cpu,
        'ai_manager_ready': manager_ready,
        'ai_systems_status': ai_systems_status_dict,
        'ai_manager_configured_db': current_db_for_ai_manager,
        'application_active_db_context': current_database_path_global
    })

@app.route('/')
def home():
    try:
        get_dual_manager(current_database_path_global) # Ensure manager is attempted to init
    except Exception:
        logger.warning("Home: Dual manager not ready for initial page load, UI may show AI systems as unavailable.", exc_info=True)
    return render_template('index_super_safe.html', initial_database_name=current_database_path_global)

@app.route('/status') # Deprecated
def get_status_deprecated():
    # This endpoint is confusing, /health is better
    logger.warning("Access to deprecated /status endpoint. Consider using /health for comprehensive status.")
    return health_check() # Just redirect to the new health check logic

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query_text = data.get('query')
    system_choice = data.get('system', 'autogen') # Default to autogen since LangChain is disabled

    if not query_text: return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    logger.info(f"Query: \"{query_text[:70]}...\" for system '{system_choice}' on DB: {current_database_path_global}")
    try:
        manager = get_dual_manager(current_database_path_global)
        start_time = time.monotonic()
        result = manager.process_query(query_text, system=system_choice)
        result['execution_time_ms'] = round((time.monotonic() - start_time) * 1000)
        logger.info(f"Query by {system_choice} completed. Success: {result.get('success')}, Time: {result['execution_time_ms']}ms")
        return jsonify(result)
    except RuntimeError as e: # Errors from get_dual_manager or AI system issues
        logger.error(f"RuntimeError during query processing with {system_choice}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'AI System Error: {str(e)}', 'query': query_text}), 503
    except Exception as e:
        logger.error(f"Unexpected error processing query with {system_choice}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Unexpected server error: {str(e)}', 'query': query_text}), 500

@app.route('/compare', methods=['POST'])
def handle_compare():
    # LangChain is disabled, so comparison isn't really meaningful but we provide a stub response
    logger.warning("Compare endpoint called, but LangChain is disabled. AutoGen will run.")
    data = request.json
    query_text = data.get('query')
    if not query_text: return jsonify({'autogen': {'success':False, 'error':'No query'}, 'langchain': {'success':False, 'error':'No query'}}), 400
    
    try:
        manager = get_dual_manager(current_database_path_global)
        autogen_result = manager.process_query(query_text, system='autogen')
        langchain_result = {'success': False, 'error': 'LangChain system is disabled in this configuration.', 'query': query_text, 'system': 'langchain_disabled'}
        
        return jsonify({
            'query': query_text,
            'autogen': autogen_result,
            'langchain': langchain_result,
            'comparison': {'both_successful': False}
        })
    except Exception as e:
        logger.error(f"Error during a compare request (AutoGen part): {e}", exc_info=True)
        err_str = str(e)
        return jsonify({'autogen': {'success': False, 'error': err_str}, 'langchain': {'success': False, 'error': 'LangChain disabled'}}), 500

@app.route('/databases')
def handle_list_databases():
    logger.info("Request to list available databases.")
    try:
        manager = get_dual_manager() 
        databases = manager.get_available_databases()
        return jsonify({'databases': databases})
    except Exception as e:
        logger.error(f"Error listing databases: {e}", exc_info=True)
        return jsonify({'databases': [], 'error': str(e)}), 500

@app.route('/validate-database', methods=['POST'])
def handle_validate_database():
    db_path = request.json.get('database')
    if not db_path: return jsonify({'valid': False, 'error': 'No database path provided for validation.'})
    logger.info(f"Validating database: {db_path}")
    try:
        manager = get_dual_manager() 
        validation_result = manager.validate_database(db_path)
        return jsonify(validation_result)
    except Exception as e:
        logger.error(f"Error validating database {db_path}: {e}", exc_info=True)
        return jsonify({'valid': False, 'error': str(e)})

@app.route('/switch-database', methods=['POST'])
def handle_switch_database():
    global current_database_path_global
    new_db_path = request.json.get('database')
    if not new_db_path: return jsonify({'success': False, 'error': 'No database path provided for switch.'})
    
    logger.info(f"Attempting to switch application context and AI systems to database: {new_db_path}")
    try:
        manager = get_dual_manager(new_db_path) # This triggers the switch in the global manager
        if manager.db_path == new_db_path:
            current_database_path_global = new_db_path # Update app context after manager confirms switch
            logger.info(f"Successfully switched app context and AI systems to database: {new_db_path}")
            return jsonify({'success': True, 'database': new_db_path})
        else:
            logger.error(f"Failed to confirm AI manager switch to {new_db_path}. Manager indicates DB: {manager.db_path}. Reverting app context.")
            # If manager didn't switch, global current_database_path_global was not updated by get_dual_manager
            return jsonify({'success': False, 'error': f'AI Manager failed to switch. Still on {manager.db_path}'})
    except RuntimeError as e:
        logger.error(f"RuntimeError during database switch to {new_db_path}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'AI System failed to switch: {str(e)}'})
    except Exception as e:
        logger.error(f"Unexpected error during database switch to {new_db_path}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Unexpected server error during switch: {str(e)}'})

def cleanup_app_resources():
    logger.info("Application shutting down. Cleaning up resources...")
    global dual_manager
    if dual_manager:
        try:
            dual_manager.cleanup()
            logger.info("DualSystemManager cleaned up.")
        except Exception as e:
            logger.error(f"Error cleaning up DualSystemManager: {e}", exc_info=True)

atexit.register(cleanup_app_resources)

if __name__ == '__main__':
    logger.info("🚀 Starting Super Safe Dual System API with Web UI")
    
    # Make sure templates directory exists (relative to project root)
    # Script is in app/, templates are in ../templates/
    # templates_dir = os.path.join(PROJECT_ROOT, 'templates') # Handled by Flask(template_folder=...)
    # if not os.path.exists(templates_dir):
    #     try: os.makedirs(templates_dir); logger.info(f"Created missing 'templates' directory at {templates_dir}")
    #     except OSError as e: logger.warning(f"Could not create 'templates' dir at {templates_dir}: {e}")
            
    try:
        get_dual_manager(DEFAULT_DATABASE) 
        logger.info(f"Initial Global AI Manager setup for {DEFAULT_DATABASE} attempted.")
    except RuntimeError as e:
        logger.critical(f"CRITICAL STARTUP FAILURE: Could not initialize AI System Manager with {DEFAULT_DATABASE}: {e}. Application will likely be non-functional.", exc_info=True)
    except Exception as e:
        logger.critical(f"CRITICAL STARTUP FAILURE: Unexpected error during initial AI setup: {e}.", exc_info=True)

    effective_db_for_ai = dual_manager.db_path if dual_manager else f"Manager not ready, intended: {DEFAULT_DATABASE}"
    logger.info(f"Flask starting. App DB Context: {current_database_path_global}. AI Manager DB: {effective_db_for_ai}")
    logger.info(f"🌐 Visit http://localhost:5002")
    
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True, use_reloader=False) 