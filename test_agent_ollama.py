#!/usr/bin/env python3
"""
Quick test of the chatbot agent with Ollama
"""

import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variables for Ollama
os.environ["USE_OLLAMA_PRIMARY"] = "true"
os.environ["OLLAMA_MODEL"] = "llama3.2:1b"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

try:
    from app.chatbot.agent import ChatbotAgent
    
    print("🧪 Testing Ollama GPT Model Integration")
    print("=" * 50)
    
    # Initialize agent
    print("🤖 Initializing chatbot agent...")
    agent = ChatbotAgent()
    
    # Get status
    print("\n📊 LLM Status:")
    status = agent.get_llm_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test LLM response
    print("\n🧪 Testing LLM Response...")
    test_result = agent.test_llm_response("Hello! Are you working with the local model?")
    print(test_result)
    
    # Test chat functionality
    print("\n💬 Testing Chat Session...")
    session = agent.create_chat_session("test@example.com")
    
    test_messages = [
        "Hello, I'm testing the local GPT model",
        "Can you tell me about your capabilities?",
        "What's the weather like today?"
    ]
    
    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        start_time = time.time()
        
        try:
            response, session = agent.chat(msg, session, use_external_search=False)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"🤖 Bot ({response_time:.1f}s): {response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
