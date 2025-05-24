"""
LangChain Integration Module for GPT4All NL2SQL Enterprise System

This module provides LangChain-based components to replace the custom AutoGen
multi-agent system with a more robust and enterprise-ready solution.

Components:
- SQL Agent: LangChain SQL agent with GPT4All integration
- Query Classifier: SQL vs Natural Language detection
- Entity Resolver: Fuzzy name matching and entity resolution
- Database Connectors: Multi-database support (SQLite, PostgreSQL, Vertica)
- Conversation Memory: Context and conversation management
"""

from .query_classifier import QueryClassifier
from .database_connectors import DatabaseConnectorFactory
from .sql_agent import LangChainSQLAgent

__all__ = [
    'QueryClassifier', 
    'DatabaseConnectorFactory',
    'LangChainSQLAgent'
]

__version__ = "1.0.0"