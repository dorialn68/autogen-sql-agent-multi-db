#!/usr/bin/env python3
"""
Test script specifically for the Autocorrect Agent functionality
"""
import sys
import os
sys.path.insert(0, 'app')  # Add app directory to path

from autogen_iterative import DatabaseManager, AutocorrectAgent, QueryUnderstandingAgent, EntityExtractionAgent
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_autocorrect_agent():
    print("Testing Autocorrect Agent Directly")
    print("=" * 80)
    
    # Initialize components
    db_path = "Chinook_Sqlite.sqlite"
    db_manager = DatabaseManager(db_path)
    autocorrect_agent = AutocorrectAgent(db_manager)
    query_agent = QueryUnderstandingAgent()
    entity_agent = EntityExtractionAgent()
    
    # Test cases
    test_queries = [
        "where does Helena and Bjprn lives ?",
        "find customer Steve Muray",
        "show me all customers from Prage",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: '{query}'")
        print("-" * 60)
        
        # Extract intent and entities
        intent = query_agent.analyze_query(query)
        entities = entity_agent.extract_entities(query)
        
        print(f"Intent: {intent}")
        print(f"Original entities: {entities}")
        
        # Apply autocorrection
        corrected_entities = autocorrect_agent.correct_entities(entities, intent)
        
        print(f"Corrected entities: {corrected_entities}")
        if corrected_entities.get("_corrections"):
            print(f"Corrections made: {corrected_entities['_corrections']}")
        else:
            print("No corrections made")
        
        # Test fuzzy matching directly
        if entities.get("person_names"):
            print("\nTesting fuzzy matching for names:")
            for name in entities["person_names"]:
                matches = autocorrect_agent.find_similar_values(name, "Customer", "FirstName", threshold=0.7)
                print(f"  '{name}' → Similar names found: {matches[:3]}")

if __name__ == "__main__":
    test_autocorrect_agent() 