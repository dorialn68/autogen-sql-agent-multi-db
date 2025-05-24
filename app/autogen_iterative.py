#!/usr/bin/env python3
import requests
import json
import re
import sys
import os
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
import logging

# Import the enhanced autonomous autocorrect agent
try:
    from autocorrect_agent_enhanced import EnhancedAutocorrectIntegration
    ENHANCED_AUTOCORRECT_AVAILABLE = True
except ImportError:
    ENHANCED_AUTOCORRECT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced Autocorrect Agent not available, using basic version")

logger = logging.getLogger(__name__) # Initialize logger at module level

class DatabaseManager:
    """Handle database schema and connection management."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_info = None
        # Ensure db_path is correctly resolved if it's relative
        if not os.path.isabs(self.db_path) and not os.path.exists(self.db_path):
            # Assuming this script (autogen_iterative.py) is in app/
            # and db_path is relative to project root (one level up from app/)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate_path = os.path.join(project_root, self.db_path)
            if os.path.exists(candidate_path):
                self.db_path = candidate_path
                logger.info(f"DatabaseManager: Resolved relative DB path to {self.db_path}")
            else:
                logger.warning(f"DatabaseManager: DB file {self.db_path} not found directly or at {candidate_path}")

    def get_schema(self) -> str:
        if self.schema_info is None:
            try:
                # Assuming database.py is in the same directory (app/)
                from database import get_schema_representation
                self.schema_info = get_schema_representation(self.db_path)
                logger.info(f"DATABASE MANAGER: Schema loaded for {self.db_path}. Length: {len(self.schema_info)}")
            except ImportError:
                logger.error("DATABASE MANAGER ERROR: Failed to import 'database.get_schema_representation'. Ensure database.py is in app/.")
                self.schema_info = "Error: Schema loading module not found."
            except Exception as e:
                logger.error(f"DATABASE MANAGER ERROR loading schema for {self.db_path}: {e}", exc_info=True)
                self.schema_info = f"Error loading schema: {e}"
        return self.schema_info

    def execute_query_safe(self, sql: str) -> Tuple[bool, Any]:
        try:
            from database import execute_query # Assuming database.py is in the same directory (app/)
            result = execute_query(sql, self.db_path)
            logger.info(f"DATABASE MANAGER: Query executed successfully on {self.db_path}. SQL: {sql[:100]}...")
            return True, result
        except ImportError:
            logger.error("DATABASE MANAGER ERROR: Failed to import 'database.execute_query'. Ensure database.py is in app/.")
            return False, "Error: Query execution module not found."
        except Exception as e:
            logger.error(f"DATABASE MANAGER ERROR executing query on {self.db_path}: {sql[:100]}... Error: {e}", exc_info=True)
            return False, str(e)

class QueryUnderstandingAgent:
    def analyze_query(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        logger.info(f"QUERY AGENT: Analyzing '{query}'")
        intent_type = "select"
        if any(word in query_lower for word in ['sum', 'total', 'amount', 'spent']): intent_type = "aggregation_sum"
        elif any(word in query_lower for word in ['count', 'how many', 'number']): intent_type = "aggregation_count"
        elif any(word in query_lower for word in ['all customers', 'all artists', 'all albums', 'list all', 'show all']): intent_type = "list_all"
        elif any(word in query_lower for word in ['lives in', 'from', 'located in']): intent_type = "location_filter"
        elif any(word in query_lower for word in ['most expensive', 'highest', 'top', 'maximum']): intent_type = "ranking"
        
        entity = "customer"
        if any(word in query_lower for word in ['artist', 'band']): entity = "artist"
        elif any(word in query_lower for word in ['album']): entity = "album"
        elif any(word in query_lower for word in ['track', 'song']): entity = "track"
        elif any(word in query_lower for word in ['invoice']): entity = "invoice"
        
        is_meta = any(p in query_lower for p in ['db name', 'database name', 'list tables', 'show tables'])
        if is_meta: intent_type = "meta_query"

        result = {
            "intent_type": intent_type,
            "entity": entity,
            "requires_join": intent_type in ["aggregation_sum", "aggregation_count", "ranking"], # Simplified
            "has_filter": "filter" in intent_type or any(w in query_lower for w in ['where', 'who', 'which', 'by'])
        }
        logger.info(f"QUERY AGENT: Intent: {result}")
        return result

class EntityExtractionAgent:
    def extract_entities(self, query: str) -> Dict[str, Any]:
        logger.info(f"ENTITY AGENT: Extracting from '{query}'")
        entities = {"person_names": [], "locations": {}, "artists": [], "attributes": [], "target_values": []}
        query_lower = query.lower()

        name_matches = re.findall(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', query) # Proper names
        for name in name_matches:
            if name.lower() not in ['customer', 'artist', 'album', 'track', 'invoice', 'genre', 'employee', 'select', 'from', 'where'] and len(name.split()) <= 2:
                entities["person_names"].append(name)
        
        # More specific for artists after "by"
        artist_by_match = re.search(r'by\s+([A-Z][A-Za-z\s\.&\-\']+)', query, re.IGNORECASE)
        if artist_by_match and artist_by_match.group(1).strip() not in entities["person_names"]:
            entities["artists"].append(artist_by_match.group(1).strip())
        
        # Values in quotes often are specific search terms
        quoted_values = re.findall(r"['\"](.*?)['\"]", query)
        entities["target_values"].extend(quoted_values)

        logger.info(f"ENTITY AGENT: Extracted: {entities}")
        return entities

class SQLValidationAgent:
    def validate_sql(self, sql: str, schema: str) -> Dict[str, Any]:
        logger.info(f"VALIDATION AGENT: Validating SQL: {sql[:100]}...")
        res = {"is_valid": True, "syntax_errors": [], "schema_errors": [], "suggestions": []}
        if not sql.strip().endswith(';'): res["suggestions"].append("Add semicolon at end of SQL.")
        # Basic check for SELECT statement (can be expanded)
        if not sql.upper().strip().startswith("SELECT"):
            res["is_valid"] = False
            res["syntax_errors"].append("Query does not start with SELECT.")
        logger.info(f"VALIDATION AGENT: Result: {res}")
        return res

class ErrorAnalysisAgent:
    def analyze_error(self, sql: str, error_msg: str, schema: str) -> Dict[str, Any]:
        logger.info(f"ERROR ANALYSIS AGENT: Analyzing error: {error_msg} for SQL: {sql[:100]}...")
        analysis = {"error_type": "unknown", "suggested_fixes": [], "original_error_message": error_msg}
        error_lower = error_msg.lower()
        if "no such column" in error_lower: analysis["error_type"] = "missing_column"
        elif "no such table" in error_lower: analysis["error_type"] = "missing_table"
        elif "syntax error" in error_lower: analysis["error_type"] = "syntax_error"
        elif "ambiguous column" in error_lower: analysis["error_type"] = "ambiguous_column"
        logger.info(f"ERROR ANALYSIS AGENT: Analysis: {analysis}")
        return analysis

class SQLRefinementAgent:
    def __init__(self):
        self.model = "qwen2.5-coder:7b" 
        self.ollama_url = "http://localhost:11434/api/generate"

    def _clean_sql_response(self, response: str) -> str:
        logger.debug(f"Cleaning SQL response: {response[:100]}...")
        for pattern in ["```sql", "```", "SQL:", "Query:", "SQLQuery:"]:
            response = response.replace(pattern, "")
        response = response.strip()
        
        # Remove any existing semicolons first, then add exactly one
        response = response.rstrip(';').strip()
        if response:
            response += ';'
        
        return response

    def refine_sql(self, sql: str, error_analysis: Dict, schema: str, intent: Dict, entities: Dict) -> str:
        logger.info(f"REFINEMENT AGENT (AI): Refining SQL for error: {error_analysis.get('error_type', 'unknown')}")
        error_analysis_str = json.dumps(error_analysis, indent=2)
        intent_str = json.dumps(intent, indent=2)
        entities_str = json.dumps(entities, indent=2)

        prompt_template = (
            'The following SQL query failed:\n'
            '--- FAILED SQL ---\n{failed_sql}\n---\n\n'
            'Error Analysis:\n{error_analysis_json}\n\n'
            'Original User Query Intent:\n{intent_json}\n\n'
            'Extracted Entities from User Query:\n{entities_json}\n\n'
            'Database Schema (SQLite):\n{schema}\n\n'
            'INSTRUCTIONS:\n'
            '1. Analyze the FAILED SQL, Error Analysis, Intent, Entities, and Schema.\n'
            '2. Produce a CORRECTED SQLite query that resolves the error AND fulfills the user\'s intent.\n'
            '3. Pay attention to table/column names, aliases, JOINs, aggregates, and syntax.\n'
            '4. Return ONLY the corrected SQL query, ending with a semicolon. No explanations.\n'
            '5. Ensure the query is syntactically correct and executes without errors.\n'
            'Corrected SQLQuery:'
        )
        context = prompt_template.format(failed_sql=sql, error_analysis_json=error_analysis_str, intent_json=intent_str, entities_json=entities_str, schema=schema)
        logger.debug(f"Refinement Agent AI Context:\n{context}")
        
        try:
            response = requests.post(self.ollama_url, json={
                'model': self.model, 'prompt': context, 'stream': False,
                'options': {'temperature': 0.2, 'max_tokens': 300, 'num_ctx': 4096}
            }, timeout=40)
            if response.status_code == 200:
                refined_sql = self._clean_sql_response(response.json().get('response', '').strip())
                logger.info(f"REFINEMENT AGENT (AI): Refined SQL: {refined_sql}")
                return refined_sql if refined_sql else sql
            else:
                logger.error(f"REFINEMENT AGENT (AI): AI refinement failed status {response.status_code}: {response.text}")
        except requests.Timeout:
            logger.error("REFINEMENT AGENT (AI): Timeout during AI refinement.")
        except Exception as e:
            logger.error(f"REFINEMENT AGENT (AI): Exception: {e}", exc_info=True)
        return sql # Return original on any error/timeout

class AutocorrectAgent:
    """Agent that handles typos and misspellings using fuzzy matching"""
    
    def __init__(self, db_manager: 'DatabaseManager'):
        self.db_manager = db_manager
        logger.info("AUTOCORRECT AGENT: Initialized")
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return AutocorrectAgent.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def find_similar_values(self, value: str, table: str, column: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Find similar values in the database using fuzzy matching"""
        try:
            # Query distinct values from the specified column
            sql = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL;"
            success, result = self.db_manager.execute_query_safe(sql)
            
            if not success:
                logger.error(f"AUTOCORRECT AGENT: Failed to query {table}.{column} for fuzzy matching")
                return []
            
            similar_values = []
            value_lower = value.lower()
            
            for row in result.get('rows', []):
                db_value = str(row[0])
                db_value_lower = db_value.lower()
                
                # Calculate similarity score (1.0 - normalized distance)
                max_len = max(len(value_lower), len(db_value_lower))
                if max_len == 0:
                    continue
                    
                distance = self.levenshtein_distance(value_lower, db_value_lower)
                similarity = 1.0 - (distance / max_len)
                
                if similarity >= threshold:
                    similar_values.append((db_value, similarity))
            
            # Sort by similarity (highest first)
            similar_values.sort(key=lambda x: x[1], reverse=True)
            return similar_values[:5]  # Return top 5 matches
            
        except Exception as e:
            logger.error(f"AUTOCORRECT AGENT: Error in find_similar_values: {e}", exc_info=True)
            return []
    
    def correct_entities(self, entities: Dict[str, Any], intent: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Correct typos in extracted entities using fuzzy matching"""
        corrected_entities = entities.copy()
        corrections_made = []
        
        # Correct person names based on Customer table
        if entities.get("person_names") and intent.get("entity") == "customer":
            corrected_names = []
            for name in entities["person_names"]:
                # Check FirstName column
                similar_first = self.find_similar_values(name, "Customer", "FirstName", threshold=0.7)
                if similar_first:
                    best_match, score = similar_first[0]
                    if score < 1.0:  # It's a correction, not exact match
                        logger.info(f"AUTOCORRECT AGENT: Correcting '{name}' to '{best_match}' (score: {score:.2f})")
                        corrections_made.append(f"'{name}' → '{best_match}'")
                        corrected_names.append(best_match)
                    else:
                        corrected_names.append(name)
                else:
                    # Check LastName column as fallback
                    similar_last = self.find_similar_values(name, "Customer", "LastName", threshold=0.7)
                    if similar_last:
                        best_match, score = similar_last[0]
                        logger.info(f"AUTOCORRECT AGENT: Found '{name}' as last name '{best_match}' (score: {score:.2f})")
                        corrected_names.append(name)  # Keep original, but note it might be a last name
                    else:
                        corrected_names.append(name)
            
            corrected_entities["person_names"] = corrected_names
        
        # Correct artist names
        if entities.get("artists") and intent.get("entity") == "artist":
            corrected_artists = []
            for artist in entities["artists"]:
                similar = self.find_similar_values(artist, "Artist", "Name", threshold=0.7)
                if similar:
                    best_match, score = similar[0]
                    if score < 1.0:
                        logger.info(f"AUTOCORRECT AGENT: Correcting artist '{artist}' to '{best_match}' (score: {score:.2f})")
                        corrections_made.append(f"'{artist}' → '{best_match}'")
                        corrected_artists.append(best_match)
                    else:
                        corrected_artists.append(artist)
                else:
                    corrected_artists.append(artist)
            
            corrected_entities["artists"] = corrected_artists
        
        # Store correction info for reference
        corrected_entities["_corrections"] = corrections_made
        
        if corrections_made:
            logger.info(f"AUTOCORRECT AGENT: Made {len(corrections_made)} corrections: {corrections_made}")
        
        return corrected_entities
    
    def suggest_query_corrections(self, query: str) -> Dict[str, Any]:
        """Suggest corrections for common misspellings in the query itself"""
        corrections = {}
        query_lower = query.lower()
        
        # Common misspellings mapping
        common_typos = {
            'costumer': 'customer',
            'costumers': 'customers',
            'custmer': 'customer',
            'custmers': 'customers',
            'ablum': 'album',
            'ablums': 'albums',
            'atrist': 'artist',
            'atrists': 'artists',
            'invioce': 'invoice',
            'invioces': 'invoices',
        }
        
        # Check for common typos
        for typo, correction in common_typos.items():
            if typo in query_lower:
                corrections[typo] = correction
                logger.info(f"AUTOCORRECT AGENT: Detected typo '{typo}' → suggest '{correction}'")
        
        return corrections

class IterativeNL2SQLOrchestrator:
    def __init__(self, db_path: str, max_iterations: int = 3):
        self.db_manager = DatabaseManager(db_path)
        self.query_agent = QueryUnderstandingAgent()
        self.entity_agent = EntityExtractionAgent()
        self.validation_agent = SQLValidationAgent()
        self.error_agent = ErrorAnalysisAgent()
        self.refinement_agent = SQLRefinementAgent()
        
        # Use enhanced autocorrect if available, otherwise fall back to basic
        if ENHANCED_AUTOCORRECT_AVAILABLE:
            self.autocorrect_agent = EnhancedAutocorrectIntegration(self.db_manager)
            logger.info("ITERATIVE ORCHESTRATOR: Using Enhanced Autonomous Autocorrect Agent")
        else:
            self.autocorrect_agent = AutocorrectAgent(self.db_manager)
            logger.info("ITERATIVE ORCHESTRATOR: Using Basic Autocorrect Agent")
            
        self.max_iterations = max_iterations
        logger.info("ITERATIVE ORCHESTRATOR: All agents initialized.")

    def _clean_sql_response(self, response: str) -> str: # Moved here for access by _generate_with_ai too
        logger.debug(f"Cleaning SQL response: {response[:100]}...")
        for pattern in ["```sql", "```", "SQL:", "Query:", "SQLQuery:"]:
            response = response.replace(pattern, "")
        response = response.strip()
        
        # Remove any existing semicolons first, then add exactly one
        response = response.rstrip(';').strip()
        if response:
            response += ';'
        
        return response

    def _generate_with_ai(self, query: str, intent: Dict, entities: Dict, schema: str, custom_prompt_override: Optional[str] = None) -> str:
        if custom_prompt_override:
            context = custom_prompt_override
            logger.info(f"AUTOGEN SQL AI: Using custom prompt for: '{query}'.")
        else:
            logger.info(f"AUTOGEN SQL AI: Generating SQL for query: '{query}' with intent: {intent.get('intent_type')}")
            intent_json_str = json.dumps(intent, indent=2)
            
            # Remove _corrections key before sending to AI
            entities_for_ai = entities.copy()
            entities_for_ai.pop('_corrections', None)
            entities_json_str = json.dumps(entities_for_ai, indent=2)
            
            # Log if corrections were made
            if entities.get('_corrections'):
                logger.info(f"AUTOGEN SQL AI: Using corrected entities: {entities.get('_corrections')}")
            
            default_prompt_template = (
                'You are an expert SQLite query writer.\n'
                'Given the natural language query, user\'s intent, extracted entities, and the database schema, generate an accurate and efficient SQLite query.\n\n'
                'Natural Language Query: {query}\n'
                'User Intent Analysis: {intent_json}\n'
                'Extracted Entities (may include autocorrected names): {entities_json}\n\n'
                'Database Schema (SQLite):\n{schema}\n\n'
                'Key Instructions for SQLite Query Generation:\n'
                '1.  Understand the Goal. 2. Identify Tables. 3. Specify JOIN Conditions accurately. 4. Use Table Aliases. 5. Apply WHERE clauses correctly. 6. Use Aggregations (COUNT, SUM, etc.) with GROUP BY. 7. Use ORDER BY and LIMIT. 8. Match schema case for names. 9. Prioritize correctness and simplicity. 10. Return ONLY SQL query, ending with a semicolon.\n'
                '11. IMPORTANT: Use the exact entity names provided in "Extracted Entities" - these have been verified against the database.\n\n'
                'Example (artists and album counts):\nNL: Show me all artists and how many albums each has.\nSQLQuery: SELECT ar.Name, COUNT(al.AlbumId) AS TotalAlbums FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId GROUP BY ar.ArtistId, ar.Name ORDER BY TotalAlbums DESC;\n\n'
                'Now, generate the SQL query for the provided Natural Language Query.\nSQLQuery:'
            )
            context = default_prompt_template.format(query=query, intent_json=intent_json_str, entities_json=entities_json_str, schema=schema)
        
        logger.debug(f"AUTOGEN SQL AI Context for Ollama:\n{context[:500]}...")
        try:
            response = requests.post(self.refinement_agent.ollama_url, json={
                'model': self.refinement_agent.model, 'prompt': context, 'stream': False,
                'options': {'temperature': 0.1, 'max_tokens': 300, 'num_ctx': 4096}
            }, timeout=35)
            if response.status_code == 200:
                sql_response = self._clean_sql_response(response.json().get('response', '').strip())
                logger.info(f"AUTOGEN SQL AI: Generated SQL: {sql_response}")
                return sql_response if sql_response else ("" if custom_prompt_override else "SELECT 1 -- AI no response;")
            else:
                logger.error(f"AUTOGEN SQL AI: Ollama request failed {response.status_code}: {response.text}")
                return "" if custom_prompt_override else "SELECT 1 -- Ollama HTTP error;"
        except requests.Timeout:
            logger.error(f"AUTOGEN SQL AI: Timeout to Ollama.")
            return "" if custom_prompt_override else "SELECT 1 -- Ollama timeout;"
        except Exception as e:
            logger.error(f"AUTOGEN SQL AI: Exception: {e}", exc_info=True)
            return "" if custom_prompt_override else "SELECT 1 -- AI system error;"

    def _handle_ambiguous_name_query(self, original_nl_query: str, intent: Dict, entities: Dict, schema: str, original_sql_for_log: str) -> Tuple[str, bool]:
        logger.warning(f"ORCHESTRATOR: Ambiguous name query returned 0 results. Original SQL: {original_sql_for_log}. Names: {entities.get('person_names')}")
        person_names = entities.get('person_names', [])
        if not person_names or len(person_names) < 2: return original_sql_for_log, False

        example_name_1 = person_names[0].replace("'", "''")
        example_name_2 = person_names[1].replace("'", "''") if len(person_names) > 1 else "AnotherName"
        
        correction_prompt_template = (
            'You are an expert SQLite query writer tasked with helping a user who provided multiple names that might refer to separate individuals.\n'
            'Original User Query: "{original_nl_query}"\n'
            'The system extracted these names (already autocorrected if needed): {person_names_list_str}\n'
            'An earlier query like `SELECT ... WHERE FirstName = \'{example_name_1}\' AND (LastName = \'{example_name_2}\' OR FirstName = \'{example_name_2}\')` (or similar logic for a single person) returned 0 results.\n'
            'It is likely the user wants to find customers where EITHER the FirstName is one of the listed names, OR perhaps LastName matches one of them if they are looking for different people.\n\n'
            'Database Schema (SQLite):\n{schema}\n\n'
            'Task: Generate a SQLite query to find customers where the FirstName is IN the list of names: {person_names_list_str}.\n'
            'Alternatively, if that seems too broad, consider a query where FirstName matches one name OR FirstName matches another name from the list.\n'
            'Select relevant customer details: FirstName, LastName, City, State, Country, Address. Use table alias \'c\' for Customer.\n'
            'IMPORTANT: Use the exact names provided - they have been verified against the database.\n'
            'Return ONLY the SQL query, ending with a semicolon.\n\n'
            'Example for names [\'Alice\', \'Bob\'] (looking for either person):\n'
            'SQLQuery: SELECT c.FirstName, c.LastName, c.Address, c.City, c.State, c.Country FROM Customer c WHERE c.FirstName IN (\'Alice\', \'Bob\');\n\n'
            'SQLQuery:'
        )
        correction_prompt_context = correction_prompt_template.format(
            original_nl_query=original_nl_query,
            person_names_list_str=str(person_names),
            example_name_1=example_name_1,
            example_name_2=example_name_2,
            schema=schema
        )
        logger.info("ORCHESTRATOR (Name Correction): Calling AI for OR-based name query.")
        logger.debug(f"Name Correction Prompt:\n{correction_prompt_context[:500]}...")

        corrected_sql = self._generate_with_ai(original_nl_query, intent, entities, schema, custom_prompt_override=correction_prompt_context)
        
        if corrected_sql: # Check if AI returned anything useful
            logger.info(f"ORCHESTRATOR (Name Correction): Auto-corrected SQL: {corrected_sql}")
            return corrected_sql, True
        else:
            logger.warning("ORCHESTRATOR (Name Correction): Failed to generate auto-corrected SQL.")
            return original_sql_for_log, False

    def _generate_initial_sql(self, query: str, intent: Dict, entities: Dict, schema: str) -> str:
        logger.info("ORCHESTRATOR: Generating initial SQL.")
        # Simplified rule-based generation for common, simple cases
        # This section can be expanded with more rules from your original, working AutoGen logic
        if intent["intent_type"] == "meta_query":
            if any(word in query.lower() for word in ['db name', 'database name']):
                return "SELECT name, type FROM sqlite_master WHERE type='table' ORDER BY name;" # More informative for DB name
            elif any(word in query.lower() for word in ['tables', 'list tables', 'show tables']):
                return "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        
        # Add more rules from your previously working AutoGen if they were effective
        # For example:
        # if intent["intent_type"] == "list_all" and intent["entity"] == "customer":
        #     return "SELECT CustomerId, FirstName, LastName, Email FROM Customer;"

        logger.info("ORCHESTRATOR: No simple rule matched, using AI for initial SQL generation.")
        return self._generate_with_ai(query, intent, entities, schema)

    def _fix_validation_issues(self, sql: str, validation: Dict) -> str:
        logger.warning(f"Attempting to fix validation issues for SQL: {sql} Issues: {validation}")
        if not sql.strip().endswith(';'): sql = sql.strip() + ';'
        # Add more rule-based validation fixes if possible
        return sql

    def process_query_iteratively(self, nl_query: str) -> Dict[str, Any]:
        logger.info(f"\n{'='*60}")
        logger.info(f"ORCHESTRATOR: Starting iterative processing for: '{nl_query}'")
        logger.info(f"{'='*60}")
        
        intent = self.query_agent.analyze_query(nl_query)
        entities = self.entity_agent.extract_entities(nl_query)
        
        # Apply autocorrection to entities
        original_entities = entities.copy()
        if ENHANCED_AUTOCORRECT_AVAILABLE and isinstance(self.autocorrect_agent, EnhancedAutocorrectIntegration):
            # Enhanced version with query parameter
            entities = self.autocorrect_agent.correct_entities(entities, intent, nl_query)
        else:
            # Basic version without query parameter
            entities = self.autocorrect_agent.correct_entities(entities, intent)
        
        # Check if any corrections were made
        corrections_made = entities.get("_corrections", [])
        if corrections_made:
            logger.info(f"ORCHESTRATOR: Autocorrect applied corrections: {corrections_made}")
        
        schema = self.db_manager.get_schema()
        if "Error loading schema" in schema or "Schema loading module not found" in schema:
             return {"success": False, "error": "Critical: Database schema could not be loaded.", "sql": "", "history": []}

        sql = self._generate_initial_sql(nl_query, intent, entities, schema)
        logger.info(f"ORCHESTRATOR: Initial SQL generated: {sql}")

        iteration = 0
        history = []
        attempted_name_autocorrection = False
        result_or_error = "No execution attempt yet."
        success = False

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n--- ORCHESTRATOR: ITERATION {iteration} ---")
            current_iteration_log = {'iteration': iteration, 'sql_attempted': sql}
            history.append(current_iteration_log)
            
            if not sql or sql.startswith("SELECT 1 --") or not sql.strip(): # Check for invalid/placeholder SQL
                logger.warning(f"ORCHESTRATOR: Invalid or placeholder SQL generated: '{sql}'. Aborting iteration.")
                current_iteration_log['error'] = "Invalid or placeholder SQL generated by AI."
                break # Exit loop if SQL is clearly bad

            validation = self.validation_agent.validate_sql(sql, schema)
            current_iteration_log['validation'] = validation
            if not validation["is_valid"]:
                logger.warning(f"ORCHESTRATOR: SQL Validation failed: {validation}")
                sql = self._fix_validation_issues(sql, validation)
                current_iteration_log['validation_fix_attempted'] = sql
                continue 
            
            success, result_or_error = self.db_manager.execute_query_safe(sql)
            current_iteration_log['execution_success'] = success
            current_iteration_log['execution_result'] = result_or_error
            
            if success:
                if (not attempted_name_autocorrection and 
                    intent.get('entity') == 'customer' and 
                    len(entities.get('person_names', [])) > 1 and 
                    isinstance(result_or_error, dict) and 
                    result_or_error.get('rows') and len(result_or_error['rows']) == 0 and 
                    any(name_part.lower() in sql.lower() for name_part in entities.get('person_names',[]))):
                    
                    logger.info("ORCHESTRATOR: Zero results on multi-name customer query. Attempting auto-correction.")
                    corrected_sql_attempt, was_corrected = self._handle_ambiguous_name_query(nl_query, intent, entities, schema, sql)
                    attempted_name_autocorrection = True 
                    current_iteration_log['name_autocorrection_attempted'] = True
                    current_iteration_log['name_autocorrection_output_sql'] = corrected_sql_attempt

                    if was_corrected and corrected_sql_attempt and corrected_sql_attempt != sql:
                        sql = corrected_sql_attempt
                        logger.info("ORCHESTRATOR: Retrying with auto-corrected name query.")
                        continue 
                    else:
                        logger.info("ORCHESTRATOR: Name auto-correction did not yield a new query or failed. Proceeding with 0 results.")
            
                logger.info(f"ORCHESTRATOR: ✅ SUCCESS on iteration {iteration} with SQL: {sql}")
                
                # Create response with autocorrection info
                response = {
                    "success": True, "sql": sql, "result": result_or_error,
                    "iterations": iteration, "history": history
                }
                
                # Add autocorrection info if any corrections were made
                if corrections_made:
                    response["autocorrections"] = corrections_made
                    response["message"] = f"✨ Autocorrect fixed: {', '.join(corrections_made)}"
                
                return response
            else: 
                logger.error(f"ORCHESTRATOR: ❌ SQL Execution failed on iteration {iteration}: {result_or_error}")
                error_analysis = self.error_agent.analyze_error(sql, str(result_or_error), schema)
                current_iteration_log['error_analysis'] = error_analysis
                
                refined_sql_attempt = self.refinement_agent.refine_sql(sql, error_analysis, schema, intent, entities)
                current_iteration_log['refinement_agent_output_sql'] = refined_sql_attempt
                if refined_sql_attempt == sql:
                    logger.warning("ORCHESTRATOR: SQL Refinement Agent did not change the query. Breaking loop.")
                    break 
                sql = refined_sql_attempt
                logger.info(f"ORCHESTRATOR: Refined SQL by ErrorAnalysis/RefinementAgent: {sql}")
        
        logger.error(f"ORCHESTRATOR: ❌ Failed after {self.max_iterations} iterations. Last SQL: {sql}")
        return {
            "success": False, "sql": sql, "error": str(result_or_error),
            "history": history
        }

# Main translation function (compatible with existing interface)
def translate_nl_to_sql_autogen(nl_query: str, db_path: str) -> str:
    logger.info(f"AUTOGEN_ITERATIVE: Received NL query: '{nl_query}' for DB: {db_path}")
    try:
        orchestrator = IterativeNL2SQLOrchestrator(db_path, max_iterations=3)
        result = orchestrator.process_query_iteratively(nl_query)
        
        if result["success"]:
            logger.info(f"AUTOGEN_ITERATIVE: ✅ Success. SQL: {result['sql']}")
            return result["sql"]
        else:
            logger.error(f"AUTOGEN_ITERATIVE: ❌ Failure. Last SQL: {result['sql']}, Error: {result['error']}")
            return result.get('sql', "SELECT 1 -- AutoGen iterative refinement failed;") # Return last attempted SQL or fallback
    except Exception as e:
        logger.error(f"AUTOGEN_ITERATIVE: SYSTEM ERROR during translation: {e}", exc_info=True)
        return "SELECT 1 -- AutoGen system error;" 