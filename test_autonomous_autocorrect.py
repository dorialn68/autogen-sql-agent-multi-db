#!/usr/bin/env python3
"""
Test script for the Enhanced Autonomous Autocorrect Agent
"""
import sys
import os
sys.path.insert(0, 'app')

from autocorrect_agent_enhanced import AutonomousAutocorrectAgent
import logging
import json

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_autonomous_agent():
    print("Testing Enhanced Autonomous Autocorrect Agent")
    print("=" * 80)
    
    # Initialize the agent
    db_path = "Chinook_Sqlite.sqlite"
    agent = AutonomousAutocorrectAgent(db_path)
    
    # Test 1: Generate and display the knowledge base report
    print("\n1. GENERATING KNOWLEDGE BASE REPORT")
    print("-" * 60)
    report = agent.generate_report()
    print(report[:1000] + "...\n[Report truncated for display]")
    
    # Save full report
    with open("autocorrect_knowledge_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n✅ Full report saved to: autocorrect_knowledge_report.txt")
    
    # Test 2: Test corrections
    print("\n2. TESTING AUTOCORRECTION CAPABILITIES")
    print("-" * 60)
    
    test_cases = [
        {
            "query": "where does Bjprn and Helena live?",
            "entities": {"person_names": ["Bjprn", "Helena"]},
            "intent": {"entity": "customer"}
        },
        {
            "query": "show me Steve Muray",
            "entities": {"person_names": ["Steve", "Muray"]},
            "intent": {"entity": "customer"}
        },
        {
            "query": "find artist Aerosmth",
            "entities": {"artists": ["Aerosmth"]},
            "intent": {"entity": "artist"}
        }
    ]
    
    for test in test_cases:
        print(f"\nQuery: '{test['query']}'")
        suggestions = agent.suggest_corrections(
            test["query"], 
            test["entities"], 
            test["intent"]
        )
        
        if suggestions["corrections"]:
            print("Corrections:")
            for corr in suggestions["corrections"]:
                print(f"  • {corr['original']} → {corr['suggested']} "
                      f"(confidence: {corr['confidence']:.2f})")
        else:
            print("  No corrections needed")
        
        if suggestions["warnings"]:
            print("Warnings:")
            for warn in suggestions["warnings"]:
                print(f"  ⚠ {warn}")
    
    # Test 3: Show knowledge base structure
    print("\n3. KNOWLEDGE BASE STRUCTURE")
    print("-" * 60)
    
    # Save knowledge base for inspection
    kb_preview_file = "knowledge_base_preview.json"
    with open(kb_preview_file, 'w', encoding='utf-8') as f:
        # Create a preview with limited data
        preview = {
            "metadata": agent.knowledge_base.get("metadata", {}),
            "schema": {
                table: {
                    "columns": list(info["columns"].keys()),
                    "primary_keys": info["primary_keys"],
                    "foreign_keys_count": len(info["foreign_keys"])
                }
                for table, info in agent.knowledge_base["schema"].items()
            },
            "sample_common_values": {
                table: {
                    col: len(values) if values else 0
                    for col, values in cols.items()
                }
                for table, cols in agent.knowledge_base["common_values"].items()
            }
        }
        json.dump(preview, f, indent=2)
    
    print(f"Knowledge base structure saved to: {kb_preview_file}")
    print("\nKnowledge Base Contains:")
    print(f"  • Tables analyzed: {len(agent.knowledge_base['schema'])}")
    print(f"  • Relationships found: {len(agent.knowledge_base['relationships'])}")
    print(f"  • Tables with common values: {len(agent.knowledge_base['common_values'])}")
    
    # Test 4: Show correction patterns
    print("\n4. CORRECTION PATTERNS ANALYSIS")
    print("-" * 60)
    patterns = agent.analyze_correction_patterns()
    print(f"Total corrections logged: {patterns['total_corrections']}")
    if patterns.get('common_mistakes'):
        print("Common mistakes:")
        for mistake, count in list(patterns['common_mistakes'].items())[:5]:
            print(f"  • {mistake}: {count} times")
    
    print("\n" + "="*80)
    print("✅ Enhanced Autonomous Autocorrect Agent Test Complete!")
    print("\nThe agent has:")
    print("  • Built a comprehensive knowledge base from the database")
    print("  • Learned all table schemas, relationships, and common values")
    print("  • Created a persistent cache for fast lookups")
    print("  • Can intelligently correct typos based on actual data")
    print("  • Tracks correction history for continuous improvement")

if __name__ == "__main__":
    test_autonomous_agent() 