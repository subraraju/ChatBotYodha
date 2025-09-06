#!/usr/bin/env python3

# Simple test to check if CustomerServiceBot can be imported and initialized
try:
    from app.chatbot.customer_service_bot import CustomerServiceBot
    bot = CustomerServiceBot()
    print("✅ CustomerServiceBot imported and initialized successfully!")
    print("✅ Purchase pagination feature is ready to test!")
except Exception as e:
    print(f"❌ Error importing CustomerServiceBot: {e}")
