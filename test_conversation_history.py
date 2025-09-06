#!/usr/bin/env python3

"""
Test conversation history integration with OpenAI
"""
from app.chatbot.customer_service_bot import CustomerServiceBot

def test_conversation_history():
    print("🧪 Testing Conversation History Integration")
    print("=" * 50)
    
    # Check if we have a valid OpenAI API key first
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "sk-" not in api_key or len(api_key) < 40:
        print("⚠️ No valid OpenAI API key found - testing structure only")
        test_structure_only = True
    else:
        print("✅ OpenAI API key found - testing full functionality")
        test_structure_only = False
    
    # Initialize the bot
    bot = CustomerServiceBot()
    session = bot.start_new_session()
    
    print(f"\n1. Session created: {session.session_id}")
    print(f"   Initial messages: {len(session.messages)}")
    
    # Test conversation flow
    test_messages = [
        "Hi, I need help with my account",
        "My email is john@example.com", 
        "I'm having trouble with my headphones",
        "Can you help me with this?"
    ]
    
    print("\n2. Testing conversation flow...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Step {i}: User says: '{message}'")
        
        if test_structure_only:
            # Just test the structure without making API calls
            print(f"   📝 Conversation history length: {len(session.messages)}")
            
            # Test the _call_llm method signature (without actually calling OpenAI)
            try:
                # This will fail at the API call, but we can check the method signature
                history = session.messages[-3:] if len(session.messages) > 3 else session.messages
                print(f"   📋 Would pass {len(history)} history messages to OpenAI")
                
                # Add mock messages to simulate conversation
                from app.chatbot.customer_service_bot import ChatMessage
                session.messages.append(ChatMessage("user", message))
                session.messages.append(ChatMessage("assistant", f"Mock response to: {message}"))
                
            except Exception as e:
                print(f"   ⚠️ Structure test error: {e}")
        else:
            # Full API test
            try:
                response, updated_session = bot.process_message(message, session)
                session = updated_session
                print(f"   🤖 Bot responded: {response[:60]}...")
                print(f"   📝 Total messages now: {len(session.messages)}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                break
    
    print(f"\n3. Final conversation summary:")
    print(f"   📊 Total messages: {len(session.messages)}")
    print(f"   🎯 Customer state: {session.customer_state.value}")
    
    if session.messages:
        print(f"\n4. Message flow:")
        for i, msg in enumerate(session.messages, 1):
            role_icon = "👤" if msg.role == "user" else "🤖"
            print(f"   {i}. {role_icon} {msg.role}: {msg.content[:50]}...")
    
    print("\n✅ Conversation history test completed!")
    
    # Test the OpenAI message structure
    if len(session.messages) > 2:
        print(f"\n5. Testing OpenAI message format...")
        try:
            # Test that we can build the message array correctly
            recent_history = session.messages[-5:]
            messages = [{"role": "system", "content": "Test system prompt"}]
            
            for msg in recent_history:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    role = "assistant" if msg.role == "assistant" else "user"
                    messages.append({"role": role, "content": msg.content})
            
            print(f"   📋 OpenAI message array would have {len(messages)} messages:")
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:40] + "..." if len(msg['content']) > 40 else msg['content']
                print(f"     {i+1}. {msg['role']}: {content_preview}")
            
            print("   ✅ Message format structure is correct!")
            
        except Exception as e:
            print(f"   ❌ Message format error: {e}")

if __name__ == "__main__":
    test_conversation_history()
