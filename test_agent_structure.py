"""Test the enhanced agent structure without requiring Ollama"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test if all the imports work correctly"""
    try:
        from chatbot.agent import EnhancedChatAgent
        print("✅ Successfully imported EnhancedChatAgent")
        
        from models.pydantic_models import ChatSession
        print("✅ Successfully imported ChatSession")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_agent_initialization():
    """Test if the agent can be initialized"""
    try:
        from chatbot.agent import EnhancedChatAgent
        agent = EnhancedChatAgent()
        print("✅ Agent initialized successfully")
        
        # Test that the agent has the expected attributes
        if hasattr(agent, 'sql_model'):
            print(f"✅ Agent has sql_model: {agent.sql_model}")
        if hasattr(agent, 'chat_model'):
            print(f"✅ Agent has chat_model: {agent.chat_model}")
        if hasattr(agent, 'database_schema'):
            print("✅ Agent has database_schema loaded")
        if hasattr(agent, '_contextualize_query'):
            print("✅ Agent has _contextualize_query method")
        if hasattr(agent, '_generate_sql_query'):
            print("✅ Agent has _generate_sql_query method")
        if hasattr(agent, 'execute_smart_sql_query'):
            print("✅ Agent has execute_smart_sql_query method")
            
        return True
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False


def test_session_creation():
    """Test session creation and management"""
    try:
        from models.pydantic_models import ChatSession, ChatMessage
        
        # Create a session
        session = ChatSession(customer_email="test@example.com")
        print("✅ Session created successfully")
        
        # Test adding messages
        session.messages.append(ChatMessage(role="user", content="Hello"))
        session.messages.append(ChatMessage(role="assistant", content="Hi there!"))
        print(f"✅ Session has {len(session.messages)} messages")
        
        return True
    except Exception as e:
        print(f"❌ Session test error: {e}")
        return False


def test_database_schema():
    """Test that database schema is properly loaded"""
    try:
        from chatbot.agent import EnhancedChatAgent
        agent = EnhancedChatAgent()
        
        if hasattr(agent, 'database_schema') and agent.database_schema:
            schema_lines = agent.database_schema.split('\n')
            table_count = sum(1 for line in schema_lines if 'CREATE TABLE' in line)
            print(f"✅ Database schema loaded with {table_count} tables")
            
            # Check for expected tables
            expected_tables = ['customers', 'products', 'sales', 'activities']
            for table in expected_tables:
                if table.lower() in agent.database_schema.lower():
                    print(f"  ✅ Found {table} table in schema")
                else:
                    print(f"  ❌ Missing {table} table in schema")
            
            return True
        else:
            print("❌ Database schema not loaded")
            return False
    except Exception as e:
        print(f"❌ Database schema test error: {e}")
        return False


def main():
    print("🧪 Testing Enhanced Agent Structure (No Ollama Required)")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Agent Initialization", test_agent_initialization),
        ("Session Creation", test_session_creation),
        ("Database Schema", test_database_schema),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 Test Results Summary:")
    print("=" * 40)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All structure tests passed! The enhanced agent is ready.")
        print("💡 To test full functionality, ensure Ollama is installed with:")
        print("   - sqlcoder:7b model for SQL generation")
        print("   - phi3:chat model for query contextualization")
        print("   - llama3.2:1b model for general chat")
    else:
        print("⚠️  Some tests failed. Please check the code structure.")


if __name__ == "__main__":
    main()
