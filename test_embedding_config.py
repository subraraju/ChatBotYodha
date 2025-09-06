"""
Test the improved chunking and new embedding model configuration
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_embedding_model():
    """Test the new embedding model download and functionality"""
    print("🧪 Testing New Embedding Model Configuration")
    print("=" * 60)
    
    try:
        # Import configuration
        from streamlit_customer_service import EMBEDDING_MODEL, EMBEDDING_MODEL_FALLBACK, CHUNK_SIZE, CHUNK_OVERLAP
        
        print(f"📊 Configuration:")
        print(f"   Primary Model: {EMBEDDING_MODEL}")
        print(f"   Fallback Model: {EMBEDDING_MODEL_FALLBACK}")
        print(f"   Chunk Size: {CHUNK_SIZE}")
        print(f"   Chunk Overlap: {CHUNK_OVERLAP}")
        
        # Test model loading
        from sentence_transformers import SentenceTransformer
        
        print(f"\n🔄 Attempting to load primary model: {EMBEDDING_MODEL}")
        try:
            model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"✅ Successfully loaded {EMBEDDING_MODEL}")
            
            # Test embedding generation
            test_text = ["This is a test sentence for embedding generation."]
            embeddings = model.encode(test_text)
            print(f"✅ Embedding shape: {embeddings.shape}")
            print(f"✅ Model working correctly!")
            
        except Exception as e:
            print(f"❌ Failed to load {EMBEDDING_MODEL}: {e}")
            print(f"🔄 Trying fallback model: {EMBEDDING_MODEL_FALLBACK}")
            
            model = SentenceTransformer(EMBEDDING_MODEL_FALLBACK)
            print(f"✅ Successfully loaded fallback model: {EMBEDDING_MODEL_FALLBACK}")
            
            # Test embedding generation
            test_text = ["This is a test sentence for embedding generation."]
            embeddings = model.encode(test_text)
            print(f"✅ Embedding shape: {embeddings.shape}")
            
    except Exception as e:
        print(f"❌ Error testing embedding model: {e}")
        import traceback
        traceback.print_exc()

def test_chunking_configuration():
    """Test the improved chunking configuration"""
    print(f"\n🧪 Testing Improved Chunking")
    print("=" * 40)
    
    try:
        from streamlit_customer_service import chunk_text, CHUNK_SIZE, CHUNK_OVERLAP
        
        # Create a sample large text
        sample_text = """
        ShinyLocks 360 – Best hair Straightening ever
        
        Price: $139.99
        
        Product Benefits: Metallic plates for all types of hairs, heavy duty.
        Shape: Flat, round edges, twisted
        Brand: ShinyLocks
        
        Measurements:
        Width (W): 1.5 inches
        Depth (D): 1.2 inches  
        Length (L): 12.0 inches
        Weight: 0.79 lbs (wire not included)
        
        Product Features:
        - Professional grade ceramic plates
        - Adjustable temperature control from 180°F to 450°F
        - Fast heating technology - ready in 30 seconds
        - Auto shut-off after 60 minutes for safety
        - 360-degree swivel cord for easy styling
        - Dual voltage for international travel
        
        Usage Instructions:
        1. Ensure hair is completely dry before use
        2. Plug in the device and wait for heating indicator
        3. Select desired temperature based on hair type
        4. Section hair into 1-2 inch strands
        5. Slowly glide the straightener from roots to tips
        6. Repeat as needed for desired results
        
        Care Instructions:
        - Unplug device after each use
        - Clean plates with a damp cloth when cool
        - Store in a safe, dry place
        - Do not immerse in water
        
        Warranty Information:
        - 2-year limited warranty on manufacturing defects
        - Warranty does not cover misuse or normal wear
        - Contact customer service for warranty claims
        
        Customer Support:
        Phone: (610) 555-2001
        Email: CRM@ShinyLocks.com
        Hours: Monday-Friday 9AM-6PM EST
        """ * 3  # Repeat to make it longer
        
        print(f"📄 Sample text length: {len(sample_text)} characters")
        
        # Test chunking
        chunks = chunk_text(sample_text)
        
        print(f"✅ Created {len(chunks)} chunks")
        print(f"📊 Chunk size configuration: {CHUNK_SIZE} chars, overlap: {CHUNK_OVERLAP} chars")
        
        # Show chunk information
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\n--- Chunk {i+1} (length: {len(chunk)}) ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
            
        print(f"\n✅ Chunking working with improved configuration!")
        
    except Exception as e:
        print(f"❌ Error testing chunking: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🚀 Testing Improved Embedding and Chunking Configuration")
    print("=" * 80)
    
    test_embedding_model()
    test_chunking_configuration()
    
    print("\n" + "=" * 80)
    print("🏁 Configuration testing completed!")

if __name__ == "__main__":
    main()
