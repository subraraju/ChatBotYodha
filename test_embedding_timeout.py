"""
Test case specifically for the BAAI/bge-large-en-v1.5 loading timeout issue
"""
import sys
import os
import time

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_embedding_model_loading_timeout():
    """Test the specific timeout issue with BAAI/bge-large-en-v1.5"""
    print("🔍 Testing BAAI/bge-large-en-v1.5 Loading Timeout Issue")
    print("=" * 70)
    
    try:
        print("📋 Testing scenario:")
        print("   1. Loading BAAI/bge-large-en-v1.5 (1.34GB model)")
        print("   2. Checking if loading causes Ollama timeout")
        print("   3. Measuring loading time")
        
        # Test 1: Check if model is already cached
        print(f"\n🧪 Test 1: Checking model cache status")
        from pathlib import Path
        cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
        bge_model_dirs = list(cache_dir.glob("*bge-large-en-v1.5*")) if cache_dir.exists() else []
        
        if bge_model_dirs:
            print(f"✅ Model cache found: {len(bge_model_dirs)} directories")
            for dir_path in bge_model_dirs:
                print(f"   {dir_path.name}")
        else:
            print("❌ Model not cached - first load will be slow")
        
        # Test 2: Time the model loading
        print(f"\n🧪 Test 2: Timing model loading")
        start_time = time.time()
        
        try:
            from sentence_transformers import SentenceTransformer
            print("   Loading BAAI/bge-large-en-v1.5...")
            model = SentenceTransformer('BAAI/bge-large-en-v1.5')
            load_time = time.time() - start_time
            print(f"✅ Model loaded successfully in {load_time:.2f} seconds")
            
            # Test embedding generation
            test_embedding = model.encode(["Test sentence for embedding"])
            print(f"✅ Embedding generated: shape {test_embedding.shape}")
            
        except Exception as e:
            load_time = time.time() - start_time
            print(f"❌ Model loading failed after {load_time:.2f} seconds: {e}")
            return False
        
        # Test 3: Test if this affects Ollama calls
        print(f"\n🧪 Test 3: Testing Ollama after embedding model load")
        try:
            from chatbot.customer_service_bot import CustomerServiceBot
            bot = CustomerServiceBot()
            
            # Try a simple Ollama call
            response = bot._call_ollama(bot.chat_model, "Say 'test' in one word", 5)
            print(f"✅ Ollama response: {response}")
            
            if "timed out" in response.lower():
                print("❌ Ollama timeout detected after embedding model load")
                return False
            else:
                print("✅ Ollama working normally after embedding model load")
                
        except Exception as e:
            print(f"❌ Error testing Ollama: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in timeout test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_model_alternatives():
    """Test different embedding models to find faster alternatives"""
    print(f"\n⚡ Testing Alternative Embedding Models")
    print("=" * 50)
    
    models_to_test = [
        'all-MiniLM-L6-v2',  # Small, fast
        'all-mpnet-base-v2',  # Medium size, good quality
        'BAAI/bge-base-en-v1.5',  # Smaller version of BGE
        'BAAI/bge-large-en-v1.5'  # The problematic large model
    ]
    
    results = []
    
    for model_name in models_to_test:
        print(f"\n📊 Testing {model_name}...")
        try:
            start_time = time.time()
            
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            load_time = time.time() - start_time
            
            # Test embedding
            test_text = ["This is a test sentence for measuring embedding quality and speed."]
            embed_start = time.time()
            embedding = model.encode(test_text)
            embed_time = time.time() - embed_start
            
            results.append({
                'model': model_name,
                'load_time': load_time,
                'embed_time': embed_time,
                'dimensions': embedding.shape[1],
                'success': True
            })
            
            print(f"   ✅ Load time: {load_time:.2f}s")
            print(f"   ✅ Embedding time: {embed_time:.4f}s")
            print(f"   ✅ Dimensions: {embedding.shape[1]}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'model': model_name,
                'load_time': None,
                'embed_time': None,
                'dimensions': None,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n📈 Performance Summary:")
    print(f"{'Model':<25} {'Load Time':<12} {'Embed Time':<12} {'Dimensions':<12}")
    print("-" * 65)
    
    for result in results:
        if result['success']:
            print(f"{result['model']:<25} {result['load_time']:<12.2f} {result['embed_time']:<12.4f} {result['dimensions']:<12}")
        else:
            print(f"{result['model']:<25} {'FAILED':<12} {'FAILED':<12} {'FAILED':<12}")
    
    return results

def test_ollama_timeout_during_embedding():
    """Specifically test if Ollama times out while embedding model is loading"""
    print(f"\n🔄 Testing Concurrent Ollama + Embedding Loading")
    print("=" * 55)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize bot first
        bot = CustomerServiceBot()
        print("✅ Bot initialized")
        
        # Test Ollama before embedding load
        response1 = bot._call_ollama(bot.chat_model, "Say 'before'", 5)
        print(f"✅ Ollama before embedding load: {response1}")
        
        # Now load the large embedding model while testing Ollama
        print("🔄 Loading large embedding model...")
        import threading
        import time
        
        def load_embedding():
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('BAAI/bge-large-en-v1.5')
            return model
        
        # Start embedding loading in background
        embedding_thread = threading.Thread(target=load_embedding)
        embedding_thread.start()
        
        # Wait a bit then test Ollama
        time.sleep(2)
        print("🧪 Testing Ollama while embedding model loads...")
        response2 = bot._call_ollama(bot.chat_model, "Say 'during'", 5)
        print(f"📝 Ollama during embedding load: {response2}")
        
        # Wait for embedding to finish
        embedding_thread.join()
        print("✅ Embedding model loading completed")
        
        # Test Ollama after
        response3 = bot._call_ollama(bot.chat_model, "Say 'after'", 5)
        print(f"✅ Ollama after embedding load: {response3}")
        
        # Check for timeouts
        if any("timed out" in resp.lower() for resp in [response1, response2, response3]):
            print("❌ Timeout detected during the process")
            return False
        else:
            print("✅ No timeouts detected")
            return True
            
    except Exception as e:
        print(f"❌ Error in concurrent test: {e}")
        return False

def main():
    """Run all timeout-specific tests"""
    print("🚨 BAAI/bge-large-en-v1.5 Timeout Issue Investigation")
    print("=" * 80)
    
    test1_success = test_embedding_model_loading_timeout()
    test_embedding_model_alternatives()
    test2_success = test_ollama_timeout_during_embedding()
    
    print("\n" + "=" * 80)
    print("📊 Test Results Summary:")
    print(f"   Embedding model loading: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Concurrent Ollama/Embedding: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if not test1_success or not test2_success:
        print("\n💡 Recommended fixes:")
        print("   1. Use smaller embedding model (all-mpnet-base-v2)")
        print("   2. Pre-load embedding model separately")
        print("   3. Increase Ollama timeout further")
        print("   4. Load embedding model async")
    else:
        print("\n✅ All tests passed - issue may be resolved!")

if __name__ == "__main__":
    main()
