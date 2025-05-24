#!/usr/bin/env python3
"""
Enhanced Autonomous Autocorrect Agent with self-learning capabilities
"""
import json
import os
import sqlite3
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import re
from difflib import SequenceMatcher
import pickle

logger = logging.getLogger(__name__)

class AutonomousAutocorrectAgent:
    """
    An autonomous agent that learns from the database schema and data
    to build its own knowledge base for intelligent autocorrection
    """
    
    def __init__(self, db_path: str, knowledge_base_dir: str = "autocorrect_knowledge"):
        self.db_path = db_path
        self.knowledge_base_dir = knowledge_base_dir
        self.knowledge_base = {}
        self.correction_history = []
        
        # Create knowledge base directory if it doesn't exist
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        
        # File paths for persistence
        self.kb_file = os.path.join(self.knowledge_base_dir, "knowledge_base.json")
        self.history_file = os.path.join(self.knowledge_base_dir, "correction_history.json")
        self.cache_file = os.path.join(self.knowledge_base_dir, "db_cache.pkl")
        
        # Initialize or load existing knowledge base
        self._initialize_knowledge_base()
        
        # Load correction history if exists
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.correction_history = json.load(f)
                logger.info(f"AUTONOMOUS AUTOCORRECT: Loaded {len(self.correction_history)} correction history entries")
            except Exception as e:
                logger.warning(f"AUTONOMOUS AUTOCORRECT: Could not load correction history: {e}")
        
        logger.info(f"AUTONOMOUS AUTOCORRECT: Initialized with DB: {db_path}")
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base from existing files or build new one"""
        if os.path.exists(self.kb_file):
            self._load_knowledge_base()
            logger.info("AUTONOMOUS AUTOCORRECT: Loaded existing knowledge base")
        else:
            logger.info("AUTONOMOUS AUTOCORRECT: Building new knowledge base from database")
            self._build_knowledge_base()
            self._save_knowledge_base()
    
    def _build_knowledge_base(self):
        """Build comprehensive knowledge base from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            self.knowledge_base = {
                "schema": {},
                "data_patterns": {},
                "common_values": {},
                "relationships": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "db_path": self.db_path,
                    "total_tables": len(tables)
                }
            }
            
            for table_name, in tables:
                logger.info(f"AUTONOMOUS AUTOCORRECT: Analyzing table '{table_name}'")
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                self.knowledge_base["schema"][table_name] = {
                    "columns": {},
                    "primary_keys": [],
                    "foreign_keys": []
                }
                
                for col in columns:
                    cid, name, data_type, not_null, default_value, pk = col
                    self.knowledge_base["schema"][table_name]["columns"][name] = {
                        "type": data_type,
                        "not_null": bool(not_null),
                        "default": default_value,
                        "is_pk": bool(pk)
                    }
                    if pk:
                        self.knowledge_base["schema"][table_name]["primary_keys"].append(name)
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table_name});")
                foreign_keys = cursor.fetchall()
                for fk in foreign_keys:
                    id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                    self.knowledge_base["schema"][table_name]["foreign_keys"].append({
                        "from": from_col,
                        "to_table": ref_table,
                        "to_column": to_col
                    })
                
                # Analyze data patterns and common values
                self._analyze_table_data(cursor, table_name)
            
            # Analyze relationships between tables
            self._analyze_relationships()
            
            conn.close()
            
            logger.info(f"AUTONOMOUS AUTOCORRECT: Knowledge base built successfully. "
                       f"Analyzed {len(tables)} tables")
            
        except Exception as e:
            logger.error(f"AUTONOMOUS AUTOCORRECT: Error building knowledge base: {e}", exc_info=True)
    
    def _analyze_table_data(self, cursor, table_name: str):
        """Analyze data patterns in a table"""
        self.knowledge_base["data_patterns"][table_name] = {}
        self.knowledge_base["common_values"][table_name] = {}
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        
        self.knowledge_base["data_patterns"][table_name]["row_count"] = row_count
        
        # For each column, analyze patterns and collect common values
        for col_name, col_info in self.knowledge_base["schema"][table_name]["columns"].items():
            # Skip analysis for very large tables to avoid memory issues
            if row_count > 10000:
                sample_limit = 1000
            else:
                sample_limit = row_count
            
            # Get distinct values for text columns
            if 'TEXT' in col_info["type"] or 'VARCHAR' in col_info["type"]:
                cursor.execute(f"""
                    SELECT DISTINCT {col_name}, COUNT(*) as freq 
                    FROM {table_name} 
                    WHERE {col_name} IS NOT NULL 
                    GROUP BY {col_name}
                    ORDER BY freq DESC
                    LIMIT 100;
                """)
                
                values = cursor.fetchall()
                if values:
                    self.knowledge_base["common_values"][table_name][col_name] = [
                        {"value": val, "frequency": freq} for val, freq in values
                    ]
                    
                    # Analyze patterns (e.g., email format, phone format)
                    self._detect_column_patterns(table_name, col_name, [v[0] for v in values[:20]])
    
    def _detect_column_patterns(self, table_name: str, column_name: str, sample_values: List[str]):
        """Detect patterns in column data"""
        patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "phone": r'^[\+\-\(\)\s\d]+$',
            "url": r'^https?://|^www\.',
            "postal_code": r'^\d{5}(-\d{4})?$|^[A-Z]\d[A-Z]\s?\d[A-Z]\d$',
            "date": r'^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$'
        }
        
        detected_patterns = []
        for pattern_name, pattern_regex in patterns.items():
            matches = sum(1 for val in sample_values if re.match(pattern_regex, str(val)))
            if matches > len(sample_values) * 0.5:  # If >50% match
                detected_patterns.append(pattern_name)
        
        if detected_patterns:
            if table_name not in self.knowledge_base["data_patterns"]:
                self.knowledge_base["data_patterns"][table_name] = {}
            self.knowledge_base["data_patterns"][table_name][column_name] = {
                "patterns": detected_patterns
            }
    
    def _analyze_relationships(self):
        """Analyze relationships between tables based on foreign keys and naming patterns"""
        relationships = []
        
        # Extract from foreign keys
        for table, schema in self.knowledge_base["schema"].items():
            for fk in schema.get("foreign_keys", []):
                relationships.append({
                    "from_table": table,
                    "from_column": fk["from"],
                    "to_table": fk["to_table"],
                    "to_column": fk["to_column"],
                    "type": "foreign_key"
                })
        
        # Detect implicit relationships based on naming patterns
        # (e.g., CustomerId in Invoice table likely refers to Customer.CustomerId)
        for table1, schema1 in self.knowledge_base["schema"].items():
            for col1 in schema1["columns"]:
                for table2, schema2 in self.knowledge_base["schema"].items():
                    if table1 != table2:
                        for col2 in schema2["columns"]:
                            if (col1.lower().endswith('id') and 
                                col2.lower().endswith('id') and
                                table2.lower() in col1.lower()):
                                relationships.append({
                                    "from_table": table1,
                                    "from_column": col1,
                                    "to_table": table2,
                                    "to_column": col2,
                                    "type": "implicit",
                                    "confidence": 0.8
                                })
        
        self.knowledge_base["relationships"] = relationships
    
    def _save_knowledge_base(self):
        """Save knowledge base to file"""
        try:
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
            logger.info(f"AUTONOMOUS AUTOCORRECT: Knowledge base saved to {self.kb_file}")
        except Exception as e:
            logger.error(f"AUTONOMOUS AUTOCORRECT: Error saving knowledge base: {e}")
    
    def _load_knowledge_base(self):
        """Load knowledge base from file"""
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            logger.info(f"AUTONOMOUS AUTOCORRECT: Knowledge base loaded from {self.kb_file}")
        except Exception as e:
            logger.error(f"AUTONOMOUS AUTOCORRECT: Error loading knowledge base: {e}")
            self._build_knowledge_base()
    
    def refresh_knowledge_base(self):
        """Refresh the knowledge base with latest data from database"""
        logger.info("AUTONOMOUS AUTOCORRECT: Refreshing knowledge base...")
        self._build_knowledge_base()
        self._save_knowledge_base()
    
    def find_best_match(self, value: str, table: str, column: str, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
        """
        Find best match for a value using the knowledge base
        Uses multiple strategies for matching
        """
        if table not in self.knowledge_base["common_values"]:
            logger.warning(f"AUTONOMOUS AUTOCORRECT: Table '{table}' not in knowledge base")
            return None
        
        if column not in self.knowledge_base["common_values"][table]:
            logger.warning(f"AUTONOMOUS AUTOCORRECT: Column '{column}' not in knowledge base for table '{table}'")
            return None
        
        best_match = None
        best_score = 0
        value_lower = value.lower()
        
        # Strategy 1: Exact match (case-insensitive)
        for item in self.knowledge_base["common_values"][table][column]:
            db_value = item["value"]
            if db_value.lower() == value_lower:
                return (db_value, 1.0)
        
        # Strategy 2: Fuzzy matching with multiple algorithms
        for item in self.knowledge_base["common_values"][table][column]:
            db_value = item["value"]
            
            # Levenshtein-based similarity
            seq_score = SequenceMatcher(None, value_lower, db_value.lower()).ratio()
            
            # Prefix matching bonus
            prefix_bonus = 0.1 if db_value.lower().startswith(value_lower[:3]) else 0
            
            # Frequency-based bonus (more common values get slight preference)
            freq_bonus = min(0.05, item["frequency"] / 1000.0)
            
            # Combined score
            total_score = seq_score + prefix_bonus + freq_bonus
            
            if total_score > best_score and total_score >= threshold:
                best_score = total_score
                best_match = (db_value, min(total_score, 1.0))
        
        return best_match
    
    def suggest_corrections(self, query: str, entities: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest corrections for all entities in a query using the knowledge base
        """
        suggestions = {
            "corrections": [],
            "warnings": [],
            "confidence": 1.0
        }
        
        # Correct table/entity names if misspelled
        if intent.get("entity"):
            entity = intent["entity"]
            if entity not in self.knowledge_base["schema"]:
                # Find closest table name
                best_table = self._find_closest_table(entity)
                if best_table:
                    suggestions["corrections"].append({
                        "type": "entity",
                        "original": entity,
                        "suggested": best_table[0],
                        "confidence": best_table[1]
                    })
        
        # Correct person names
        if entities.get("person_names") and intent.get("entity") == "customer":
            for name in entities["person_names"]:
                # Try FirstName
                match = self.find_best_match(name, "Customer", "FirstName")
                if match:
                    if match[0] != name:
                        suggestions["corrections"].append({
                            "type": "person_name",
                            "original": name,
                            "suggested": match[0],
                            "confidence": match[1],
                            "column": "FirstName"
                        })
                else:
                    # Try LastName
                    match = self.find_best_match(name, "Customer", "LastName")
                    if match:
                        suggestions["corrections"].append({
                            "type": "person_name",
                            "original": name,
                            "suggested": match[0],
                            "confidence": match[1],
                            "column": "LastName"
                        })
                    else:
                        suggestions["warnings"].append(f"No match found for name '{name}'")
        
        # Log corrections to history
        if suggestions["corrections"]:
            self._log_correction(query, suggestions)
        
        return suggestions
    
    def _find_closest_table(self, name: str) -> Optional[Tuple[str, float]]:
        """Find closest table name in schema"""
        best_match = None
        best_score = 0
        name_lower = name.lower()
        
        for table_name in self.knowledge_base["schema"]:
            score = SequenceMatcher(None, name_lower, table_name.lower()).ratio()
            if score > best_score and score >= 0.7:
                best_score = score
                best_match = (table_name, score)
        
        return best_match
    
    def _log_correction(self, query: str, suggestions: Dict[str, Any]):
        """Log corrections for learning and analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "suggestions": suggestions
        }
        
        self.correction_history.append(log_entry)
        
        # Save history periodically
        if len(self.correction_history) % 10 == 0:
            self._save_correction_history()
    
    def _save_correction_history(self):
        """Save correction history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.correction_history, f, indent=2)
        except Exception as e:
            logger.error(f"AUTONOMOUS AUTOCORRECT: Error saving history: {e}")
    
    def analyze_correction_patterns(self) -> Dict[str, Any]:
        """Analyze correction patterns to improve future corrections"""
        patterns = {
            "total_corrections": 0,
            "common_mistakes": {},
            "success_rate": 0,
            "recommendations": []
        }
        
        if not self.correction_history:
            patterns["recommendations"].append("No correction history available yet")
            return patterns
        
        patterns["total_corrections"] = len(self.correction_history)
        
        # Analyze common mistakes
        mistakes = {}
        for entry in self.correction_history:
            for correction in entry["suggestions"]["corrections"]:
                key = f"{correction['original']} -> {correction['suggested']}"
                mistakes[key] = mistakes.get(key, 0) + 1
        
        # Sort by frequency
        patterns["common_mistakes"] = dict(sorted(mistakes.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Generate recommendations
        if patterns["common_mistakes"]:
            patterns["recommendations"].append(
                "Consider adding common misspellings to a custom dictionary for faster correction"
            )
        
        return patterns
    
    def generate_report(self) -> str:
        """Generate a comprehensive report of the knowledge base and corrections"""
        report = []
        report.append("=" * 70)
        report.append("AUTONOMOUS AUTOCORRECT AGENT - KNOWLEDGE BASE REPORT")
        report.append("=" * 70)
        report.append(f"Generated at: {datetime.now().isoformat()}")
        report.append(f"Database: {self.db_path}")
        report.append("")
        
        # Schema summary
        report.append("SCHEMA SUMMARY:")
        report.append("-" * 50)
        for table, info in self.knowledge_base["schema"].items():
            report.append(f"\nTable: {table}")
            report.append(f"  Columns: {len(info['columns'])}")
            report.append(f"  Primary Keys: {', '.join(info['primary_keys'])}")
            report.append(f"  Foreign Keys: {len(info['foreign_keys'])}")
            
            # Show sample values
            if table in self.knowledge_base["common_values"]:
                report.append("  Sample Values:")
                for col, values in list(self.knowledge_base["common_values"][table].items())[:3]:
                    if values:
                        sample = values[0]["value"]
                        report.append(f"    {col}: '{sample}' (and {len(values)-1} more)")
        
        # Relationships
        report.append("\nRELATIONSHIPS:")
        report.append("-" * 50)
        for rel in self.knowledge_base["relationships"][:10]:
            report.append(f"{rel['from_table']}.{rel['from_column']} -> "
                         f"{rel['to_table']}.{rel['to_column']} ({rel['type']})")
        
        # Correction patterns
        patterns = self.analyze_correction_patterns()
        report.append("\nCORRECTION PATTERNS:")
        report.append("-" * 50)
        report.append(f"Total Corrections: {patterns['total_corrections']}")
        if patterns["common_mistakes"]:
            report.append("Common Mistakes:")
            for mistake, count in list(patterns["common_mistakes"].items())[:5]:
                report.append(f"  {mistake}: {count} times")
        
        return "\n".join(report)


class EnhancedAutocorrectIntegration:
    """Integration layer for the autonomous autocorrect agent"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.agent = AutonomousAutocorrectAgent(db_manager.db_path)
        logger.info("ENHANCED AUTOCORRECT: Integration initialized")
    
    def correct_entities(self, entities: Dict[str, Any], intent: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Correct entities using the autonomous agent"""
        # Get suggestions from the autonomous agent
        suggestions = self.agent.suggest_corrections(query, entities, intent)
        
        # Apply corrections
        corrected_entities = entities.copy()
        corrections_made = []
        
        for correction in suggestions["corrections"]:
            if correction["type"] == "person_name":
                # Update the person names list
                if "person_names" in corrected_entities:
                    for i, name in enumerate(corrected_entities["person_names"]):
                        if name == correction["original"]:
                            corrected_entities["person_names"][i] = correction["suggested"]
                            corrections_made.append(
                                f"{correction['original']} → {correction['suggested']} "
                                f"(confidence: {correction['confidence']:.2f})"
                            )
            
            elif correction["type"] == "entity":
                # This would update the intent, but we return it separately
                corrections_made.append(
                    f"Entity '{correction['original']}' → '{correction['suggested']}' "
                    f"(confidence: {correction['confidence']:.2f})"
                )
        
        # Add metadata
        corrected_entities["_corrections"] = corrections_made
        corrected_entities["_warnings"] = suggestions["warnings"]
        
        return corrected_entities
    
    def generate_knowledge_report(self, output_file: str = "autocorrect_knowledge_report.txt"):
        """Generate and save a knowledge base report"""
        report = self.agent.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"ENHANCED AUTOCORRECT: Report saved to {output_file}")
        return output_file 