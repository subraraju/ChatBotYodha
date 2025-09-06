import streamlit as st
import sys
import os
from datetime import datetime
import json
import io
import traceback
import re

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# ===== CONFIGURATION =====
# Embedding Model Configuration
# Using all-mpnet-base-v2 as default for best compatibility and good quality
EMBEDDING_MODEL_DEFAULT = 'all-mpnet-base-v2'  # Reliable, good quality, 768 dimensions
EMBEDDING_MODEL_FAST = 'all-MiniLM-L6-v2'  # Fast fallback option, 384 dimensions
EMBEDDING_MODEL_FALLBACK = 'all-MiniLM-L6-v2'  # Fallback if main model fails

# Text Chunking Configuration  
CHUNK_SIZE = 4000  # Increased from 1000 for better context
CHUNK_OVERLAP = 800  # Increased proportionally

# Configure the page
st.set_page_config(
    page_title=f"Yodha - {os.getenv('COMPANY_NAME', 'Contoso')} Customer Service", 
    page_icon="💬", 
    layout="centered"
)

def enhance_response_formatting(response_text: str) -> str:
    """
    Enhanced function to automatically bold key parts of bot responses.
    
    Args:
        response_text: The original bot response text
        
    Returns:
        Enhanced response with improved bold formatting
    """
    if not response_text:
        return response_text
    
    # Skip if already heavily formatted (to avoid over-formatting)
    if response_text.count('**') >= 6:
        return response_text
    
    # More selective patterns to avoid over-formatting
    patterns = [
        # Direct answers at start of response
        (r'^(Yes|No|Absolutely|Certainly|Definitely|Of course)', r'**\1**'),
        (r'\b(The answer is|The solution is)\b', r'**\1**'),
        
        # Key actions and recommendations
        (r'\b(I recommend|You should|Please try|Follow these steps)\b', r'**\1**'),
        (r'\b(Important|Note|Remember)\b', r'**\1**'),
        
        # Prices and specific numbers
        (r'\$(\d+(?:\.\d{2})?)\b', r'**$\1**'),
        (r'\b(\d+(?:\.\d+)?%)\b', r'**\1**'),
        
        # Key customer service phrases
        (r'\b(in stock|out of stock|available|unavailable|warranty|guarantee)\b', r'**\1**'),
        (r'\b(contact support|call us|email us)\b', r'**\1**'),
        
        # Step numbers only
        (r'\b(Step \d+)\b', r'**\1**'),
        
        # Status words that are important
        (r'\b(working|not working|broken|fixed|resolved)\b', r'**\1**'),
    ]
    
    # Apply patterns selectively
    enhanced_text = response_text
    for pattern, replacement in patterns:
        enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
    
    # Bold the first sentence only if it's a clear direct answer and short
    sentences = enhanced_text.split('. ')
    if (sentences and len(sentences[0]) < 80 and 
        not sentences[0].startswith('**') and
        any(word in sentences[0].lower() for word in ['yes', 'no', 'available', 'can help'])):
        sentences[0] = f"**{sentences[0].strip()}**"
        enhanced_text = '. '.join(sentences)
    
    return enhanced_text

def _safe_model_init(model_name: str, device: str = 'cpu'):
    """Safely initialize SentenceTransformer with PyTorch compatibility fixes"""
    import torch
    import tempfile
    import shutil
    from pathlib import Path
    
    # Critical fix for '__path__._path' PyTorch error
    try:
        # Force PyTorch to use safe loading
        original_load = torch.load
        
        def safe_load(*args, **kwargs):
            kwargs['map_location'] = device
            kwargs['weights_only'] = False  # Allow pickle loading
            return original_load(*args, **kwargs)
        
        # Temporarily patch torch.load
        torch.load = safe_load
        
        try:
            # Method 1: Force torch to use safe settings
            torch.set_grad_enabled(False)
            if hasattr(torch.backends, 'cudnn'):
                torch.backends.cudnn.enabled = False
            
            # Method 2: Use a temporary cache directory to avoid path issues
            temp_cache = tempfile.mkdtemp(prefix='st_cache_')
            
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(model_name, device=device, cache_folder=temp_cache)
                return model
            finally:
                # Clean up temp cache
                if Path(temp_cache).exists():
                    shutil.rmtree(temp_cache, ignore_errors=True)
                    
        finally:
            # Restore original torch.load
            torch.load = original_load
            
    except Exception as e:
        # Fallback: try with minimal settings
        from sentence_transformers import SentenceTransformer
        torch.set_grad_enabled(False)
        return SentenceTransformer(model_name, device=device)

def _fresh_model_download(model_name: str):
    """Download model fresh without cache to avoid corrupted cache issues"""
    import torch
    import shutil
    from pathlib import Path
    from sentence_transformers import SentenceTransformer
    
    try:
        # Clear any existing cache for this model
        cache_dir = Path.home() / '.cache' / 'torch' / 'sentence_transformers'
        model_cache = cache_dir / model_name.replace('/', '_')
        
        if model_cache.exists():
            st.info(f"🧹 Clearing cache for {model_name}")
            shutil.rmtree(model_cache, ignore_errors=True)
        
        # Force fresh download
        torch.set_grad_enabled(False)
        model = SentenceTransformer(model_name, device='cpu')
        return model
        
    except Exception as e:
        raise e

def initialize_bot(embedding_model: str = None, debug_mode: bool = False):
    """Initialize the customer service bot with configurable embedding model"""
    try:
        from app.chatbot.customer_service_bot import CustomerServiceBot
        if embedding_model is None:
            embedding_model = EMBEDDING_MODEL_DEFAULT
            
        # Show initialization progress
        with st.spinner(f"🚀 Initializing bot with {embedding_model}..."):
            # Preload embedding model to avoid delays during conversations
            st.info(f"Loading embedding model: {embedding_model}")
            
            # Initialize bot with preloading
            bot = CustomerServiceBot(embedding_model=embedding_model, debug_mode=debug_mode)
            
            # Preload the embedding model with enhanced PyTorch compatibility
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                import os
                import warnings
                
                # Suppress PyTorch warnings that can cause issues
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", category=FutureWarning)
                
                # Set environment variables to help with PyTorch compatibility
                os.environ['TOKENIZERS_PARALLELISM'] = 'false'
                os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
                
                st.info(f"🔧 Initializing {embedding_model} with enhanced compatibility...")
                
                # Clear any existing torch cache that might cause issues
                if hasattr(torch, 'cuda') and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                model = None
                init_attempts = [
                    # Attempt 1: Safe CPU initialization with cache disabled
                    lambda: SentenceTransformer(embedding_model, device='cpu', cache_folder=None),
                    # Attempt 2: Force CPU with explicit torch settings and safe loading
                    lambda: _safe_model_init(embedding_model, 'cpu'),
                    # Attempt 3: Fresh download without cache
                    lambda: _fresh_model_download(embedding_model),
                    # Attempt 4: BGE models with trust_remote_code
                    lambda: SentenceTransformer(embedding_model, trust_remote_code=True, device='cpu') if "bge" in embedding_model.lower() else None,
                    # Attempt 5: Alternative model fallback
                    lambda: SentenceTransformer('all-MiniLM-L6-v2', device='cpu') if embedding_model != 'all-MiniLM-L6-v2' else None,
                    # Attempt 6: Minimal initialization
                    lambda: SentenceTransformer('paraphrase-MiniLM-L3-v2', device='cpu'),
                ]
                
                for i, attempt in enumerate(init_attempts, 1):
                    try:
                        result = attempt()
                        if result is None:
                            continue
                        model = result
                        actual_model = getattr(model, 'model_name', embedding_model)
                        st.info(f"✅ Model '{actual_model}' loaded successfully with method {i}")
                        break
                    except Exception as attempt_error:
                        error_msg = str(attempt_error)
                        st.warning(f"⚠️ Attempt {i} failed: {error_msg[:80]}...")
                        continue
                
                if model is None:
                    raise Exception("All initialization attempts failed")
                
                # Test encoding to ensure model is working
                try:
                    # Force CPU encoding without tensor conversion to avoid device issues
                    test_result = model.encode(["test sentence"], 
                                             convert_to_tensor=False, 
                                             device='cpu' if hasattr(model, 'device') else None,
                                             show_progress_bar=False)
                    
                    if test_result is not None and len(test_result) > 0:
                        st.success(f"✅ {embedding_model} loaded and tested successfully")
                    else:
                        raise Exception("Model encoding test failed")
                        
                except Exception as encoding_error:
                    st.warning(f"⚠️ Encoding test failed: {encoding_error}")
                    # Don't fail completely, just warn
                
                # Clean up model from memory
                if model is not None:
                    del model
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
            except Exception as e:
                print(f"❌ Model preload failed: {e}")
                print(traceback.format_exc())
                st.error(f"❌ Model preload failed: {str(e)[:100]}...")
                st.warning("⚠️ Embedding model failed to load. The bot will work but document search may be unavailable.")
                st.info("💡 Try switching to 'all-MiniLM-L6-v2' model which is more compatible.")
            
        return bot
    except Exception as e:
        st.error(f"Failed to initialize bot: {e}")
        print(traceback.format_exc())
        return None

def admin_authentication():
    """Simple admin authentication"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.subheader("🔐 Admin Authentication")
        username = st.text_input("Username:", key="admin_username")
        password = st.text_input("Password:", type="password", key="admin_password")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Login"):
                if username and password:  # Accept any non-empty credentials for now
                    st.session_state.admin_authenticated = True
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Please enter username and password")
        return False
    return True

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        import io
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        st.error("PyPDF2 not installed. Please install: pip install PyPDF2")
        return None
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

def chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Split text into chunks with configurable size"""
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks
    except ImportError:
        # Fallback simple chunking if langchain not available
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

def export_conversation_as_json():
    """Export the current conversation as a JSON file for download"""
    if 'session' not in st.session_state or not hasattr(st.session_state.session, 'messages') or not st.session_state.session.messages:
        st.warning("No conversation to export.")
        return None
    
    session = st.session_state.session
    
    # Create conversation export data
    export_data = {
        "export_metadata": {
            "timestamp": datetime.now().isoformat(),
            "company_name": os.getenv("COMPANY_NAME", "Contoso"),
            "session_id": getattr(session, 'session_id', 'unknown'),
            "total_messages": len(session.messages),
            "embedding_model": st.session_state.get('current_embedding_model', 'unknown'),
            "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
            "app_version": "1.0",
            "export_format": "customer_service_chat"
        },
        "session_info": {
            "customer_id": getattr(session, 'customer_id', None),
            "customer_state": getattr(session, 'customer_state', {}).value if hasattr(getattr(session, 'customer_state', {}), 'value') else 'unknown',
            "customer_info": getattr(session, 'customer_info', {}),
            "recent_purchases": getattr(session, 'recent_purchases', []),
            "session_start_time": getattr(session, 'start_time', datetime.now().isoformat())
        },
        "conversation": []
    }
    
    # Add messages to export
    for i, message in enumerate(session.messages):
        message_data = {
            "message_id": i + 1,
            "timestamp": getattr(message, 'timestamp', datetime.now().isoformat()),
            "role": getattr(message, 'role', 'unknown'),
            "content": getattr(message, 'content', ''),
            "metadata": {
                "message_type": getattr(message, 'type', 'text'),
                "has_debug_info": hasattr(message, 'debug_info') and message.debug_info is not None,
                "debug_info": getattr(message, 'debug_info', None) if hasattr(message, 'debug_info') else None
            }
        }
        export_data["conversation"].append(message_data)
    
    # Convert to JSON string with proper formatting
    json_string = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    
    return json_string

def create_embeddings(chunks, vector_store_type="FAISS"):
    """Create embeddings and store in vector database with configurable model"""
    try:
        # Use sentence-transformers for embeddings
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from pathlib import Path
        import warnings
        import torch
        
        # Suppress torch warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="torch")
        
        # Try to initialize the primary embedding model with fallback
        model_name = EMBEDDING_MODEL_DEFAULT
        model = None
        
        # Try models in order of preference with proper error handling
        model_attempts = [
            EMBEDDING_MODEL_DEFAULT,
            "all-mpnet-base-v2",  # Good alternative
            EMBEDDING_MODEL_FALLBACK,  # Final fallback
        ]
        
        for attempt_model in model_attempts:
            try:
                st.info(f"Loading embedding model: {attempt_model}")
                
                # Enhanced compatibility approach for all models
                model = None
                init_methods = [
                    # Method 1: Force CPU device
                    lambda: SentenceTransformer(attempt_model, device='cpu'),
                    # Method 2: BGE models with trust_remote_code
                    lambda: SentenceTransformer(attempt_model, trust_remote_code=True, device='cpu') if "bge" in attempt_model.lower() else None,
                    # Method 3: Default initialization
                    lambda: SentenceTransformer(attempt_model),
                    # Method 4: Initialize then move to CPU
                    lambda: SentenceTransformer(attempt_model).to('cpu'),
                ]
                
                for method_num, init_method in enumerate(init_methods, 1):
                    try:
                        result = init_method()
                        if result is None:
                            continue
                        model = result
                        st.info(f"✅ Model loaded with initialization method {method_num}")
                        break
                    except Exception as method_error:
                        st.warning(f"⚠️ Init method {method_num} failed: {str(method_error)[:50]}...")
                        continue
                
                if model is None:
                    raise Exception(f"All initialization methods failed for {attempt_model}")
                
                # Test encoding immediately to catch device issues
                test_encoding = model.encode(["test sentence"], 
                                           convert_to_tensor=False,
                                           device='cpu' if hasattr(model, 'device') else None)
                if test_encoding is not None:
                    model_name = attempt_model
                    st.success(f"Successfully loaded and tested {attempt_model}")
                    break
                else:
                    raise Exception("Model encoding test failed")
                        
            except Exception as e:
                st.warning(f"Failed to load {attempt_model}: {str(e)[:100]}...")
                if model is not None:
                    del model
                    model = None
                continue
        
        if model is None:
            raise Exception("All embedding models failed to load")
        
        # Generate embeddings with enhanced compatibility
        st.info(f"Generating embeddings for {len(chunks)} chunks with {model_name}...")
        try:
            # Multiple encoding strategies for maximum compatibility
            embeddings = None
            encoding_methods = [
                # Method 1: CPU with progress bar
                lambda: model.encode(chunks, convert_to_tensor=False, device='cpu', show_progress_bar=True),
                # Method 2: CPU without progress bar
                lambda: model.encode(chunks, convert_to_tensor=False, device='cpu', show_progress_bar=False),
                # Method 3: Default without device specification
                lambda: model.encode(chunks, convert_to_tensor=False, show_progress_bar=False),
                # Method 4: Batch processing approach
                lambda: model.encode(chunks, batch_size=16, convert_to_tensor=False, show_progress_bar=False),
            ]
            
            for method_num, encoding_method in enumerate(encoding_methods, 1):
                try:
                    st.info(f"Trying encoding method {method_num}...")
                    embeddings = encoding_method()
                    embeddings = np.array(embeddings)  # Ensure numpy array format
                    st.success(f"✅ Embeddings generated successfully with method {method_num}")
                    break
                except Exception as enc_error:
                    st.warning(f"⚠️ Encoding method {method_num} failed: {str(enc_error)[:80]}...")
                    continue
            
            if embeddings is None:
                raise Exception("All embedding generation methods failed")
                
        except Exception as e:
            st.error(f"Failed to generate embeddings: {e}")
            raise e
        
        # Create data/index directory
        index_dir = Path("data/index")
        index_dir.mkdir(parents=True, exist_ok=True)
        
        if vector_store_type == "FAISS":
            import faiss
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype('float32'))
            
            # Save FAISS index
            faiss.write_index(index, str(index_dir / "faiss_vector_store.index"))
            
            # Save chunks and metadata
            import pickle
            metadata = {
                'chunks': chunks,
                'embeddings_shape': embeddings.shape,
                'model_name': model_name,
                'chunk_size': CHUNK_SIZE,
                'chunk_overlap': CHUNK_OVERLAP
            }
            with open(index_dir / "faiss_vector_store.pkl", 'wb') as f:
                pickle.dump(metadata, f)
                
            return True, f"FAISS index created with {len(chunks)} chunks"
            
        else:
            return False, f"Unsupported vector store type: {vector_store_type}"
            
    except Exception as e:
        return False, f"Error creating embeddings: {str(e)}"

def main():
    # Create header with title and logo on the same line using HTML
    try:
        logo_path = "contoso.png"
        if os.path.exists(logo_path):
            # Convert image to base64 for inline display
            import base64
            with open(logo_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            # Create inline header with logo
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <h1 style="margin: 0; flex-grow: 1;">   Yodha - Customer Service Chat</h1>
                    <img src="data:image/png;base64,{img_base64}" style="height: 60px; margin-left: 20px;">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.title("💬 Yodha - Customer Service Chat")
            st.warning("Logo not found")
    except Exception as e:
        st.title("💬 Yodha - Customer Service Chat")
        st.error(f"Logo error: {str(e)}")
    
    # Get company name from environment or default
    company_name = os.getenv("COMPANY_NAME", "Contoso")
    llm_provider = os.getenv("LLM_PROVIDER", "openai").upper()
    
    st.markdown(f"Welcome to {company_name} customer service! I'm Yodha, here to help you with your account and products.")
    
    # Configure sidebar first to get user preferences
    with st.sidebar:
        st.header("Session Info")
        
        # Show current configuration
        st.info(f"**Company:** {company_name}")
        st.info(f"**LLM Provider:** {llm_provider}")
        
        # Debug Mode Toggle (default to True)
        debug_mode = st.checkbox("🐛 Debug Mode", value=True, help="Show debugging information for PDF search")
        
        # Embedding Model Selection
        st.markdown("---")
        st.subheader("🧠 AI Configuration")
        
        embedding_model = st.selectbox(
            "Embedding Model",
            options=[
                EMBEDDING_MODEL_DEFAULT,
                EMBEDDING_MODEL_FAST,
                "BAAI/bge-base-en-v1.5",
                "BAAI/bge-large-en-v1.5"
            ],
            index=0,
            help=f"""
            Choose embedding model:
            • {EMBEDDING_MODEL_DEFAULT}: Reliable, good quality (438MB, 768 dims)
            • {EMBEDDING_MODEL_FAST}: Fast, reliable (90MB, 384 dims)
            • BAAI/bge-base-en-v1.5: Good quality (438MB, 768 dims) - May have compatibility issues
            • BAAI/bge-large-en-v1.5: High quality (1.34GB, 1024 dims) - May have compatibility issues
            """
        )
        
        # Show model info
        if embedding_model == EMBEDDING_MODEL_DEFAULT:
            st.info("✅ High quality model selected (may take longer to load)")
        elif embedding_model == EMBEDDING_MODEL_FAST:
            st.success("✅ Fast model selected")
            
        st.markdown("---")
        
        # Session Information
        # Only show state if it's not unknown
        if 'session' in st.session_state and st.session_state.session.customer_state.value != "unknown":
            st.write(f"**State:** {st.session_state.session.customer_state.value}")
        
        if 'session' in st.session_state and st.session_state.session.customer_info:
            st.write("**Customer Info:**")
            for key, value in st.session_state.session.customer_info.items():
                st.write(f"- {key}: {value}")
        
        if 'session' in st.session_state and st.session_state.session.customer_id:
            st.write(f"**Customer ID:** {st.session_state.session.customer_id}")
            
        if 'session' in st.session_state and st.session_state.session.recent_purchases:
            st.write("**Recent Purchases:**")
            for purchase in st.session_state.session.recent_purchases:
                st.write(f"- {purchase['product_name']}")
        
        if 'session' in st.session_state:
            st.write(f"**Messages:** {len(st.session_state.session.messages)}")
        
        # Download Conversation Button
        st.markdown("---")
        st.subheader("💾 Export & Session")
        
        # Check if there are messages to export
        if 'session' in st.session_state and hasattr(st.session_state.session, 'messages') and st.session_state.session.messages:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
            
            # Export conversation button
            json_data = export_conversation_as_json()
            if json_data:
                st.download_button(
                    label="📥 Download Conversation",
                    data=json_data,
                    file_name=filename,
                    mime="application/json",
                    help="Download the current conversation as a JSON file"
                )
                
                # Show conversation stats
                message_count = len(st.session_state.session.messages)
                st.caption(f"📊 {message_count} messages ready to export")
                
            # Close Session Button
            if st.button("🔚 Close Session", type="secondary", help="Close current session and store conversation"):
                if st.session_state.session and st.session_state.session.customer_id:
                    # Use the bot's close session method
                    closing_message, storage_success = st.session_state.bot.close_session_and_store_conversation(
                        st.session_state.session, "ui_closed"
                    )
                    
                    if storage_success:
                        st.success("✅ Session closed and conversation stored successfully!")
                        st.info(closing_message)
                    else:
                        st.warning("⚠️ Session closed but conversation storage failed")
                        st.info(closing_message)
                    
                    # Reset session
                    st.session_state.session = st.session_state.bot.start_new_session()
                    st.rerun()
                else:
                    st.info("No active customer session to close. Starting new session...")
                    st.session_state.session = st.session_state.bot.start_new_session()
                    st.rerun()
        else:
            st.info("💬 Start a conversation to enable export and session management")
        
        # Admin Task Button
        st.markdown("---")
        if st.button("🔧 Admin Task"):
            st.session_state.show_admin = True
    
    # Initialize session state with selected configuration
    if 'bot' not in st.session_state or st.session_state.get('current_embedding_model') != embedding_model:
        # Reinitialize bot if embedding model changed
        st.session_state.bot = initialize_bot(embedding_model=embedding_model, debug_mode=debug_mode)
        st.session_state.current_embedding_model = embedding_model
        if not st.session_state.bot:
            st.error("Could not initialize the customer service bot")
            return
        # Reset session when bot changes
        st.session_state.pop('session', None)
    
    if 'session' not in st.session_state:
        # Create new session (welcome message is automatically added)
        st.session_state.session = st.session_state.bot.start_new_session()
    
    # Display chat messages
    st.subheader("Chat")
    
    # Create a container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display all messages in chronological order
        for i, message in enumerate(st.session_state.session.messages):
            if message.role == "user":
                st.markdown(f"**👤 You:** {message.content}")
            else:
                # Enhance bot response formatting
                enhanced_content = enhance_response_formatting(message.content)
                st.markdown(f"**🤖 Yodha, the Assistant:** {enhanced_content}")
            
            # Add separator except for the last message
            if i < len(st.session_state.session.messages) - 1:
                st.markdown("---")
    
    # Show debug information if debug mode is enabled and available
    if debug_mode and hasattr(st.session_state.session, 'debug_info') and st.session_state.session.debug_info:
        with st.expander("🐛 Debug Information - Last PDF Search", expanded=True):
            debug_info = st.session_state.session.debug_info
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Total chunks searched:** {debug_info.get('chunks_searched', 'N/A')}")
                st.write(f"**Relevant chunks found:** {debug_info.get('relevant_chunks_found', 'N/A')}")
                st.write(f"**Final chunks used:** {debug_info.get('filtered_chunks_count', 'N/A')}")
                st.write(f"**Model used:** {debug_info.get('model_used', 'N/A')}")
            
            with col2:
                st.write(f"**Filter keywords:** {', '.join(debug_info.get('filter_keywords', []))}")
                st.write(f"**Context length:** {debug_info.get('final_context_length', 'N/A')} chars")
                st.write(f"**Prompt length:** {debug_info.get('prompt_length', 'N/A')} chars")
                if 'error' in debug_info:
                    st.error(f"**Error:** {debug_info['error']}")
            
            # Show retrieved chunks
            if 'top_chunks' in debug_info and debug_info['top_chunks']:
                st.subheader("📄 Retrieved Chunks (ordered by relevance)")
                for i, chunk_info in enumerate(debug_info['top_chunks']):
                    # Use a container instead of expander to avoid nesting
                    chunk_container = st.container()
                    with chunk_container:
                        st.markdown(f"**Chunk {i+1}** (Score: {chunk_info.get('score', 'N/A'):.4f})")
                        # Show chunk content in a code block for better readability
                        st.code(chunk_info.get('full_chunk', 'No content'), language='text')
                        st.caption(f"Chunk Index: {chunk_info.get('chunk_index', 'N/A')}")
                        st.markdown("---")  # Separator between chunks
            
            # Show search scores
            if 'search_scores' in debug_info and debug_info['search_scores']:
                st.subheader("📊 Search Scores")
                st.write("Lower scores indicate better matches (L2 distance)")
                score_data = {f"Chunk {i+1}": score for i, score in enumerate(debug_info['search_scores'])}
                st.bar_chart(score_data)
    
    # Add New Session button to main sidebar
    with st.sidebar:
        if st.button("🔄 New Session"):
            # Create new session (welcome message is automatically added)
            st.session_state.session = st.session_state.bot.start_new_session()
            st.rerun()
    
    # Admin Task Modal/Window
    if 'show_admin' not in st.session_state:
        st.session_state.show_admin = False
    
    if st.session_state.show_admin:
        # Create admin panel in the same window
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 8, 1])
            with col2:
                st.markdown("### 🔧 Admin Task Panel")
                
                # Close button
                if st.button("❌ Close", key="close_admin"):
                    st.session_state.show_admin = False
                    st.session_state.admin_authenticated = False  # Reset auth
                    st.rerun()
                
                # Admin authentication and functionality
                if admin_authentication():
                    st.subheader("📁 Document Management")
                    
                    # Vector store type selection
                    vector_store_type = st.selectbox(
                        "Vector Store Type:",
                        ["FAISS", "ChromaDB"],
                        help="Choose the vector database type for storing embeddings"
                    )
                    
                    # File upload section
                    st.subheader("📤 Upload Documents")
                    uploaded_files = st.file_uploader(
                        "Choose PDF files",
                        type="pdf",
                        accept_multiple_files=True,
                        help="Upload one or more PDF files to process"
                    )
                    
                    if uploaded_files:
                        st.write(f"📄 {len(uploaded_files)} file(s) selected")
                        
                        # Show file details
                        for file in uploaded_files:
                            st.write(f"- {file.name} ({file.size:,} bytes)")
                        
                        if st.button("🚀 Process Documents", type="primary"):
                            with st.spinner("Processing documents..."):
                                try:
                                    from pathlib import Path
                                    
                                    # Create data/docs directory
                                    docs_dir = Path("data/docs")
                                    docs_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    all_chunks = []
                                    processed_files = []
                                    
                                    # Process each file
                                    for file in uploaded_files:
                                        st.info(f"Processing {file.name}...")
                                        
                                        # Save file
                                        file_path = docs_dir / file.name
                                        with open(file_path, "wb") as f:
                                            f.write(file.getvalue())
                                        
                                        # Extract text
                                        file.seek(0)  # Reset file pointer
                                        text = extract_text_from_pdf(file)
                                        
                                        if text:
                                            # Chunk text using configured parameters
                                            chunks = chunk_text(text)  # Uses CHUNK_SIZE and CHUNK_OVERLAP from config
                                            all_chunks.extend(chunks)
                                            processed_files.append(file.name)
                                            st.success(f"✅ {file.name}: {len(chunks)} chunks created")
                                            st.info(f"   Using chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")
                                        else:
                                            st.error(f"❌ Failed to extract text from {file.name}")
                                    
                                    if all_chunks:
                                        # Create embeddings and vector store
                                        st.info(f"Creating {vector_store_type} vector store with {len(all_chunks)} chunks...")
                                        success, message = create_embeddings(all_chunks, vector_store_type)
                                        
                                        if success:
                                            st.success(f"🎉 {message}")
                                            # st.balloons()
                                            
                                            # Show summary
                                            st.subheader("📊 Processing Summary")
                                            st.write(f"**Files processed:** {len(processed_files)}")
                                            st.write(f"**Total chunks:** {len(all_chunks)}")
                                            st.write(f"**Vector store:** {vector_store_type}")
                                            st.write(f"**Storage path:** data/index/faiss_vector_store")
                                            
                                        else:
                                            st.error(f"❌ {message}")
                                    else:
                                        st.error("No text could be extracted from the uploaded files")
                                        
                                except Exception as e:
                                    st.error(f"Error processing documents: {str(e)}")
                
            st.markdown("---")
        
        # Don't show chat interface when admin panel is open
        return
    
    # Chat input with form for better UX
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("💬 Type your message:", placeholder="How can I help you today?")
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Send 📤")
        
        if submitted and user_input.strip():
            with st.spinner("🤔 Retrieving Information..."):
                try:
                    response, updated_session = st.session_state.bot.process_message(user_input, st.session_state.session, debug_mode=debug_mode)
                    st.session_state.session = updated_session
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing message: {e}")
    
    # Demo info
    with st.expander("ℹ️ How This Works"):
        st.markdown("""
        **Customer Service Flow:**
        
        1. **Welcome**: Bot greets and asks how to help
        2. **Info Collection**: Asks for email/phone to identify customer  
        3. **Account Lookup**: Finds customer and shows recent purchases
        4. **Assistance**: Helps with purchases or finds new products
        
        **Features:**
        - 🧠 **Smart State Management**: Tracks where you are in the conversation
        - 📧 **Info Extraction**: Automatically detects emails, phones, names
        - 🛍️ **Purchase History**: Shows recent purchases when identified
        - 🔍 **Product Search**: Finds products with keyword/regex matching
        - 💬 **Natural Conversation**: Uses AI for contextual responses
        
        **Try It:**
        - Start with "Hi, I need help"
        - Provide your email like "my email is john@example.com"
        - Ask about products or recent purchases
        """)

if __name__ == "__main__":
    main()
