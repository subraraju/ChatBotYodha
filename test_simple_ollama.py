#!/usr/bin/env python3
"""
Simple test for Ollama connection without complex dependencies
"""

import requests
import json
import os
from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama

def test_ollama_server():
    """Test if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama server is running!")
            print(f"📦 Available models: {[m['name'] for m in models]}")
            return models
        else:
            print(f"❌ Ollama server responded with status: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server (http://localhost:11434)")
        print("💡 Make sure Ollama is installed and running:")
        print("   1. Install Ollama from https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Pull a model: ollama pull llama3.2:1b")
        return []
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return []

def test_ollama_langchain():
    """Test Ollama with LangChain"""
    try:
        print("\n🧪 Testing Ollama with LangChain...")
        
        # Try with ChatOllama (recommended)
        llm = ChatOllama(
            model="llama3.2:1b",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        
        response = llm.invoke("Hello! Can you help me with customer service?")
        print(f"✅ ChatOllama test successful!")
        print(f"🤖 Response: {response.content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        
        # Try fallback with regular Ollama
        try:
            print("🔄 Trying fallback with Ollama LLM...")
            llm = Ollama(
                model="llama3.2:1b",
                base_url="http://localhost:11434"
            )
            response = llm.invoke("Hello!")
            print(f"✅ Ollama LLM test successful!")
            print(f"🤖 Response: {response[:100]}...")
            return True
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return False

def test_ollama_api_direct():
    """Test Ollama API directly"""
    try:
        print("\n🧪 Testing Ollama API directly...")
        
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "llama3.2:1b",
            "prompt": "Hello! Please respond with a short greeting.",
            "stream": False
        }
        
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Direct API test successful!")
            print(f"🤖 Response: {result.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"❌ API returned status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Ollama GPT/OSS Model Connection Test")
    print("=" * 50)
    
    # Test 1: Check if Ollama server is running
    models = test_ollama_server()
    
    if not models:
        print("\n💡 To set up Ollama:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Start server: ollama serve")
        print("3. Pull model: ollama pull llama3.2:1b")
        return
    
    # Test 2: Test direct API
    api_success = test_ollama_api_direct()
    
    # Test 3: Test with LangChain
    langchain_success = test_ollama_langchain()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"  Ollama Server: {'✅' if models else '❌'}")
    print(f"  Direct API: {'✅' if api_success else '❌'}")
    print(f"  LangChain: {'✅' if langchain_success else '❌'}")
    
    if models and (api_success or langchain_success):
        print("\n🎉 Ollama is working! You can now use GPT/OSS models.")
        print("\n📝 To use in your chatbot:")
        print("1. Set USE_OLLAMA_PRIMARY=true in your .env file")
        print("2. Set OLLAMA_MODEL=llama3.2:1b (or your preferred model)")
        print("3. Restart your chatbot application")
    else:
        print("\n⚠️  Some tests failed. Check Ollama installation and model availability.")

if __name__ == "__main__":
    main()
