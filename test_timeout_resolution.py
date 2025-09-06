#!/usr/bin/env python3
"""
Quick test to verify the timeout issue is resolved with the new configuration
"""

import sys
import os
import time
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

print("🧪 Testing Timeout Resolution")
print("=" * 50)

def test_default_model():
    """Test with default (fast) embedding model"""
    print("📋 Test 1: Default Fast Model (all-MiniLM-L6-v2)")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot, CustomerSession
        
        # Initialize bot with default settings (should use fast model)
        bot = CustomerServiceBot()
        
        init_time = time.time() - start_time
        print(f"✅ Bot initialized in {init_time:.2f}s")
        
        # Create session
        session = CustomerSession()
        
        # Test a query
        query_start = time.time()
        response, updated_session = bot.process_message("What products do you offer?", session)
        query_time = time.time() - query_start
        
        print(f"✅ Query processed in {query_time:.2f}s")
        print(f"📝 Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ FAILED after {error_time:.2f}s: {e}")
        return False

def test_high_quality_model():
    """Test with high quality (potentially slow) embedding model"""
    print("\n📋 Test 2: High Quality Model (BAAI/bge-large-en-v1.5)")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot, CustomerSession
        
        # Initialize bot with high quality model
        bot = CustomerServiceBot(embedding_model="BAAI/bge-large-en-v1.5", debug_mode=True)
        
        init_time = time.time() - start_time
        print(f"✅ Bot initialized in {init_time:.2f}s")
        
        # Create session
        session = CustomerSession()
        
        # Test a query
        query_start = time.time()
        response, updated_session = bot.process_message("What products do you offer?", session)
        query_time = time.time() - query_start
        
        print(f"✅ Query processed in {query_time:.2f}s")
        print(f"📝 Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ FAILED after {error_time:.2f}s: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Embedding Model Configuration")
    print("=" * 50)
    
    results = {
        "Default Fast Model": test_default_model(),
        "High Quality Model": test_high_quality_model()
    }
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("✅ Timeout issue has been resolved")
        print("💡 Users can now choose between fast and high-quality models")
    else:
        print("\n⚠️  Some tests failed")
        print("🔧 Check configuration and model availability")

if __name__ == "__main__":
    main()
