#!/usr/bin/env python3

"""
Test OpenAI integration directly
"""
from app.chatbot.customer_service_bot import CustomerServiceBot

def test_openai_integration():
    print("🧪 Testing OpenAI Integration")
    print("=" * 40)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    
    # Test OpenAI call
    print("\n1. Testing OpenAI API call...")
    try:
        response = bot._call_llm("Hello, what is your name?", max_tokens=50)
        print(f"✅ OpenAI Response: {response}")
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return False
    
    # Test session and conversation
    print("\n2. Testing full conversation flow...")
    try:
        session = bot.start_new_session()
        print(f"✅ Session created: {session.session_id}")
        
        # Test a simple conversation
        response, updated_session = bot.process_message("Hi, I need help", session)
        print(f"✅ Bot Response: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Conversation Error: {e}")
        return False
    
    print("\n✅ All OpenAI integration tests passed!")
    return True

if __name__ == "__main__":
    test_openai_integration()
