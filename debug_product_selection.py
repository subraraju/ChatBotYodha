#!/usr/bin/env python3

"""
Debug product selection issue
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def debug_product_selection():
    print("🔍 Debugging Product Selection Issue")
    print("=" * 50)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    session = bot.start_new_session()
    
    # Simulate getting customer with purchases
    customer_id, all_purchases, has_more = bot._database_lookup({'email': 'henry.f@example.com'}, offset=0, limit=10)
    
    # Set up session as if we're in the 6-10 state
    session.customer_id = customer_id
    session.all_purchases = all_purchases
    session.displayed_purchases = all_purchases[5:10]  # Show 6-10
    session.has_more_purchases = False
    
    print("Session setup:")
    print(f"  All purchases: {len(session.all_purchases)}")
    print(f"  Displayed purchases (6-10): {len(session.displayed_purchases)}")
    
    print(f"\nAll purchases (1-10):")
    for i, purchase in enumerate(session.all_purchases, 1):
        print(f"  {i:2d}. {purchase['product_name']}")
    
    print(f"\nDisplayed purchases (6-10):")
    for i, purchase in enumerate(session.displayed_purchases, 6):
        print(f"  {i:2d}. {purchase['product_name']}")
    
    # Test product extraction
    test_cases = ["7", "product 7", "StyleX Express", "number 7"]
    
    for test_input in test_cases:
        print(f"\nTesting input: '{test_input}'")
        result = bot._extract_product_from_input(test_input, session.displayed_purchases, session)
        print(f"  Result: {result}")
        
        # Test what product 7 should be
        if session.all_purchases and len(session.all_purchases) >= 7:
            expected = session.all_purchases[6]['product_name']  # 7th product (0-indexed)
            print(f"  Expected (7th overall): {expected}")

if __name__ == "__main__":
    debug_product_selection()
