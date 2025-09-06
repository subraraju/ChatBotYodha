#!/usr/bin/env python3
"""
Simple Ollama connection test - no complex dependencies
"""

import requests
import json
import time

def check_ollama_server():
    """Check if Ollama server is running and list models"""
    print("🔍 Checking Ollama server...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print("✅ Ollama server is running!")
            
            if models:
                print(f"📦 Available models ({len(models)}):")
                for model in models:
                    print(f"  - {model['name']} ({model.get('size', 'unknown size')})")
                return models
            else:
                print("📦 No models installed")
                return []
        else:
            print(f"❌ Server returned status {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server")
        print("💡 To fix this:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Run: ollama serve")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_ollama_chat(model_name="llama3.2:1b"):
    """Test Ollama chat functionality"""
    print(f"\n🧪 Testing chat with model: {model_name}")
    
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": "Hello! Please respond with a brief greeting and confirm you're working.",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    
    try:
        print("  Sending request...")
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'response' in result:
                print("✅ Chat test successful!")
                print(f"🤖 Model response: {result['response']}")
                return True
            else:
                print(f"❌ No response in result: {result}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (model might be loading)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def pull_model(model_name="llama3.2:1b"):
    """Pull a model if it doesn't exist"""
    print(f"\n📥 Attempting to pull model: {model_name}")
    
    url = "http://localhost:11434/api/pull"
    data = {"name": model_name}
    
    try:
        print("  This may take a few minutes...")
        response = requests.post(url, json=data, stream=True, timeout=300)
        
        if response.status_code == 200:
            print("✅ Model pull initiated!")
            # Note: In a real implementation, you'd parse the streaming response
            # to show progress, but for simplicity we'll just wait
            return True
        else:
            print(f"❌ Pull failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error pulling model: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Simple Ollama GPT/OSS Connection Test")
    print("=" * 50)
    
    # Step 1: Check if server is running
    models = check_ollama_server()
    
    if models is None:
        print("\n💡 Ollama Setup Instructions:")
        print("1. Download and install Ollama from https://ollama.ai")
        print("2. Open a terminal and run: ollama serve")
        print("3. In another terminal, run: ollama pull llama3.2:1b")
        print("4. Run this test again")
        return
    
    # Step 2: If no models, try to pull one
    if not models:
        print("\n📥 No models found. Attempting to pull a small model...")
        if pull_model("llama3.2:1b"):
            print("  Waiting for download to complete...")
            time.sleep(10)  # Wait a bit for download to start
            models = check_ollama_server()  # Check again
    
    # Step 3: Test available models
    if models:
        for model in models:
            model_name = model['name']
            print(f"\n🧪 Testing model: {model_name}")
            success = test_ollama_chat(model_name)
            if success:
                print(f"✅ {model_name} is working correctly!")
                break
            else:
                print(f"❌ {model_name} test failed")
    
    # Step 4: Summary and next steps
    print("\n📊 Test Summary:")
    server_status = "✅" if models is not None else "❌"
    model_status = "✅" if models else "❌"
    print(f"  Ollama Server: {server_status}")
    print(f"  Models Available: {model_status}")
    
    if models:
        print("\n🎉 Ollama is ready!")
        print("\n📝 To use with your chatbot:")
        print("1. In your .env file, add:")
        print("   USE_OLLAMA_PRIMARY=true")
        print("   OLLAMA_MODEL=llama3.2:1b")
        print("2. Your chatbot will now use Ollama instead of Groq!")
        print("3. Available GPT-style models to try:")
        print("   - llama3.2:1b (small, fast)")
        print("   - llama3.2:3b (medium)")
        print("   - llama3.1:8b (large, more capable)")
        print("   - mistral:7b (alternative architecture)")
    else:
        print("\n⚠️  Ollama setup needed. Follow the instructions above.")

if __name__ == "__main__":
    main()
