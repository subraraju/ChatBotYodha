import streamlit as st
import requests
import json
import time
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="GPT Model Chat Test", 
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

def send_message_to_ollama(model_name, message, temperature=0.7, max_tokens=500):
    """Send message to Ollama and get response"""
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": model_name,
        "prompt": message,  
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "top_p": 0.9,
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, timeout=60)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get('response', ''),
                "response_time": response_time,
                "error": None
            }
        else:
            return {
                "success": False,
                "response": '',
                "response_time": response_time,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "response": '',
            "response_time": 60,
            "error": "Request timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "response": '',
            "response_time": 0,
            "error": f"Error: {str(e)}"
        }

def main():
    """Main Streamlit app"""
    st.title("🤖 Ollama Chat Test")
    
    # st.title("🤖 GPT Model Chat Test")
    st.markdown("Testing local GPT models via Ollama - No integrations required!")
    
    # Sidebar for configuration
    with st.sidebar:
        # st.header("🔧 Configuration")
        
        # Test connection
        # st.subheader("Connection Status")
        if False and st.button("🔍 Test Connection"):
            with st.spinner("Testing connection..."):
                connected, models = test_ollama_connection()
                
                if connected:
                    st.success("✅ Ollama is running!")
                    if models:
                        st.info(f"📦 Available models: {len(models)}")
                        for model in models:
                            st.text(f"  • {model}")
                    else:
                        st.warning("📦 No models installed")
                else:
                    st.error("❌ Cannot connect to Ollama")
                    st.info("💡 Make sure Ollama is running: `ollama serve`")
        
        # Model selection
        st.subheader("Model Settings")
        connected, available_models = test_ollama_connection()
        
        if available_models:
            selected_model = st.selectbox(
                "Select Model",
                options=available_models,
                index=0 if available_models else None
            )
        else:
            st.error("No models available")
            st.info("Install a model: `ollama pull llama3.2:1b`")
            selected_model = None
        
        # Parameters
        st.subheader("Generation Parameters")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 50, 1000, 500, 50)
        
        # Stats
        if "stats" in st.session_state:
            st.subheader("📊 Session Stats")
            stats = st.session_state.stats
            st.metric("Messages Sent", stats["messages_sent"])
            st.metric("Avg Response Time", f"{stats['avg_response_time']:.1f}s")
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "stats" not in st.session_state:
        st.session_state.stats = {
            "messages_sent": 0,
            "total_response_time": 0,
            "successful_requests": 0,
            "avg_response_time": 0,
            "success_rate": 0
        }
    
    # Main chat interface
    if not available_models:
        st.warning("⚠️ No models available. Please install a model first.")
        st.info("Run: `ollama pull llama3.2:1b` to install a small test model")
        return
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show metadata for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"⏱️ {metadata['response_time']:.1f}s")
                    with col2:
                        st.caption(f"🤖 {metadata['model']}")
                    with col3:
                        if metadata.get('success'):
                            st.caption("✅ Success")
                        else:
                            st.caption("❌ Failed")
    
    # Chat input
    if prompt := st.chat_input("Type your message here...", disabled=not selected_model):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(f"🤖 {selected_model} is thinking..."):
                result = send_message_to_ollama(
                    selected_model, 
                    prompt, 
                    temperature, 
                    max_tokens
                )
                
                # Update stats
                stats = st.session_state.stats
                stats["messages_sent"] += 1
                stats["total_response_time"] += result["response_time"]
                
                if result["success"]:
                    stats["successful_requests"] += 1
                    st.write(result["response"])
                else:
                    st.error(f"❌ Error: {result['error']}")
                    st.write("Sorry, I encountered an error processing your request.")
                
                # Calculate averages
                stats["avg_response_time"] = stats["total_response_time"] / stats["messages_sent"]
                stats["success_rate"] = (stats["successful_requests"] / stats["messages_sent"]) * 100
                
                # Show response metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"⏱️ {result['response_time']:.1f}s")
                with col2:
                    st.caption(f"🤖 {selected_model}")
                with col3:
                    if result['success']:
                        st.caption("✅ Success")
                    else:
                        st.caption("❌ Failed")
        
        # Add assistant message to history
        assistant_message = {
            "role": "assistant",
            "content": result["response"] if result["success"] else "Sorry, I encountered an error.",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "metadata": {
                "model": selected_model,
                "response_time": result["response_time"],
                "success": result["success"],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        
        if not result["success"]:
            assistant_message["metadata"]["error"] = result["error"]
        
        st.session_state.messages.append(assistant_message)
        
        # Auto-rerun to update the display
        st.rerun()
    
    # Quick test buttons
    if available_models and False:
        st.markdown("---")
        st.subheader("🧪 Quick Tests")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👋 Test Greeting"):
                test_prompt = "Hello! Please introduce yourself briefly."
                st.session_state.test_prompt = test_prompt
        
        with col2:
            if st.button("🧠 Test Knowledge"):
                test_prompt = "What is artificial intelligence? Please explain in 2-3 sentences."
                st.session_state.test_prompt = test_prompt
        
        with col3:
            if st.button("💬 Test Chat"):
                test_prompt = "You are a helpful customer service assistant. How can you help customers today?"
                st.session_state.test_prompt = test_prompt
        
        # Handle test prompts
        if "test_prompt" in st.session_state:
            prompt = st.session_state.test_prompt
            del st.session_state.test_prompt
            
            # Add to messages and process
            st.session_state.messages.append({
                "role": "user",
                "content": f"🧪 TEST: {prompt}",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            st.rerun()
    
    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.stats = {
                "messages_sent": 0,
                "total_response_time": 0,
                "successful_requests": 0,
                "avg_response_time": 0,
                "success_rate": 0
            }
            st.rerun()

if __name__ == "__main__":
    main()
