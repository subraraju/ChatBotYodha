import streamlit as st
import random
from datetime import datetime
import time

# Configure the page
st.set_page_config(
    page_title="Customer Chat Support", 
    page_icon="💬", 
    layout="wide"
)

# Sample responses for different query types
SAMPLE_RESPONSES = {
    "greeting": [
        "Hello! Welcome to our customer support. How can I help you today?",
        "Hi there! I'm here to assist you. What can I do for you?",
        "Good day! Thanks for contacting us. How may I assist you?",
        "Hello! I'm your virtual assistant. What would you like to know?"
    ],
    "product": [
        "I'd be happy to help you with product information! Our latest products include advanced analytics tools, cloud storage solutions, and enterprise software. Which specific product are you interested in?",
        "Great question about our products! We offer a wide range of solutions from basic plans starting at $29/month to enterprise packages. What's your use case?",
        "Our product catalog includes software solutions, cloud services, and support packages. Let me know what you're looking for and I can provide detailed information.",
        "We have several popular products that might interest you. Could you tell me more about your specific needs so I can recommend the best option?"
    ],
    "pricing": [
        "Our pricing starts from $19/month for basic plans and goes up to $299/month for enterprise solutions. Would you like me to send you a detailed pricing sheet?",
        "We have flexible pricing options to fit different budgets. Basic: $19/month, Professional: $59/month, Enterprise: $299/month. Which tier interests you?",
        "Great question! We offer competitive pricing with no hidden fees. I can create a custom quote based on your specific requirements. What features do you need?",
        "Our pricing is transparent and scalable. We also offer annual discounts of up to 20%. Would you like to schedule a call to discuss your needs?"
    ],
    "support": [
        "I'm here to help with any technical issues! Can you describe the problem you're experiencing?",
        "Sorry to hear you're having trouble. Let me assist you right away. What seems to be the issue?",
        "Our support team is available 24/7. I'll do my best to resolve this for you. Can you provide more details about the problem?",
        "I understand how frustrating technical issues can be. Let's get this sorted out. What error message are you seeing?"
    ],
    "billing": [
        "I can help you with billing questions. Are you looking to update your payment method, view invoices, or change your subscription?",
        "Let me assist you with your billing inquiry. I can help with payments, refunds, or subscription changes. What do you need?",
        "For billing matters, I'm here to help! Whether it's about charges, invoices, or account updates, I've got you covered. What's your question?",
        "I can access your billing information right away. What specifically would you like to know about your account?"
    ],
    "demo": [
        "I'd love to show you our platform! We offer free 30-minute demos where you can see all features in action. When would be a good time for you?",
        "Absolutely! Our product demos are very popular. I can schedule a personalized demo for you. Are you available this week?",
        "Great idea! A demo is the best way to understand our platform. We have slots available tomorrow and next week. What works for you?",
        "Perfect! Our demos cover all key features and answer common questions. Would you prefer a one-on-one session or a group demo?"
    ],
    "complaint": [
        "I sincerely apologize for any inconvenience you've experienced. Let me escalate this to our senior support team right away. Can you provide more details?",
        "I'm sorry to hear about this issue. Your feedback is important to us and I want to make this right. Let me connect you with a specialist.",
        "Thank you for bringing this to our attention. I take this seriously and will ensure it's resolved promptly. Can you share more about what happened?",
        "I understand your frustration and I'm here to help resolve this. Let me document this issue and get you in touch with our resolution team."
    ],
    "general": [
        "That's an interesting question! Let me think about the best way to help you with that.",
        "I see what you're asking about. Based on your query, I think I can provide some helpful information.",
        "Thanks for that question! I want to make sure I give you the most accurate information possible.",
        "I appreciate you reaching out about this. Let me provide you with some relevant details."
    ]
}

def get_response_type(user_message):
    """Determine the type of response based on user message"""
    message_lower = user_message.lower()
    
    greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    product_words = ['product', 'feature', 'software', 'tool', 'solution', 'service']
    pricing_words = ['price', 'cost', 'pricing', 'plan', 'subscription', 'fee', 'charge']
    support_words = ['problem', 'issue', 'error', 'bug', 'not working', 'broken', 'help']
    billing_words = ['bill', 'billing', 'payment', 'invoice', 'refund', 'charge', 'account']
    demo_words = ['demo', 'trial', 'test', 'show me', 'demonstration', 'preview']
    complaint_words = ['complaint', 'angry', 'frustrated', 'disappointed', 'terrible', 'awful', 'bad experience']
    
    if any(word in message_lower for word in greeting_words):
        return 'greeting'
    elif any(word in message_lower for word in complaint_words):
        return 'complaint'
    elif any(word in message_lower for word in product_words):
        return 'product'
    elif any(word in message_lower for word in pricing_words):
        return 'pricing'
    elif any(word in message_lower for word in support_words):
        return 'support'
    elif any(word in message_lower for word in billing_words):
        return 'billing'
    elif any(word in message_lower for word in demo_words):
        return 'demo'
    else:
        return 'general'

def generate_ai_response(user_message):
    """Generate AI response based on user message"""
    response_type = get_response_type(user_message)
    
    # Add some randomness to make responses feel more natural
    if response_type in SAMPLE_RESPONSES:
        base_response = random.choice(SAMPLE_RESPONSES[response_type])
    else:
        base_response = random.choice(SAMPLE_RESPONSES['general'])
    
    # Add some contextual follow-ups
    follow_ups = [
        "Is there anything else I can help you with?",
        "Do you have any other questions?",
        "Would you like me to connect you with a human agent?",
        "I'm here if you need any clarification!",
        "Feel free to ask if you need more information."
    ]
    
    # Sometimes add a follow-up (30% chance)
    if random.random() < 0.3:
        base_response += f"\n\n{random.choice(follow_ups)}"
    
    return base_response

def simulate_typing_delay():
    """Simulate AI typing with a realistic delay"""
    delay = random.uniform(1, 3)  # Random delay between 1-3 seconds
    with st.spinner("AI is typing..."):
        time.sleep(delay)

def main():
    """Main Streamlit chat application"""
    
    st.title("💬 Customer Support Chat")
    st.markdown("---")
    
    # Sidebar with chat info
    with st.sidebar:
        st.header("Chat Information")
        st.info("**Status**: Online 🟢")
        st.info("**Support Agent**: AI Assistant")
        st.info("**Response Time**: ~2-3 seconds")
        
        st.markdown("---")
        st.subheader("Quick Actions")
        
        if st.button("🔄 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("📁 Export Chat"):
            if "messages" in st.session_state and st.session_state.messages:
                chat_export = []
                for msg in st.session_state.messages:
                    timestamp = msg.get('timestamp', 'Unknown time')
                    chat_export.append(f"[{timestamp}] {msg['role'].title()}: {msg['content']}")
                
                export_text = "\n".join(chat_export)
                st.download_button(
                    label="Download Chat Log",
                    data=export_text,
                    file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        st.markdown("---")
        st.subheader("Sample Questions")
        st.markdown("""
        Try asking:
        - "Hello, I need help with your products"
        - "What are your pricing plans?"
        - "I'm having trouble with my account"
        - "Can I get a demo?"
        - "I want to speak to billing"
        - "I have a complaint about service"
        """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Hello! Welcome to our customer support chat. I'm here to help you with any questions about our products, services, billing, or technical issues. How can I assist you today?",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        ]
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                # Show timestamp for each message
                if "timestamp" in message:
                    st.caption(f"📅 {message['timestamp']}")
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Get current timestamp
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": current_time
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"📅 {current_time}")
        
        # Generate and display AI response
        with st.chat_message("assistant"):
            # Simulate typing delay
            simulate_typing_delay()
            
            # Generate response
            response = generate_ai_response(prompt)
            response_time = datetime.now().strftime("%H:%M:%S")
            
            # Display response
            st.write(response)
            st.caption(f"📅 {response_time}")
            
            # Add AI response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": response_time
            })
    
    # Show some usage stats at the bottom
    if len(st.session_state.messages) > 1:  # More than just the welcome message
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            st.metric("Your Messages", user_messages)
        
        with col2:
            ai_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) - 1  # Exclude welcome
            st.metric("AI Responses", ai_messages)
        
        with col3:
            st.metric("Chat Duration", f"{len(st.session_state.messages) * 2} min")

if __name__ == "__main__":
    main()
