"""
Test the new debugging features and improved configuration
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_debug_mode():
    """Test the debug mode functionality"""
    print("🐛 Testing Debug Mode Functionality")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ Bot initialized and session started")
        
        # Set up the conversation to get to product support
        setup_messages = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "ShinyLocks 360"
        ]
        
        for message in setup_messages:
            response, session = bot.process_message(message, session)
        
        print(f"✅ Setup complete. Selected product: {session.selected_product}")
        
        # Now test with debug mode
        print(f"\n{'='*20} Testing Debug Mode {'='*20}")
        debug_question = "What are the measurements of this product?"
        
        print(f"👤 User: {debug_question}")
        
        # Test with debug mode enabled
        response, session = bot.process_message(debug_question, session, debug_mode=True)
        
        print(f"🤖 Bot Response:")
        print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")
        
        # Check if debug info was captured
        if hasattr(session, 'debug_info') and session.debug_info:
            debug_info = session.debug_info
            print(f"\n🐛 Debug Information Captured:")
            print(f"   Total chunks searched: {debug_info.get('chunks_searched', 'N/A')}")
            print(f"   Relevant chunks found: {debug_info.get('relevant_chunks_found', 'N/A')}")
            print(f"   Model used: {debug_info.get('model_used', 'N/A')}")
            print(f"   Final chunks used: {debug_info.get('filtered_chunks_count', 'N/A')}")
            print(f"   Context length: {debug_info.get('final_context_length', 'N/A')} chars")
            
            if 'top_chunks' in debug_info:
                print(f"   Retrieved chunks: {len(debug_info['top_chunks'])}")
                for i, chunk_info in enumerate(debug_info['top_chunks'][:2]):  # Show first 2
                    print(f"     Chunk {i+1}: Score {chunk_info.get('score', 'N/A'):.4f}")
                    chunk_preview = chunk_info.get('chunk_text', '')[:100] + "..."
                    print(f"       Preview: {chunk_preview}")
            
            if 'search_scores' in debug_info:
                print(f"   Search scores: {[f'{score:.4f}' for score in debug_info['search_scores'][:3]]}")
            
            print("✅ Debug mode working correctly!")
            
        else:
            print("❌ No debug information captured")
            
    except Exception as e:
        print(f"❌ Error testing debug mode: {e}")
        import traceback
        traceback.print_exc()

def test_configuration():
    """Test the improved configuration"""
    print(f"\n📊 Testing Configuration")
    print("=" * 40)
    
    try:
        from streamlit_customer_service import EMBEDDING_MODEL, EMBEDDING_MODEL_FALLBACK, CHUNK_SIZE, CHUNK_OVERLAP
        
        print(f"✅ Configuration loaded:")
        print(f"   Primary embedding model: {EMBEDDING_MODEL}")
        print(f"   Fallback embedding model: {EMBEDDING_MODEL_FALLBACK}")
        print(f"   Chunk size: {CHUNK_SIZE}")
        print(f"   Chunk overlap: {CHUNK_OVERLAP}")
        
        # Test chunking with configuration
        from streamlit_customer_service import chunk_text
        
        sample_text = "This is a test document. " * 200  # Create longer text
        chunks = chunk_text(sample_text)
        
        print(f"✅ Chunking test:")
        print(f"   Input length: {len(sample_text)} chars")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        import traceback
        traceback.print_exc()

def check_index_status():
    """Check the current FAISS index status"""
    print(f"\n🗂️ Checking FAISS Index Status")
    print("=" * 40)
    
    try:
        from pathlib import Path
        import pickle
        
        index_dir = Path("data/index")
        faiss_index_path = index_dir / "faiss_vector_store.index"
        faiss_meta_path = index_dir / "faiss_vector_store.pkl"
        
        if faiss_index_path.exists() and faiss_meta_path.exists():
            print("✅ FAISS index found")
            
            # Load metadata
            with open(faiss_meta_path, 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"📊 Index Information:")
            print(f"   Total chunks: {len(metadata.get('chunks', []))}")
            print(f"   Model used: {metadata.get('model_name', 'Unknown')}")
            print(f"   Chunk size config: {metadata.get('chunk_size', 'Unknown')}")
            print(f"   Chunk overlap config: {metadata.get('chunk_overlap', 'Unknown')}")
            print(f"   Embeddings shape: {metadata.get('embeddings_shape', 'Unknown')}")
            
            # Check for product-related content
            chunks = metadata.get('chunks', [])
            shinylocks_chunks = [c for c in chunks if 'shinylocks' in c.lower()]
            print(f"   ShinyLocks related chunks: {len(shinylocks_chunks)}")
            
        else:
            print("❌ FAISS index not found")
            print("   → Upload PDFs through admin panel to create index")
            
    except Exception as e:
        print(f"❌ Error checking index: {e}")

def main():
    """Run all debugging tests"""
    print("🚀 Testing Debugging Features and Configuration")
    print("=" * 80)
    
    check_index_status()
    test_configuration()
    test_debug_mode()
    
    print("\n" + "=" * 80)
    print("🏁 Debugging tests completed!")
    print("\n📝 To test in Streamlit:")
    print("   1. Run: streamlit run streamlit_customer_service.py")
    print("   2. Enable 'Debug Mode' toggle in sidebar")
    print("   3. Ask questions about uploaded products")
    print("   4. Check the debug information panel")

if __name__ == "__main__":
    main()
