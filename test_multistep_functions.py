#!/usr/bin/env python3
"""
Test script for multi-step function calling capabilities
This demonstrates how the agent can make multiple function calls in sequence
"""
import sys
import os

sys.path.append(".")

from app.chatbot.agent import chatbot_agent
from app.models.pydantic_models import ChatSession
from datetime import datetime


def test_multistep_functions():
    """Test multi-step function calling scenarios"""
    print("🧪 Testing Multi-Step Function Calling")
    print("=" * 60)

    # Create a test session
    test_email = "test@example.com"
    session = chatbot_agent.create_chat_session(test_email)

    # Test scenarios that should trigger multiple function calls
    test_scenarios = [
        {
            "query": "I want to know everything about the customer john.doe@example.com - their profile, purchases, and activities",
            "expected_steps": [
                "1. Look up customer basic info",
                "2. Get customer ID",
                "3. Fetch sales history",
                "4. Fetch activity history",
            ],
        },
        {
            "query": "Give me a complete analysis of our CRM software product - how it's performing, who's buying it, and customer engagement",
            "expected_steps": [
                "1. Find CRM product info",
                "2. Get sales analytics for the product",
                "3. Find top customers",
                "4. Get activity/engagement data",
            ],
        },
        {
            "query": "Find customers in Seattle and show me their total purchases and recent activities",
            "expected_steps": [
                "1. Search for customers in Seattle",
                "2. For each customer, get sales data",
                "3. Get activity data for those customers",
            ],
        },
        {
            "query": "Show me our top-selling product and then find all customers who bought it along with their contact information",
            "expected_steps": [
                "1. Get sales analytics to find top product",
                "2. Find customers who bought that product",
                "3. Get customer contact details",
            ],
        },
        {
            "query": "I need to understand the relationship between customer support activities and sales - show me customers with high support activity and their purchase history",
            "expected_steps": [
                "1. Get activity data for support interactions",
                "2. Identify customers with high support activity",
                "3. Get sales data for those customers",
            ],
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔄 Scenario {i}: Multi-Step Analysis")
        print(f"Query: {scenario['query']}")
        print(f"Expected Steps: {', '.join(scenario['expected_steps'])}")
        print("-" * 60)

        try:
            # Enable verbose mode to see the agent's reasoning
            print("🤖 Agent Processing (this may take a moment)...")
            response, updated_session = chatbot_agent.chat(
                scenario["query"], session, use_external_search=True
            )

            print(f"\n✅ Final Response:")
            print(f"{response}")
            print(f"\n📊 Response Length: {len(response)} characters")

            session = updated_session

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 60)

    print(f"\n📈 Session Summary:")
    print(f"Total messages in session: {len(session.messages)}")
    print(f"Session ID: {session.session_id}")

    # Show conversation history
    print(f"\n💬 Conversation History:")
    for i, msg in enumerate(session.messages[-6:], 1):  # Show last 6 messages
        role_emoji = "👤" if msg.role == "user" else "🤖"
        print(f"{role_emoji} {msg.role}: {msg.content[:100]}...")


def test_specific_multistep_tools():
    """Test the specific multi-step tools directly"""
    print("\n🔧 Testing Multi-Step Tools Directly")
    print("=" * 60)

    from app.chatbot.agent import ChatbotAgent

    agent = ChatbotAgent()

    # Test the new multi-step tools
    multistep_tests = [
        {
            "tool": "get_customer_details_by_email",
            "input": "john.doe@example.com",
            "description": "Get complete customer profile by email",
        },
        {
            "tool": "get_product_analytics",
            "input": "CRM Software",
            "description": "Get comprehensive product analytics",
        },
    ]

    for test in multistep_tests:
        print(f"\n🛠️  Testing: {test['description']}")
        print(f"Tool: {test['tool']}")
        print(f"Input: {test['input']}")
        print("-" * 40)

        # Find and execute the tool
        tool = next((t for t in agent.tools if t.name == test["tool"]), None)
        if tool:
            try:
                result = tool.func(test["input"])
                print(f"✅ Result: {result[:300]}...")
                if len(result) > 300:
                    print(f"📏 (Truncated - full result is {len(result)} characters)")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Tool {test['tool']} not found")


if __name__ == "__main__":
    print("🚀 Starting Multi-Step Function Calling Tests")
    print("This will demonstrate how the agent can chain multiple function calls")
    print("to gather comprehensive information in response to complex queries.\n")

    # Test direct tool functionality
    test_specific_multistep_tools()

    # Test full agent multi-step scenarios
    test_multistep_functions()

    print("\n🎉 Multi-step function calling tests completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Sequential function calls within a single query")
    print("✅ Using results from one function to inform the next")
    print("✅ Comprehensive data gathering across multiple tables")
    print("✅ Step-by-step reasoning and explanation")
