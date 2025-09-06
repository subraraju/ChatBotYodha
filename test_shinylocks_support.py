"""
Test the product support flow with uploaded PDFs
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_shinylocks_support():
    """Test product support flow with ShinyLocks 360 and measurements question"""
    print("🧪 Testing ShinyLocks 360 Product Support")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ Bot initialized and session started")
        
        # Simulate the complete customer service flow
        test_conversation = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "ShinyLocks 360",  # Select the product by name
            "Measurements of that product?"  # Ask about measurements
        ]
        
        for i, message in enumerate(test_conversation, 1):
            print(f"\n{'='*20} Message {i} {'='*20}")
            print(f"👤 User: {message}")
            
            # Process the message
            try:
                response, updated_session = bot.process_message(message, session)
                session = updated_session
                
                print(f"🤖 Bot Response:")
                print(f"   {response}")
                print(f"📊 Current State: {session.customer_state.value}")
                
                if hasattr(session, 'selected_product') and session.selected_product:
                    print(f"🎯 Selected Product: {session.selected_product}")
                    print(f"🔄 Help Attempts: {session.help_attempts}")
                
                if session.customer_id:
                    print(f"🆔 Customer ID: {session.customer_id}")
                
                # Show recent purchases when available
                if session.recent_purchases and i == 2:
                    print(f"🛍️ Recent Purchases Found: {len(session.recent_purchases)} items")
                    for j, purchase in enumerate(session.recent_purchases, 1):
                        print(f"     {j}. {purchase['product_name']} - {purchase['sale_date']}")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        # Test direct PDF search functionality
        print(f"\n{'='*20} Direct PDF Search Test {'='*20}")
        if session.selected_product:
            print(f"🔍 Testing direct PDF search for: {session.selected_product}")
            answer = bot._search_product_documentation(session.selected_product, "What are the measurements of this product?")
            
            if answer:
                print(f"✅ PDF Search Result:")
                print(f"   {answer}")
            else:
                print("❌ No answer found in PDF documentation")
        
        # Test manufacturer contact extraction
        print(f"\n{'='*20} Manufacturer Contact Test {'='*20}")
        if session.selected_product:
            contact_info = bot._get_manufacturer_contact(session.selected_product)
            print(f"📞 Manufacturer Contact Info:")
            print(f"   {contact_info}")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

def check_pdf_index():
    """Check if PDF index exists and show some info"""
    print("\n🗂️ Checking PDF Index Status")
    print("=" * 40)
    
    try:
        from pathlib import Path
        import pickle
        
        # Check index files
        index_dir = Path("data/index")
        faiss_index_path = index_dir / "faiss_vector_store.index"
        faiss_meta_path = index_dir / "faiss_vector_store.pkl"
        
        if faiss_index_path.exists() and faiss_meta_path.exists():
            print("✅ FAISS index files found")
            
            # Load metadata to see what's in the index
            with open(faiss_meta_path, 'rb') as f:
                metadata = pickle.load(f)
            
            chunks = metadata.get('chunks', [])
            print(f"📄 Total chunks in index: {len(chunks)}")
            print(f"🤖 Embedding model: {metadata.get('model_name', 'Unknown')}")
            
            # Look for ShinyLocks related content
            shinylocks_chunks = [chunk for chunk in chunks if 'shinylocks' in chunk.lower()]
            print(f"🔍 ShinyLocks related chunks: {len(shinylocks_chunks)}")
            
            if shinylocks_chunks:
                print("📝 Sample ShinyLocks content:")
                sample_chunk = shinylocks_chunks[0][:200] + "..." if len(shinylocks_chunks[0]) > 200 else shinylocks_chunks[0]
                print(f"   {sample_chunk}")
            
            # Look for measurement-related content
            measurement_chunks = [chunk for chunk in chunks if any(word in chunk.lower() for word in ['measurement', 'dimension', 'size', 'inches', 'cm', 'length', 'width', 'height'])]
            print(f"📏 Measurement related chunks: {len(measurement_chunks)}")
            
        else:
            print("❌ FAISS index files not found")
            print(f"   Looking for: {faiss_index_path}")
            print(f"   Looking for: {faiss_meta_path}")
            
            # Check if directory exists
            if index_dir.exists():
                files = list(index_dir.glob("*"))
                print(f"   Files in index directory: {[f.name for f in files]}")
            else:
                print("   Index directory doesn't exist")
                
    except Exception as e:
        print(f"❌ Error checking PDF index: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the comprehensive test"""
    print("🚀 ShinyLocks 360 Product Support Test")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check PDF index first
    check_pdf_index()
    
    # Test the product support flow
    test_shinylocks_support()
    
    print("\n" + "=" * 80)
    print(f"⏰ Test completed at: {datetime.now()}")
    print("🏁 Test finished!")

if __name__ == "__main__":
    main()
