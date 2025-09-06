"""
Test the simplified enhanced agent functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from chatbot.simple_agent import EnhancedChatAgent, ChatSession

def test_agent():
    print("🧪 Testing Enhanced Agent with Virtual Environment")
    print("=" * 50)
    
    # Initialize agent
    try:
        agent = EnhancedChatAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Create session
    try:
        session = ChatSession(customer_email="test@example.com")
        print("✅ Session created successfully")
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
    
    # Test basic chat
    test_queries = [
        "Hello, how can you help me?",
        "How many customers do we have?",
        "Show me the top products by sales"
    ]
    
    for query in test_queries:
        print(f"\n💬 Testing: '{query}'")
        try:
            response, updated_session = agent.chat(query, session)
            print(f"🤖 Response: {response[:100]}..." if len(response) > 100 else f"🤖 Response: {response}")
            session = updated_session
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Test completed! Session has {len(session.messages)} messages")
    return True

if __name__ == "__main__":
    test_agent()
