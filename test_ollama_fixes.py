"""
Test Ollama connection and timeout fixes
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_ollama_connection():
    """Test Ollama connection and timeout handling"""
    print("🔌 Testing Ollama Connection and Timeout Fixes")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        print("🚀 Initializing bot (will check Ollama connection)...")
        bot = CustomerServiceBot()
        
        print(f"\n⚙️ Configuration:")
        print(f"   Ollama URL: {bot.ollama_base_url}")
        print(f"   Chat Model: {bot.chat_model}")
        print(f"   SQL Model: {bot.sql_model}")
        
        # Test a simple call
        print(f"\n🧪 Testing simple Ollama call...")
        response = bot._call_ollama(bot.chat_model, "Say hello in one word.", 10)
        print(f"✅ Response: {response}")
        
        if "cannot connect" in response.lower() or "not responding" in response.lower():
            print("❌ Ollama connection issues detected")
            print("💡 Please ensure Ollama is running:")
            print("   1. Open terminal")
            print("   2. Run: ollama serve")
            print("   3. In another terminal, check: ollama list")
        else:
            print("✅ Ollama connection working!")
        
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        import traceback
        traceback.print_exc()

def test_embedding_warnings():
    """Test if torch warnings are suppressed"""
    print(f"\n🔇 Testing Torch Warning Suppression")
    print("=" * 40)
    
    try:
        import warnings
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from sentence_transformers import SentenceTransformer
            
            # Load model to trigger any warnings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = model.encode(["test sentence"])
            
            # Check if torch warnings were captured
            torch_warnings = [warning for warning in w if "torch" in str(warning.message).lower()]
            
            if torch_warnings:
                print(f"⚠️ {len(torch_warnings)} torch warnings still visible:")
                for warning in torch_warnings:
                    print(f"   {warning.message}")
            else:
                print("✅ No torch warnings detected")
                
            print(f"✅ Embedding test successful: shape {test_embedding.shape}")
        
    except Exception as e:
        print(f"❌ Error testing embeddings: {e}")

def check_ollama_status():
    """Check if Ollama is running"""
    print(f"\n🏥 Checking Ollama Service Status")
    print("=" * 40)
    
    try:
        import requests
        
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama is running")
            print(f"📋 Available models ({len(models)}):")
            for model in models:
                print(f"   - {model.get('name', 'Unknown')}")
        else:
            print(f"⚠️ Ollama responded with status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running or not accessible")
        print("💡 To start Ollama:")
        print("   1. Open terminal")
        print("   2. Run: ollama serve")
    except requests.exceptions.Timeout:
        print("❌ Ollama connection timed out")
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")

def main():
    """Run all connection tests"""
    print("🔧 Testing Ollama Connection Fixes")
    print("=" * 80)
    
    check_ollama_status()
    test_embedding_warnings()
    test_ollama_connection()
    
    print("\n" + "=" * 80)
    print("🏁 Connection tests completed!")
    print("\n💡 If Ollama isn't running:")
    print("   Terminal 1: ollama serve")
    print("   Terminal 2: ollama pull llama3.2:1b")
    print("   Terminal 3: ollama pull sqlcoder:7b")

if __name__ == "__main__":
    main()
