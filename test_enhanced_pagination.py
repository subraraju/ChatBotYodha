#!/usr/bin/env python3

"""
Test the enhanced purchase pagination feature
- Retrieves all 10 purchases at once
- Shows 1-5 initially
- Shows 6-10 when user requests more
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def test_enhanced_pagination():
    print("🧪 Testing Enhanced Purchase Pagination Feature")
    print("=" * 60)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    session = bot.start_new_session()
    
    print("1. Starting new session...")
    print(f"   Session ID: {session.session_id}")
    
    # Simulate customer identification
    print("\n2. Simulating customer identification...")
    response, session = bot.process_message("I need help with my recent order. My email is test@example.com", session)
    
    print(f"📝 Bot Response:")
    print(response)
    print(f"\n📊 Session State:")
    print(f"   All purchases stored: {len(session.all_purchases) if hasattr(session, 'all_purchases') else 'N/A'}")
    print(f"   Displayed purchases: {len(session.displayed_purchases) if hasattr(session, 'displayed_purchases') else 'N/A'}")
    print(f"   Has more purchases: {session.has_more_purchases if hasattr(session, 'has_more_purchases') else 'N/A'}")
    
    # Test user saying they can't find what they want
    print("\n3. Testing user can't find product in 1-5...")
    response, session = bot.process_message("I don't see the product I'm looking for in this list", session)
    
    print(f"📝 Bot Response:")
    print(response)
    
    # Test user asking for more purchases
    print("\n4. Testing user asking for more purchases...")
    response, session = bot.process_message("show more purchases", session)
    
    print(f"📝 Bot Response:")
    print(response)
    print(f"\n📊 Session State:")
    print(f"   Displayed purchases: {len(session.displayed_purchases) if hasattr(session, 'displayed_purchases') else 'N/A'}")
    print(f"   Has more purchases: {session.has_more_purchases if hasattr(session, 'has_more_purchases') else 'N/A'}")
    
    # Test selecting a product from 6-10
    print("\n5. Testing product selection from 6-10...")
    response, session = bot.process_message("I need help with product 7", session)
    
    print(f"📝 Bot Response:")
    print(response)
    
    # Test asking for even more purchases (should be politely declined)
    print("\n6. Testing request for more purchases beyond 10...")
    response, session = bot.process_message("show more products", session)
    
    print(f"📝 Bot Response:")
    print(response)
    
    print("\n✅ Enhanced purchase pagination test completed!")
    print("\n🎯 The enhanced feature allows users to:")
    print("   - See first 5 purchases initially")
    print("   - Request next 5 purchases (6-10) when they can't find what they want")
    print("   - Get a polite message when no more than 10 purchases are available")
    print("   - All 10 purchases retrieved once at identification to avoid repeated DB calls")

if __name__ == "__main__":
    test_enhanced_pagination()
