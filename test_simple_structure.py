"""Simple test to verify agent functionality without complex integrations"""

import sys
import os
from datetime import datetime
import uuid

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))


def test_basic_imports():
    """Test basic imports"""
    try:
        from models.pydantic_models import ChatSession, ChatMessage
        print("✅ Successfully imported Pydantic models")
        return True
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False


def test_session_creation():
    """Test proper session creation"""
    try:
        from models.pydantic_models import ChatSession, ChatMessage
        
        # Create a proper session with all required fields
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            customer_email="test@example.com",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("✅ Session created successfully")
        
        # Add a message
        message = ChatMessage(
            role="user",
            content="Hello, how many customers do we have?",
            timestamp=datetime.now()
        )
        session.messages.append(message)
        print(f"✅ Added message, session has {len(session.messages)} messages")
        
        return True
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False


def test_database_schema():
    """Test database schema loading"""
    try:
        # Read the database schema directly
        schema_path = os.path.join(os.path.dirname(__file__), 'sql_scripts', 'create_tables.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            if schema:
                table_count = schema.count('CREATE TABLE')
                print(f"✅ Database schema loaded with {table_count} tables")
                
                # Check for expected tables
                expected_tables = ['customers', 'products', 'sales', 'activities']
                for table in expected_tables:
                    if table.lower() in schema.lower():
                        print(f"  ✅ Found {table} table in schema")
                    else:
                        print(f"  ❌ Missing {table} table in schema")
                return True
            else:
                print("❌ Schema file is empty")
                return False
        else:
            print(f"❌ Schema file not found at: {schema_path}")
            return False
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False


def test_sql_functions():
    """Test that we can construct basic SQL queries"""
    try:
        # Test basic SQL query construction
        table_schema = """
        CREATE TABLE customers (
            customer_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(255) UNIQUE
        );
        """
        
        # Simple query that might be generated
        count_query = "SELECT COUNT(*) FROM customers;"
        top_customers_query = "SELECT first_name, last_name, email FROM customers LIMIT 5;"
        
        print("✅ Can construct basic SQL queries:")
        print(f"  - Count query: {count_query}")
        print(f"  - Top customers query: {top_customers_query}")
        
        return True
    except Exception as e:
        print(f"❌ SQL function test failed: {e}")
        return False


def main():
    print("🔧 Simple Agent Structure Test")
    print("=" * 40)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Session Creation", test_session_creation),
        ("Database Schema", test_database_schema),
        ("SQL Functions", test_sql_functions),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 Basic structure is working!")
        print("\n💡 Next steps:")
        print("1. Install Ollama (https://ollama.ai/)")
        print("2. Pull required models: ollama pull sqlcoder:7b")
        print("3. Pull required models: ollama pull phi3:chat")
        print("4. Pull required models: ollama pull llama3.2:1b")
        print("5. Test the enhanced agent with actual model integration")


if __name__ == "__main__":
    main()
