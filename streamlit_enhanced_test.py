import streamlit as st
import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure the page
st.set_page_config(
    page_title="Enhanced Agent Test", 
    page_icon="🤖", 
    layout="wide"
)

def test_ollama_connection():
    """Test if Ollama server is running and get available models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return True, [model['name'] for model in models]
        else:
            return False, []
    except:
        return False, []

def initialize_agent():
    """Initialize the enhanced agent"""
    try:
        from chatbot.simple_agent import EnhancedChatAgent, ChatSession, ChatMessage
        
        agent = EnhancedChatAgent()
        return agent, ChatSession, ChatMessage
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None, None, None

def create_session():
    """Create a new chat session"""
    try:
        from chatbot.simple_agent import ChatSession
        
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            customer_email=st.session_state.get('customer_email', 'test@example.com'),
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return session
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        return None

def main():
    st.title("🤖 Enhanced SQL Agent Test")
    st.markdown("Test the enhanced agent with SQLCoder and simplified 2-model architecture")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session' not in st.session_state:
        st.session_state.session = None
    if 'customer_email' not in st.session_state:
        st.session_state.customer_email = 'test@example.com'
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Test Ollama connection
        st.subheader("Ollama Status")
        is_connected, available_models = test_ollama_connection()
        
        if is_connected:
            st.success("✅ Ollama is running")
            st.write(f"📋 Available models ({len(available_models)}):")
            for model in available_models:
                st.write(f"• {model}")
            
            # Check for required models
            required_models = ['sqlcoder:7b', 'llama3.2:1b']
            missing_models = [model for model in required_models if not any(model in avail for avail in available_models)]
            
            if missing_models:
                st.warning(f"⚠️ Missing models: {missing_models}")
                st.write("Pull with: `ollama pull <model>`")
            else:
                st.success("✅ All required models available")
                
        else:
            st.error("❌ Ollama not running")
            st.write("Start with: `ollama serve`")
        
        # Customer email
        customer_email = st.text_input("Customer Email", value=st.session_state.customer_email)
        if customer_email != st.session_state.customer_email:
            st.session_state.customer_email = customer_email
        
        # New session button
        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.session = create_session()
            st.rerun()
        
        # Test database connection
        st.subheader("🗄️ Database Status")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            db_url = os.getenv("DATABASE_URL", "Not configured")
            if "4.155.102.23" in db_url:
                st.write("🔍 Database: mycrm@4.155.102.23")
                st.info("💡 Database connection may timeout")
            else:
                st.write(f"Database: {db_url}")
        except:
            st.write("Database config not loaded")
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Initialize agent if not done
    if 'agent' not in st.session_state:
        agent, ChatSession, ChatMessage = initialize_agent()
        if agent:
            st.session_state.agent = agent
            st.session_state.ChatSession = ChatSession
            st.session_state.ChatMessage = ChatMessage
            st.success("✅ Enhanced agent initialized successfully")
        else:
            st.error("❌ Failed to initialize agent")
            return
    
    # Create session if not exists
    if st.session_state.session is None:
        st.session_state.session = create_session()
    
    # Sample queries
    st.subheader("🎯 Sample Database Queries")
    sample_queries = [
        "How many customers do we have?",
        "Show me the top 5 products by sales",
        "What are the recent customer activities?",
        "Tell me about sales from last month",
        "Which customers have made the most purchases?",
        "What's our total revenue?",
        "Show me products in the electronics category",
        "List customers from California"
    ]
    
    cols = st.columns(4)
    for i, query in enumerate(sample_queries):
        with cols[i % 4]:
            if st.button(query, key=f"sample_{i}"):
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
    
    # Display chat messages
    st.subheader("🗨️ Conversation")
    
    # Chat container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your database..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Use the enhanced agent
                    agent = st.session_state.agent
                    session = st.session_state.session
                    
                    # Get response from agent
                    start_time = time.time()
                    response, updated_session = agent.chat(prompt, session)
                    end_time = time.time()
                    
                    # Update session
                    st.session_state.session = updated_session
                    
                    # Display response with timing
                    st.markdown(response)
                    st.caption(f"⏱️ Response time: {end_time - start_time:.2f}s")
                    
                    # Add to messages
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Debug info
    with st.expander("🔍 Debug Information"):
        st.write("**Agent Configuration:**")
        if 'agent' in st.session_state:
            agent = st.session_state.agent
            st.write(f"- SQL Model: {getattr(agent, 'sql_model', 'Not configured')}")
            st.write(f"- Chat Model: {getattr(agent, 'chat_model', 'Not configured')}")
            st.write(f"- Database URL: {getattr(agent, 'database_url', 'Not configured')}")
        
        st.write("**Current Session:**")
        if st.session_state.session:
            st.write(f"- Session ID: {st.session_state.session.session_id}")
            st.write(f"- Customer: {st.session_state.session.customer_email}")
            st.write(f"- Messages: {len(st.session_state.session.messages)}")
        
        st.write("**Environment:**")
        st.write(f"- Ollama Connected: {is_connected}")
        st.write(f"- Available Models: {len(available_models) if available_models else 0}")

if __name__ == "__main__":
    main()
