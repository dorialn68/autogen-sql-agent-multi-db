# 🤖 AutoGen SQL Agent with Multi-Database Support

A sophisticated Natural Language to SQL (NL2SQL) system powered by AutoGen agents with enhanced autocorrection capabilities, autonomous learning, and multi-database support (SQLite, PostgreSQL, Vertica).

## 🌟 Features

### 🔄 **AutoGen Multi-Agent Architecture**
- **Query Understanding Agent**: Analyzes user intent and query patterns
- **Entity Extraction Agent**: Identifies names, locations, and attributes
- **SQL Validation Agent**: Validates generated SQL syntax and schema compliance
- **Error Analysis Agent**: Diagnoses SQL execution errors with intelligent suggestions
- **SQL Refinement Agent**: Uses AI to fix and optimize failed queries
- **Enhanced Autonomous Autocorrect Agent**: Self-learning typo correction with database content verification

### 🗄️ **Multi-Database Support**
- **SQLite**: Local file-based databases (default: Chinook sample)
- **PostgreSQL**: Local and remote PostgreSQL servers with SSL support
- **Vertica**: Enterprise-grade analytics database support
- **Unified Interface**: Consistent query interface across all database types
- **Connection Management**: Automatic connection testing and validation
- **Schema Analysis**: Automatic schema discovery and metadata gathering

### ✨ **Enhanced Autocorrection System**
- **Autonomous Knowledge Base**: Automatically analyzes database schema and content
- **Intelligent Typo Correction**: Fixes common misspellings (e.g., "Bjorn" → "Bjørn", "Muray" → "Murray")
- **Confidence Scoring**: Provides confidence scores for corrections
- **Self-Learning**: Tracks correction patterns and improves over time
- **Real-time Feedback**: Shows users what corrections were applied

### 📊 **Advanced Query Results**
- **Full Results Display**: View all query results with scrollable interface
- **CSV Export**: One-click export of query results to CSV files
- **Real-time Processing**: Live query execution with progress indicators
- **Error Recovery**: Intelligent error handling with suggested fixes

### 🖥️ **Web Interface**
- **Modern UI**: Beautiful, responsive web interface
- **Real-time Health Monitoring**: System resource monitoring
- **Database Management**: Easy database switching and validation
- **Query History**: Track query performance and iterations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama with `qwen2.5-coder:7b` model
- Optional: PostgreSQL or Vertica server for multi-database features

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/dorialn68/autogen-sql-agent-multi-db.git
cd autogen-sql-agent-multi-db
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install and start Ollama**
```bash
# Install Ollama (visit https://ollama.ai for OS-specific instructions)
# Pull the required model
ollama pull qwen2.5-coder:7b
```

4. **Start the application**
```bash
python app/app_dual_super_safe.py
```

5. **Open your browser**
Navigate to `http://localhost:5002`

## 🔧 Database Configuration

### SQLite (Default)
- Uses the included `Chinook_Sqlite.sqlite` sample database
- No additional configuration required

### PostgreSQL Setup
```python
from app.database_config import DatabaseConfigManager

config_manager = DatabaseConfigManager()
config_manager.add_postgresql_config(
    name="MyPostgreSQL",
    host="localhost",
    database="mydb",
    username="user",
    password="password",
    port=5432,
    schema="public"
)
```

### Vertica Setup
```python
config_manager.add_vertica_config(
    name="MyVertica",
    host="vertica.example.com",
    database="analytics",
    username="analyst",
    password="secret",
    port=5433,
    schema="public"
)
```

## 🎯 Usage Examples

### Basic Queries
```
"How many customers do we have?"
"Where does Helena live?"
"Show me all artists"
```

### Queries with Autocorrection
```
"Where does Helena and Bjorn live?"     # Corrects "Bjorn" → "Bjørn"
"Show me Steve Muray"                   # Corrects "Muray" → "Murray"
"Find customer named Bjprn"             # Corrects "Bjprn" → "Bjørn"
```

### Complex Queries
```
"Which items did Dan purchase and what was the amount of each item?"
"Show me the top 10 customers by total purchases"
"What are the most popular genres by sales?"
```

## 🧠 AutoGen Agent Architecture

### Query Processing Flow
1. **Intent Analysis** → Determines query type and requirements
2. **Entity Extraction** → Identifies names, values, and filters
3. **Autocorrection** → Fixes typos using database content
4. **SQL Generation** → Creates optimized SQL queries
5. **Validation** → Checks syntax and schema compliance
6. **Execution** → Runs query with error handling
7. **Refinement** → Improves failed queries using AI

## 📁 Project Structure

```
autogen-sql-agent-multi-db/
├── app/
│   ├── app_dual_super_safe.py      # Main Flask application
│   ├── autogen_iterative.py        # AutoGen agent implementation
│   ├── autocorrect_agent_enhanced.py # Enhanced autocorrect system
│   ├── database_config.py          # Multi-database configuration
│   ├── database_adapter.py         # Unified database interface
│   └── system_manager.py           # AI system coordination
├── templates/
│   └── index_super_safe.html       # Web interface
├── Chinook_Sqlite.sqlite           # Sample SQLite database
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🧪 Testing

```bash
# Test basic functionality
python test_api_direct.py

# Test autocorrection
python test_bjorn_specific.py

# Test database configuration
python test_database_config.py

# Test multi-database support
python test_postgresql_vertica.py
```

## 📊 Performance
- **Query Response Time**: ~3-8 seconds for complex queries
- **Autocorrection Speed**: ~100ms for typo detection
- **Memory Usage**: ~150MB base + knowledge base
- **Supported Databases**: SQLite, PostgreSQL, Vertica

## 🔒 Security Features
- **Connection Validation**: Automatic testing of database connections
- **SQL Injection Protection**: Parameterized queries and validation
- **Resource Monitoring**: Real-time system resource tracking
- **Error Handling**: Comprehensive error recovery and logging

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- AutoGen framework for multi-agent architecture
- Ollama for local LLM hosting
- Chinook Database for sample data
- Flask for web framework

---
**Built with ❤️ using AutoGen, Ollama, and modern web technologies**

## 📖 Additional Documentation
- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api.md)
- [Agent Architecture](docs/agents.md)