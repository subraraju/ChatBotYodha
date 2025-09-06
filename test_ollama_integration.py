#!/usr/bin/env python3
"""
Test script for Ollama GPT/OSS model integration
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.chatbot.agent import ChatbotAgent
from dotenv import load_dotenv

def main():
    """Test the Ollama connection and GPT models"""
    
    print("🧪 Testing Ollama GPT/OSS Model Integration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Set environment variables to use Ollama as primary
    os.environ["USE_OLLAMA_PRIMARY"] = "true"
    os.environ["OLLAMA_MODEL"] = "llama3.2:1b"  # Start with smaller model
    
    try:
        # Initialize the chatbot agent
        print("🤖 Initializing ChatbotAgent...")
        agent = ChatbotAgent()
        
        # Get LLM status
        print("\n📊 LLM Status:")
        status = agent.get_llm_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test LLM response
        print("\n🧪 Testing LLM Response:")
        test_result = agent.test_llm_response()
        print(test_result)
        
        # If Ollama models are available, test switching
        if status.get("ollama_models"):
            print("\n🔄 Available Ollama Models:")
            for model in status["ollama_models"]:
                print(f"  - {model}")
            
            # Test with different models if available
            larger_models = [m for m in status["ollama_models"] if "3.2" in m and "1b" not in m]
            if larger_models:
                print(f"\n🔄 Testing larger model: {larger_models[0]}")
                success, message = agent.switch_ollama_model(larger_models[0])
                print(f"  Result: {message}")
                
                if success:
                    test_result = agent.test_llm_response("Tell me about customer service best practices.")
                    print(f"  Response test: {test_result}")
        
        # Test actual chat functionality
        print("\n💬 Testing Chat Functionality:")
        session = agent.create_chat_session("test@example.com")
        
        test_messages = [
            "Hello, I'm a customer looking for help",
            "What products do you offer?",
            "Can you help me with my account?"
        ]
        
        for msg in test_messages:
            print(f"\n👤 User: {msg}")
            response, session = agent.chat(msg, session, use_external_search=False)
            print(f"🤖 Bot: {response[:200]}...")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
