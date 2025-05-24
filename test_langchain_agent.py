from app.langchain_integration import LangChainSQLAgent
import logging
import os

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

print("Testing LangChain SQL Agent:")
print("=" * 50)

try:
    # Test with the existing model (use full path)
    model_path = os.path.abspath("Phi-3-mini-4k-instruct-q4.gguf")
    
    print(f"Initializing agent with model: {model_path}")
    agent = LangChainSQLAgent(
        model_path=model_path,
        database_connection="Chinook_Sqlite.sqlite"
    )
    
    print("✅ Agent initialized successfully")
    
    # Test database info
    db_info = agent.get_database_info()
    print(f"✅ Database info: {db_info}")
    
    # Test SQL query classification and execution
    print("\n--- Testing SQL Query ---")
    sql_result = agent.process_query("SELECT COUNT(*) as customer_count FROM Customer;")
    print(f"SQL Result: {sql_result}")
    
    # Test natural language query
    print("\n--- Testing Natural Language Query ---")
    nl_result = agent.process_query("How many customers are there?")
    print(f"NL Result: {nl_result}")
    
    agent.disconnect()
    print("\n✅ All tests completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()