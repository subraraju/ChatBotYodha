#!/usr/bin/env python3

"""
Test enhanced "not in list" detection and auto-pagination
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def test_auto_pagination():
    print("🧪 Testing Enhanced Auto-Pagination on 'Not in List'")
    print("=" * 60)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    session = bot.start_new_session()
    
    print("1. Customer identification...")
    response, session = bot.process_message("I need help with my recent order. My email is henry.f@example.com", session)
    print(f"📝 Bot shows first 5 purchases")
    
    print(f"\n📊 Initial State:")
    print(f"   Displayed purchases: {len(session.displayed_purchases)} (should be 5)")
    print(f"   Has more: {session.has_more_purchases} (should be True)")
    
    # Test various "not in list" phrases
    test_phrases = [
        "It's not in this list",
        "I don't see it here", 
        "Not what I'm looking for",
        "Can't see it",
        "It's not there",
        "None of these",
        "Not listed",
        "Missing from the list"
    ]
    
    for i, phrase in enumerate(test_phrases[:3], 2):  # Test first 3 phrases
        print(f"\n{i}. Testing phrase: '{phrase}'")
        response, session = bot.process_message(phrase, session)
        
        if "Here are your next recent purchases (6-10)" in response or "No problem! Let me show you your next recent purchases (6-10)" in response:
            print(f"   ✅ SUCCESS: Auto-showed purchases 6-10")
            print(f"   📝 Response starts with: '{response[:80]}...'")
            
            # Check session state
            print(f"   📊 After auto-show:")
            print(f"      Displayed purchases: {len(session.displayed_purchases)} (should be 5)")
            print(f"      Has more: {session.has_more_purchases} (should be False)")
            
            # Reset for next test (simulate going back to 1-5)
            session.displayed_purchases = session.all_purchases[:5]
            session.has_more_purchases = True
            break
        else:
            print(f"   ❌ FAILED: Did not auto-show more purchases")
            print(f"   📝 Response: '{response[:100]}...'")
    
    print(f"\n4. Testing explicit 'show more' still works...")
    response, session = bot.process_message("show more purchases", session)
    if "purchases (6-10)" in response:
        print(f"   ✅ Explicit request still works")
    else:
        print(f"   ❌ Explicit request failed")
    
    print(f"\n5. Testing product selection from 6-10...")
    response, session = bot.process_message("I need help with product 8", session)
    if "I'll help you with" in response:
        print(f"   ✅ Product selection works from 6-10 range")
        print(f"   Selected: {session.selected_product if hasattr(session, 'selected_product') else 'None'}")
    else:
        print(f"   ❌ Product selection failed")
    
    print("\n✅ Enhanced auto-pagination test completed!")
    print("\n🎯 Expected improvements:")
    print("   ✅ Auto-detects 'not in list' phrases and shows 6-10")
    print("   ✅ More natural conversation flow")
    print("   ✅ Reduces user friction and steps")
    print("   ✅ Still supports explicit 'show more' requests")

if __name__ == "__main__":
    test_auto_pagination()
