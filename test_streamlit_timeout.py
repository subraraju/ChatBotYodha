#!/usr/bin/env python3
"""
Test script to reproduce the exact timeout issue occurring in Streamlit
"""

import time
import requests
import warnings
import os
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("🚨 Streamlit-Specific Timeout Issue Test")
print("=" * 80)

# Test within the exact same context as Streamlit
def test_streamlit_environment():
    """Test in the exact same environment as Streamlit"""
    print("🔍 Testing Streamlit Environment Simulation")
    print("=" * 60)
    
    try:
        # Initialize with the exact same imports and setup as the main app
        import sys
        sys.path.append('app')
        
        from app.chatbot.customer_service_bot import CustomerServiceBot
        from app.models.pydantic_models import CustomerSession
        
        print("✅ Imports successful")
        
        # Create session exactly like Streamlit does
        session = CustomerSession(
            session_id="test_session",
            customer_info="Test customer",
            conversation_history=[],
            context_data={}
        )
        
        print("✅ Session created")
        
        # Test both embedding models in sequence
        embedding_models = [
            "all-MiniLM-L6-v2",
            "BAAI/bge-large-en-v1.5"
        ]
        
        for model_name in embedding_models:
            print(f"\n🧪 Testing with {model_name}")
            print("-" * 40)
            
            start_time = time.time()
            
            try:
                # Initialize bot with specific embedding model
                bot = CustomerServiceBot(
                    embedding_model=model_name,
                    debug_mode=True
                )
                
                init_time = time.time() - start_time
                print(f"✅ Bot initialized in {init_time:.2f}s")
                
                # Test a query that would trigger PDF search
                test_message = "What products do you offer?"
                
                query_start = time.time()
                response = bot.process_message(test_message, session)
                query_time = time.time() - query_start
                
                print(f"✅ Query processed in {query_time:.2f}s")
                print(f"📝 Response length: {len(response.content)} chars")
                
                if hasattr(response, 'debug_info') and response.debug_info:
                    print(f"🔍 Retrieved chunks: {len(response.debug_info.get('retrieved_chunks', []))}")
                
            except requests.exceptions.Timeout as e:
                error_time = time.time() - start_time
                print(f"❌ TIMEOUT after {error_time:.2f}s: {e}")
                return False
            except Exception as e:
                error_time = time.time() - start_time
                print(f"❌ ERROR after {error_time:.2f}s: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def test_pdf_loading_timing():
    """Test PDF loading timing which might be causing issues"""
    print("\n🔍 Testing PDF Loading Timing")
    print("=" * 60)
    
    try:
        import sys
        sys.path.append('app')
        
        pdf_files_dir = Path("pdf_files")
        if not pdf_files_dir.exists():
            print("📁 No PDF files directory found - creating test environment")
            return True
            
        pdf_files = list(pdf_files_dir.glob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            print("📝 No PDF files to test")
            return True
            
        # Test index building time
        from app.chatbot.customer_service_bot import CustomerServiceBot
        
        models_to_test = ["all-MiniLM-L6-v2", "BAAI/bge-large-en-v1.5"]
        
        for model_name in models_to_test:
            print(f"\n🧪 Building index with {model_name}")
            start_time = time.time()
            
            try:
                bot = CustomerServiceBot(
                    embedding_model=model_name,
                    debug_mode=True
                )
                
                # Force index rebuild
                bot._build_vector_store()
                
                build_time = time.time() - start_time
                print(f"✅ Index built in {build_time:.2f}s")
                
            except Exception as e:
                error_time = time.time() - start_time
                print(f"❌ Index build failed after {error_time:.2f}s: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ PDF test failed: {e}")
        return False

def test_memory_pressure():
    """Test if memory pressure is causing the timeout"""
    print("\n🔍 Testing Memory Pressure")
    print("=" * 60)
    
    try:
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"📊 Initial memory usage: {initial_memory:.1f} MB")
        
        # Load embedding model and monitor memory
        from sentence_transformers import SentenceTransformer
        
        print("🔄 Loading BAAI/bge-large-en-v1.5...")
        model_start = time.time()
        
        model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        
        model_time = time.time() - model_start
        model_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"✅ Model loaded in {model_time:.2f}s")
        print(f"📊 Memory after model load: {model_memory:.1f} MB (+{model_memory - initial_memory:.1f} MB)")
        
        # Test Ollama connection under memory pressure
        print("🧪 Testing Ollama under memory pressure...")
        
        import sys
        sys.path.append('app')
        from app.chatbot.customer_service_bot import CustomerServiceBot
        
        ollama_start = time.time()
        bot = CustomerServiceBot(embedding_model="all-MiniLM-L6-v2")  # Use smaller model for bot
        
        # Test Ollama call
        response = bot._call_ollama("llama3.2:1b", "Test message", max_tokens=10)
        ollama_time = time.time() - ollama_start
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"✅ Ollama responded in {ollama_time:.2f}s")
        print(f"📊 Final memory usage: {final_memory:.1f} MB")
        print(f"📝 Response: {response[:50]}...")
        
        # Cleanup
        del model
        gc.collect()
        
        return True
        
    except ImportError:
        print("⚠️  psutil not available - skipping memory test")
        return True
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Streamlit Timeout Investigation")
    print("=" * 80)
    
    test_results = {
        "Streamlit Environment": test_streamlit_environment(),
        "PDF Loading": test_pdf_loading_timing(),
        "Memory Pressure": test_memory_pressure()
    }
    
    print("\n" + "=" * 80)
    print("📊 Test Results Summary:")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ All tests passed - issue may be environment-specific")
        print("💡 Suggestion: The timeout might be caused by:")
        print("   1. Streamlit's session state management")
        print("   2. Multiple concurrent requests")
        print("   3. File locking issues")
        print("   4. Streamlit's threading model")
    else:
        print("\n❌ Some tests failed - issue reproduced")

if __name__ == "__main__":
    main()
