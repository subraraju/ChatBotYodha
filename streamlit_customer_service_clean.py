import streamlit as st
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure the page
st.set_page_config(
    page_title="Customer Service Chat", 
    page_icon="💬", 
    layout="centered"
)

def initialize_bot():
    """Initialize the customer service bot"""
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        bot = CustomerServiceBot()
        return bot
    except Exception as e:
        st.error(f"Failed to initialize bot: {e}")
        return None

def main():
    st.title("💬 Customer Service Chat")
    st.markdown("Welcome to our customer service! I'm here to help you with your account and products.")
    
    # Initialize session state
    if 'bot' not in st.session_state:
        st.session_state.bot = initialize_bot()
        if not st.session_state.bot:
            st.error("Could not initialize the customer service bot")
            return
    
    if 'session' not in st.session_state:
        st.session_state.session = st.session_state.bot.start_new_session()
        # Generate welcome message without processing empty input
        welcome_msg = st.session_state.bot._generate_welcome_message()
        # Import ChatMessage class
        from app.chatbot.customer_service_bot import ChatMessage
        st.session_state.session.messages.append(ChatMessage("assistant", welcome_msg))
        st.session_state.session.customer_state = st.session_state.session.customer_state
    
    # Display chat messages
    st.subheader("Chat")
    
    # Create a container for chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.session.messages:
            if message.role == "user":
                with st.chat_message("user"):
                    st.markdown(message.content)
            else:
                with st.chat_message("assistant"):
                    st.markdown(message.content)
    
    # Customer state indicator
    with st.sidebar:
        st.header("Session Info")
        
        # Only show state if it's not unknown
        if st.session_state.session.customer_state.value != "unknown":
            st.write(f"**State:** {st.session_state.session.customer_state.value}")
        
        if st.session_state.session.customer_info:
            st.write("**Customer Info:**")
            for key, value in st.session_state.session.customer_info.items():
                st.write(f"- {key}: {value}")
        
        if st.session_state.session.customer_id:
            st.write(f"**Customer ID:** {st.session_state.session.customer_id}")
            
        if st.session_state.session.recent_purchases:
            st.write("**Recent Purchases:**")
            for purchase in st.session_state.session.recent_purchases:
                st.write(f"- {purchase['product_name']}")
        
        st.write(f"**Messages:** {len(st.session_state.session.messages)}")
        
        if st.button("🔄 New Session"):
            st.session_state.session = st.session_state.bot.start_new_session()
            # Generate welcome message without processing empty input
            welcome_msg = st.session_state.bot._generate_welcome_message()
            from app.chatbot.customer_service_bot import ChatMessage
            st.session_state.session.messages.append(ChatMessage("assistant", welcome_msg))
            st.rerun()
    
    # Chat input with form for better UX
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("💬 Type your message:", placeholder="How can I help you today?")
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Send 📤")
        
        if submitted and user_input.strip():
            with st.spinner("🤔 Thinking..."):
                try:
                    response, updated_session = st.session_state.bot.process_message(user_input, st.session_state.session)
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
