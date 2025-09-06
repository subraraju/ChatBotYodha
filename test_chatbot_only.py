#!/usr/bin/env python3

# Test just the CustomerServiceBot import
try:
    print("Testing CustomerServiceBot import...")
    from app.chatbot.customer_service_bot import CustomerServiceBot
    print("✓ CustomerServiceBot import OK")
    
    bot = CustomerServiceBot()
    print("✓ CustomerServiceBot initialization OK")
    
    print("✅ CustomerServiceBot is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
