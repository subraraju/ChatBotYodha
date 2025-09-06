#!/usr/bin/env python3
"""
Test script for the new function-call based chatbot
"""
import sys
import os

sys.path.append(".")

from app.chatbot.agent import chatbot_agent
from app.models.pydantic_models import ChatSession
from datetime import datetime


def test_function_calling():
    """Test the function calling capabilities"""
    print("🧪 Testing Function-Call Based Chatbot")
    print("=" * 50)

    # Create a test session
    test_email = "test@example.com"
    session = chatbot_agent.create_chat_session(test_email)

    # Test queries that should trigger different functions
    test_queries = [
        "Show me information about customers",
        "What products do you have available?",
        "Tell me about recent sales",
        "Show me customer activity data",
        "Give me sales analytics and performance data",
        "Search for information about CRM best practices",
        "Find all customers from Seattle",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: '{query}'")
        print("-" * 40)

        try:
            response, updated_session = chatbot_agent.chat(
                query, session, use_external_search=True
            )
            print(f"✅ Response: {response[:200]}...")
            session = updated_session
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n📊 Session Summary:")
    print(f"Total messages: {len(session.messages)}")
    print(f"Session ID: {session.session_id}")


def test_individual_functions():
    """Test individual functions directly"""
    print("\n🔧 Testing Individual Functions")
    print("=" * 50)

    agent = chatbot_agent

    # Test if the agent was created successfully
    if agent.agent is None:
        print("❌ Agent not properly initialized")
        return

    print("✅ Agent initialized successfully")
    print(f"Available tools: {[tool.name for tool in agent.tools]}")

    # Test database connection
    if hasattr(agent, "db"):
        print("✅ Database connection available")
    else:
        print("⚠️  Database connection not available")


if __name__ == "__main__":
    print("Starting Function-Call Chatbot Tests...")

    try:
        test_individual_functions()
        test_function_calling()
        print("\n🎉 All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
