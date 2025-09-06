import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import pandas as pd
from typing import List, Dict

# Configure the page
st.set_page_config(page_title="Agentic Chatbot", page_icon="🤖", layout="wide")

# API Base URL
API_BASE_URL = "http://127.0.0.1:8000"


def initialize_session_state():
    """Initialize session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "customer_email" not in st.session_state:
        st.session_state.customer_email = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def start_new_session(customer_email: str):
    """Start a new chat session"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat/start", params={"customer_email": customer_email}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.messages = []
            st.success(f"New chat session started: {data['session_id']}")
            return True
        else:
            st.error(f"Failed to start session: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error starting session: {str(e)}")
        return False


def send_message(message: str, use_external_search: bool = True):
    """Send a message to the chatbot"""
    if not st.session_state.session_id:
        st.error("No active session. Please start a new session first.")
        return None

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat/{st.session_state.session_id}/message",
            params={"message": message, "use_external_search": use_external_search},
        )

        if response.status_code == 200:
            data = response.json()
            return data["response"]
        else:
            st.error(f"Failed to send message: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None


def load_chat_session(session_id: str):
    """Load an existing chat session"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat/{session_id}")
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.session_id = session_id
            st.session_state.customer_email = session_data["customer_email"]
            st.session_state.messages = session_data["messages"]
            return True
        else:
            st.error(f"Session not found: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return False


def get_user_sessions(customer_email: str):
    """Get all sessions for a user"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat/user/{customer_email}")
        if response.status_code == 200:
            data = response.json()
            return data["sessions"]
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching sessions: {str(e)}")
        return []


def export_chat_session(session_id: str, format: str):
    """Export chat session in specified format"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat/{session_id}/export/{format}")
        if response.status_code == 200:
            data = response.json()
            return data["content"]
        else:
            st.error(f"Export failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error exporting session: {str(e)}")
        return None


def send_email_summary(session_id: str, recipient_email: str, subject: str = None):
    """Send chat summary via email"""
    try:
        params = {"recipient_email": recipient_email}
        if subject:
            params["subject"] = subject

        response = requests.post(
            f"{API_BASE_URL}/api/chat/{session_id}/email", params=params
        )
        if response.status_code == 200:
            st.success("Chat summary sent via email!")
            return True
        else:
            st.error(f"Failed to send email: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False


def send_sms_summary(session_id: str, recipient_phone: str):
    """Send chat summary via SMS"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat/{session_id}/sms",
            params={"recipient_phone": recipient_phone},
        )
        if response.status_code == 200:
            st.success("Chat summary sent via SMS!")
            return True
        else:
            st.error(f"Failed to send SMS: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error sending SMS: {str(e)}")
        return False


def main():
    """Main Streamlit application"""
    initialize_session_state()

    st.title("🤖 Agentic Chatbot")
    st.markdown(
        "Your intelligent assistant for customer service, sales, and product support"
    )

    # Sidebar for session management
    with st.sidebar:
        st.header("Session Management")

        # Customer email input
        customer_email = st.text_input(
            "Customer Email",
            value=st.session_state.customer_email,
            placeholder="Enter your email address",
        )

        if customer_email != st.session_state.customer_email:
            st.session_state.customer_email = customer_email

        # Start new session
        if st.button("Start New Session", disabled=not customer_email):
            if start_new_session(customer_email):
                st.rerun()

        # Load existing session
        if customer_email:
            st.subheader("Your Previous Sessions")
            user_sessions = get_user_sessions(customer_email)

            if user_sessions:
                selected_session = st.selectbox(
                    "Select a session to load",
                    options=[""] + user_sessions,
                    format_func=lambda x: (
                        "Select session..." if x == "" else f"Session: {x[:8]}..."
                    ),
                )

                if selected_session and st.button("Load Session"):
                    if load_chat_session(selected_session):
                        st.rerun()
            else:
                st.info("No previous sessions found")

        # Current session info
        if st.session_state.session_id:
            st.subheader("Current Session")
            st.info(f"Session ID: {st.session_state.session_id[:8]}...")
            st.info(f"Messages: {len(st.session_state.messages)}")

        # Export and sharing options
        if st.session_state.session_id:
            st.subheader("Export & Share")

            # Export format selection
            export_format = st.selectbox("Export Format", ["json", "markdown", "text"])

            if st.button("Export Chat"):
                content = export_chat_session(
                    st.session_state.session_id, export_format
                )
                if content:
                    st.download_button(
                        label=f"Download {export_format.upper()}",
                        data=content,
                        file_name=f"chat_{st.session_state.session_id[:8]}.{export_format}",
                        mime=f"text/{export_format}",
                    )

            # Email summary
            st.subheader("Send via Email")
            email_recipient = st.text_input("Recipient Email")
            email_subject = st.text_input("Subject (optional)")

            if st.button("Send Email", disabled=not email_recipient):
                send_email_summary(
                    st.session_state.session_id, email_recipient, email_subject
                )

            # SMS summary
            st.subheader("Send via SMS")
            sms_recipient = st.text_input("Recipient Phone (+1234567890)")

            if st.button("Send SMS", disabled=not sms_recipient):
                send_sms_summary(st.session_state.session_id, sms_recipient)

    # Main chat interface
    if st.session_state.session_id:
        st.subheader("Chat Interface")

        # Chat history display
        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                        st.caption(f"Sent at: {message['timestamp']}")
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        st.caption(f"Replied at: {message['timestamp']}")

        # Chat input
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_input(
                "Type your message here...",
                key="user_message",
                placeholder="Ask about customers, products, sales, or anything else!",
            )

        with col2:
            use_search = st.checkbox("Use External Search", value=True)

        if st.button("Send", disabled=not user_input) or (
            user_input and st.session_state.get("enter_pressed")
        ):
            if user_input:
                # Add user message to display
                user_message = {
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                st.session_state.messages.append(user_message)

                # Get bot response
                with st.spinner("Thinking..."):
                    bot_response = send_message(user_input, use_search)

                if bot_response:
                    # Add bot response to display
                    bot_message = {
                        "role": "assistant",
                        "content": bot_response,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    st.session_state.messages.append(bot_message)

                # Clear input and rerun
                st.session_state.user_message = ""
                st.rerun()

    else:
        st.info("👈 Please enter your email and start a new session to begin chatting!")

        # Show sample queries
        st.subheader("Sample Queries You Can Try:")

        sample_queries = [
            "Show me all customers from Seattle",
            "What are our top-selling products?",
            "Find recent sales activities",
            "Tell me about customer support tickets",
            "Search for information about CRM best practices",
            "Show sales analytics for this month",
        ]

        for query in sample_queries:
            st.markdown(f"• {query}")

        # Show database status
        st.subheader("System Status")
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                st.success("✅ API Server is running")
            else:
                st.error("❌ API Server is not responding")
        except:
            st.error("❌ Cannot connect to API Server")


if __name__ == "__main__":
    main()
