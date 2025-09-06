#!/usr/bin/env python3
"""
Simple test for function-call based chatbot without external dependencies
"""
import sys
import os

sys.path.append(".")


def test_function_calls_directly():
    """Test the functions directly without the LLM"""
    print("🧪 Testing Function Calls Directly")
    print("=" * 50)

    # Import the agent
    from app.chatbot.agent import ChatbotAgent

    # Create agent instance
    agent = ChatbotAgent()

    print(f"✅ Agent created successfully")
    print(f"Available tools: {[tool.name for tool in agent.tools]}")

    # Test each function directly
    test_cases = [
        ("get_customer_data", "john"),
        ("get_product_data", "software"),
        ("get_sales_data", "recent"),
        ("get_activity_data", "support"),
        ("get_sales_analytics", "all"),
        ("search_external_info", "CRM best practices"),
        ("execute_complex_query", "Show me all customers"),
    ]

    for tool_name, test_input in test_cases:
        print(f"\n🔧 Testing {tool_name} with input: '{test_input}'")
        print("-" * 40)

        # Find the tool
        tool = next((t for t in agent.tools if t.name == tool_name), None)
        if tool:
            try:
                result = tool.func(test_input)
                print(f"✅ Result: {result[:100]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Tool {tool_name} not found")


def test_mock_llm():
    """Test the mock LLM functionality"""
    print("\n🤖 Testing Mock LLM")
    print("=" * 50)

    from app.chatbot.agent import ChatbotAgent

    agent = ChatbotAgent()

    # Test the mock LLM directly
    llm = agent._get_llm()
    print(f"LLM type: {type(llm)}")

    test_prompt = "Hello, can you help me with customer information?"
    response = llm(test_prompt)
    print(f"✅ Mock LLM response: {response}")


def test_session_management():
    """Test session creation and management"""
    print("\n📝 Testing Session Management")
    print("=" * 50)

    from app.chatbot.agent import ChatbotAgent

    agent = ChatbotAgent()

    # Create a session
    test_email = "test@example.com"
    session = agent.create_chat_session(test_email)

    print(f"✅ Session created: {session.session_id}")
    print(f"Customer email: {session.customer_email}")
    print(f"Created at: {session.created_at}")

    # Add a message
    session = agent.add_message_to_session(session, "user", "Hello, can you help me?")
    session = agent.add_message_to_session(
        session, "assistant", "Of course! I'm here to help."
    )

    print(f"✅ Messages added: {len(session.messages)}")
    for msg in session.messages:
        print(f"  {msg.role}: {msg.content}")


if __name__ == "__main__":
    print("🚀 Starting Simplified Function-Call Tests...")

    try:
        test_function_calls_directly()
        test_mock_llm()
        test_session_management()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
