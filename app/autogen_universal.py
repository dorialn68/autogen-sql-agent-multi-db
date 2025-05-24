#!/usr/bin/env python3
"""
Universal AutoGen SQL Agent - Database Agnostic
Works with any database schema (SQLite, PostgreSQL, Vertica, MySQL)
Handles complex analytical queries with multi-table joins
"""
import os
import json
import logging
import sqlite3
import re
import requests
from typing import Dict, Any, List, Tuple, Optional
from database_adapter import UnifiedDatabaseAdapter
from database_config import DatabaseConfigManager

logger = logging.getLogger(__name__)

class UniversalDatabaseManager:
    """Database manager that works with any database type through unified adapter"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self.adapter = UnifiedDatabaseAdapter(config_manager)
        self.schema_cache = {}
        
    def connect(self, config_name: Optional[str] = None) -> bool:
        """Connect to database using configuration"""
        success, message = self.adapter.connect(config_name)
        if success:
            logger.info(f"UNIVERSAL DB: Connected successfully - {message}")
            return True
        else:
            logger.error(f"UNIVERSAL DB: Connection failed - {message}")
            return False
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information"""
        return self.adapter.get_schema_info()
    
    def get_schema_text(self) -> str:
        """Get schema as formatted text for AI"""
        return self.adapter.generate_schema_representation()
    
    def execute_query(self, sql: str) -> Tuple[bool, Any]:
        """Execute SQL query safely"""
        try:
            success, result = self.adapter.execute_query(sql)
            if success:
                logger.info(f"UNIVERSAL DB: Query executed successfully")
                return True, result
            else:
                logger.error(f"UNIVERSAL DB: Query failed - {result}")
                return False, result
        except Exception as e:
            logger.error(f"UNIVERSAL DB: Query execution error - {e}")
            return False, str(e)
    
    def analyze_schema_patterns(self) -> Dict[str, Any]:
        """Analyze schema to understand data patterns and relationships"""
        schema_info = self.get_schema_info()
        patterns = {
            "entity_tables": [],
            "junction_tables": [],
            "lookup_tables": [],
            "name_columns": {},
            "id_columns": {},
            "date_columns": {},
            "relationships": []
        }
        
        if not schema_info or "tables" not in schema_info:
            return patterns
        
        # Analyze each table
        for table_name, table_info in schema_info["tables"].items():
            columns = table_info.get("columns", [])
            
            # Find name columns (likely person/entity names)
            name_cols = [col["name"] for col in columns 
                        if any(keyword in col["name"].lower() 
                              for keyword in ["name", "first", "last", "title", "description"])]
            if name_cols:
                patterns["name_columns"][table_name] = name_cols
            
            # Find ID columns
            id_cols = [col["name"] for col in columns 
                      if col["name"].lower().endswith("id") or col.get("primary_key")]
            patterns["id_columns"][table_name] = id_cols
            
            # Find date columns
            date_cols = [col["name"] for col in columns 
                        if any(keyword in col["name"].lower() 
                              for keyword in ["date", "time", "created", "updated"])
                        or any(dtype in col["type"].lower() 
                              for dtype in ["date", "time", "timestamp"])]
            if date_cols:
                patterns["date_columns"][table_name] = date_cols
            
            # Classify table types
            if len(columns) <= 3 and len(id_cols) >= 2:
                patterns["junction_tables"].append(table_name)
            elif len(columns) <= 5 and any("name" in col.lower() for col in name_cols):
                patterns["lookup_tables"].append(table_name)
            else:
                patterns["entity_tables"].append(table_name)
        
        # Extract relationships from foreign keys
        for table_name, table_info in schema_info["tables"].items():
            for fk in table_info.get("foreign_keys", []):
                patterns["relationships"].append({
                    "from_table": table_name,
                    "from_column": fk["from"],
                    "to_table": fk["to_table"],
                    "to_column": fk["to_column"]
                })
        
        logger.info(f"UNIVERSAL DB: Schema analysis complete - {len(patterns['entity_tables'])} entities, "
                   f"{len(patterns['relationships'])} relationships")
        return patterns

class UniversalQueryAgent:
    """Query understanding agent that works with any database schema"""
    
    def __init__(self, db_manager: UniversalDatabaseManager):
        self.db_manager = db_manager
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query intent and complexity"""
        query_lower = query.lower()
        
        # Determine query complexity
        complexity = self._assess_complexity(query)
        
        # Determine intent type
        intent_type = "data_query"  # Default
        if any(word in query_lower for word in ['how many', 'count', 'total', 'number of']):
            intent_type = "count_query"
        elif any(word in query_lower for word in ['list', 'show all', 'display', 'get all']):
            intent_type = "list_query"
        elif any(word in query_lower for word in ['where', 'who', 'which', 'what']):
            intent_type = "search_query"
        elif any(word in query_lower for word in ['purchased', 'bought', 'sold', 'ordered']):
            intent_type = "transaction_query"
        elif any(word in query_lower for word in ['other', 'also', 'similar', 'same']):
            intent_type = "recommendation_query"
        elif any(word in query_lower for word in ['top', 'best', 'most', 'highest', 'lowest']):
            intent_type = "ranking_query"
        
        # Detect analytical patterns
        analytical_patterns = []
        if "other" in query_lower and ("purchased" in query_lower or "bought" in query_lower):
            analytical_patterns.append("cross_customer_analysis")
        if any(word in query_lower for word in ['also', 'additionally', 'furthermore']):
            analytical_patterns.append("extended_analysis")
        if re.search(r'\b(and|then|after|before)\b', query_lower):
            analytical_patterns.append("sequential_analysis")
        
        return {
            "intent_type": intent_type,
            "complexity": complexity,
            "analytical_patterns": analytical_patterns,
            "requires_joins": complexity in ["medium", "high"],
            "requires_subqueries": complexity == "high",
            "original_query": query
        }
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity based on linguistic patterns"""
        complexity_indicators = {
            "high": [
                r'\b(other|also)\b.*\b(purchased|bought)\b',
                r'\b(customers?\s+who)\b.*\b(also|additionally)\b',
                r'\b(items?\s+that)\b.*\b(other|different)\b',
                r'\b(people\s+who)\b.*\b(same|similar)\b'
            ],
            "medium": [
                r'\b(purchased|bought|ordered)\b',
                r'\b(top|best|most|highest)\b',
                r'\b(where|who|which)\b.*\b(and|or)\b',
                r'\b(group\s+by|order\s+by)\b'
            ]
        }
        
        query_lower = query.lower()
        
        # Check for high complexity patterns
        for pattern in complexity_indicators["high"]:
            if re.search(pattern, query_lower):
                return "high"
        
        # Check for medium complexity patterns
        for pattern in complexity_indicators["medium"]:
            if re.search(pattern, query_lower):
                return "medium"
        
        return "low"

class UniversalEntityAgent:
    """Entity extraction agent that works with any database schema"""
    
    def __init__(self, db_manager: UniversalDatabaseManager):
        self.db_manager = db_manager
        self.schema_patterns = None
        
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query using dynamic schema analysis"""
        if not self.schema_patterns:
            self.schema_patterns = self.db_manager.analyze_schema_patterns()
        
        entities = {
            "person_names": [],
            "entity_references": [],
            "values": [],
            "filters": {},
            "table_references": []
        }
        
        # Extract potential person names (proper nouns)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        potential_names = re.findall(name_pattern, query)
        
        # Filter out common words and SQL keywords
        sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'GROUP', 'BY', 'LIMIT', 'COUNT', 'SUM'}
        common_words = {'The', 'And', 'Or', 'But', 'For', 'With', 'Items', 'Customer', 'Customers'}
        
        for name in potential_names:
            if name not in sql_keywords and name not in common_words and len(name) > 2:
                entities["person_names"].append(name)
        
        # Extract quoted values
        quoted_values = re.findall(r"['\"]([^'\"]+)['\"]", query)
        entities["values"].extend(quoted_values)
        
        # Detect table references based on schema
        query_lower = query.lower()
        for table_name in self.schema_patterns.get("entity_tables", []):
            # Check for singular/plural variations
            if (table_name.lower() in query_lower or 
                table_name.lower().rstrip('s') in query_lower or 
                (table_name.lower() + 's') in query_lower):
                entities["table_references"].append(table_name)
        
        logger.info(f"UNIVERSAL ENTITY: Extracted entities: {entities}")
        return entities

class UniversalSQLGenerator:
    """AI-powered SQL generator that works with any database schema"""
    
    def __init__(self, db_manager: UniversalDatabaseManager):
        self.db_manager = db_manager
        self.model = "qwen2.5-coder:7b"
        self.ollama_url = "http://localhost:11434/api/generate"
    
    def generate_sql(self, query: str, intent: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """Generate SQL using AI with dynamic schema understanding"""
        schema_text = self.db_manager.get_schema_text()
        schema_patterns = self.db_manager.analyze_schema_patterns()
        
        # Create enhanced prompt based on query complexity
        if intent.get("complexity") == "high":
            prompt = self._create_complex_query_prompt(query, intent, entities, schema_text, schema_patterns)
        else:
            prompt = self._create_standard_query_prompt(query, intent, entities, schema_text, schema_patterns)
        
        return self._call_ai_for_sql(prompt)
    
    def _create_complex_query_prompt(self, query: str, intent: Dict, entities: Dict, 
                                   schema_text: str, patterns: Dict) -> str:
        """Create prompt for complex analytical queries"""
        return f"""You are an expert SQL analyst specializing in complex cross-table analytics.

USER QUERY: "{query}"

ANALYSIS:
- Query Type: {intent.get('intent_type')}
- Complexity: {intent.get('complexity')}
- Analytical Patterns: {intent.get('analytical_patterns', [])}
- Detected Entities: {entities.get('person_names', [])}

DATABASE SCHEMA:
{schema_text}

SCHEMA INSIGHTS:
- Entity Tables: {patterns.get('entity_tables', [])}
- Junction Tables: {patterns.get('junction_tables', [])}
- Name Columns by Table: {patterns.get('name_columns', {})}
- Key Relationships: {patterns.get('relationships', [])[:5]}

COMPLEX QUERY STRATEGY:
For queries involving "other customers who purchased the same items":
1. Find the target person's purchases (use appropriate name columns)
2. Find items purchased by that person
3. Find other customers who bought those same items  
4. Find additional items purchased by those other customers
5. Use appropriate JOINs and subqueries for multi-step analysis

SQL REQUIREMENTS:
- Use the exact database schema provided
- Handle person name matching across appropriate name columns
- Use proper JOINs for multi-table relationships
- Include subqueries for complex analytical logic
- Return clear, readable results with meaningful column names
- Add LIMIT clause for large result sets (LIMIT 50)

Generate the complete SQL query:"""

    def _create_standard_query_prompt(self, query: str, intent: Dict, entities: Dict, 
                                    schema_text: str, patterns: Dict) -> str:
        """Create prompt for standard queries"""
        return f"""You are an expert SQL query generator that works with any database schema.

USER QUERY: "{query}"

QUERY ANALYSIS:
- Intent: {intent.get('intent_type')}
- Complexity: {intent.get('complexity')}
- Entities: {entities.get('person_names', [])}
- Table References: {entities.get('table_references', [])}

DATABASE SCHEMA:
{schema_text}

SCHEMA PATTERNS:
- Main Entity Tables: {patterns.get('entity_tables', [])}
- Name Columns: {patterns.get('name_columns', {})}
- Relationships: {patterns.get('relationships', [])[:3]}

INSTRUCTIONS:
1. Analyze the user's intent and required data
2. Identify the correct tables and columns from the schema
3. Use appropriate JOINs based on foreign key relationships
4. Handle person name matching using available name columns
5. Generate syntactically correct SQL for the database type
6. Include proper WHERE clauses, GROUP BY, ORDER BY as needed
7. Add meaningful column aliases for readability

Generate the SQL query:"""

    def _call_ai_for_sql(self, prompt: str) -> str:
        """Call Ollama AI to generate SQL"""
        try:
            response = requests.post(self.ollama_url, json={
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'max_tokens': 500,
                    'num_ctx': 6000
                }
            }, timeout=45)
            
            if response.status_code == 200:
                sql = response.json().get('response', '').strip()
                return self._clean_sql(sql)
            else:
                logger.error(f"UNIVERSAL SQL: AI request failed {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"UNIVERSAL SQL: AI error - {e}")
            return ""
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and format SQL response"""
        # Remove markdown formatting
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove common prefixes
        sql = re.sub(r'^(SQL Query:|SQLQuery:|Query:)\s*', '', sql, flags=re.IGNORECASE)
        
        # Clean up whitespace
        sql = sql.strip()
        
        # Ensure proper semicolon
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql

class UniversalAutocorrectAgent:
    """Universal autocorrect agent that works with any schema"""
    
    def __init__(self, db_manager: UniversalDatabaseManager):
        self.db_manager = db_manager
        self.schema_patterns = None
    
    def correct_entities(self, entities: Dict[str, Any], intent: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Correct entities using dynamic schema knowledge"""
        if not self.schema_patterns:
            self.schema_patterns = self.db_manager.analyze_schema_patterns()
        
        corrected = entities.copy()
        corrections = []
        
        # Correct person names using available name columns
        if entities.get("person_names"):
            corrected_names = []
            for name in entities["person_names"]:
                best_match = self._find_best_name_match(name)
                if best_match and best_match != name:
                    corrections.append(f"'{name}' → '{best_match}'")
                    corrected_names.append(best_match)
                else:
                    corrected_names.append(name)
            corrected["person_names"] = corrected_names
        
        corrected["_corrections"] = corrections
        
        if corrections:
            logger.info(f"UNIVERSAL AUTOCORRECT: Applied corrections: {corrections}")
        
        return corrected
    
    def _find_best_name_match(self, name: str) -> Optional[str]:
        """Find best matching name across all name columns"""
        best_match = None
        best_score = 0.0
        
        # Search across all tables with name columns
        for table_name, name_columns in self.schema_patterns.get("name_columns", {}).items():
            for column in name_columns:
                try:
                    # Query distinct values from name column
                    sql = f"SELECT DISTINCT {column} FROM {table_name} WHERE {column} IS NOT NULL LIMIT 100;"
                    success, result = self.db_manager.execute_query(sql)
                    
                    if success and result.get("rows"):
                        for row in result["rows"]:
                            db_value = str(row[0])
                            score = self._calculate_similarity(name.lower(), db_value.lower())
                            if score > best_score and score >= 0.7:
                                best_score = score
                                best_match = db_value
                except Exception as e:
                    logger.warning(f"UNIVERSAL AUTOCORRECT: Error checking {table_name}.{column}: {e}")
                    continue
        
        return best_match
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using Levenshtein distance"""
        if not s1 or not s2:
            return 0.0
        
        # Simple Levenshtein distance calculation
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        distances = range(len(s2) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        
        max_len = max(len(s1), len(s2))
        return (max_len - distances[-1]) / max_len if max_len > 0 else 0.0

class UniversalNL2SQLOrchestrator:
    """Main orchestrator that handles any database type"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self.db_manager = UniversalDatabaseManager(config_manager)
        
        # Initialize agents
        self.query_agent = UniversalQueryAgent(self.db_manager)
        self.entity_agent = UniversalEntityAgent(self.db_manager)
        self.sql_generator = UniversalSQLGenerator(self.db_manager)
        self.autocorrect_agent = UniversalAutocorrectAgent(self.db_manager)
        
        logger.info("UNIVERSAL ORCHESTRATOR: Initialized for multi-database support")
    
    def connect_to_database(self, config_name: Optional[str] = None) -> bool:
        """Connect to specified database configuration"""
        return self.db_manager.connect(config_name)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query with any database"""
        try:
            logger.info(f"UNIVERSAL ORCHESTRATOR: Processing query: '{query}'")
            
            # Ensure database connection
            if not self.db_manager.adapter.is_connected():
                if not self.connect_to_database():
                    return {"success": False, "error": "Database connection failed"}
            
            # Analyze query
            intent = self.query_agent.analyze_query(query)
            entities = self.entity_agent.extract_entities(query)
            
            # Apply autocorrection
            entities = self.autocorrect_agent.correct_entities(entities, intent, query)
            
            # Generate SQL
            sql = self.sql_generator.generate_sql(query, intent, entities)
            
            if not sql:
                return {"success": False, "error": "Failed to generate SQL query"}
            
            # Execute query
            success, result = self.db_manager.execute_query(sql)
            
            # Prepare response
            response = {
                "success": success,
                "sql": sql,
                "intent": intent,
                "entities": entities
            }
            
            if success:
                response["result"] = result
                if entities.get("_corrections"):
                    response["autocorrections"] = entities["_corrections"]
                    response["message"] = f"✨ Autocorrect applied: {', '.join(entities['_corrections'])}"
            else:
                response["error"] = result
            
            return response
            
        except Exception as e:
            logger.error(f"UNIVERSAL ORCHESTRATOR: Processing error - {e}", exc_info=True)
            return {"success": False, "error": f"Processing error: {str(e)}"}

# Convenience function for backward compatibility
def translate_nl_to_sql_universal(nl_query: str, config_manager: DatabaseConfigManager) -> Dict[str, Any]:
    """Process NL query with universal database support"""
    orchestrator = UniversalNL2SQLOrchestrator(config_manager)
    return orchestrator.process_query(nl_query) 