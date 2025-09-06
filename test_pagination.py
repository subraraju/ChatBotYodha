#!/usr/bin/env python3

"""
Test the purchase pagination feature
"""
from app.chatbot.customer_service_bot import CustomerServiceBot

def test_purchase_pagination():
    print("🧪 Testing Purchase Pagination Feature")
    print("=" * 50)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    session = bot.start_new_session()
    
    print("1. Starting new session...")
    print(f"   Session ID: {session.session_id}")
    
    # Simulate finding a customer
    print("\n2. Testing customer lookup with pagination...")
    
    # Test the database lookup with pagination
    info = {"email": "test@example.com"}
    
    # Test first page (0-4)
    customer_id, purchases_page1, has_more_page1 = bot._database_lookup(info, offset=0, limit=5)
    print(f"\n   📄 Page 1 (purchases 1-5):")
    print(f"   Customer ID: {customer_id}")
    print(f"   Purchases returned: {len(purchases_page1)}")
    print(f"   Has more purchases: {has_more_page1}")
    
    if purchases_page1:
        for i, purchase in enumerate(purchases_page1, 1):
            print(f"   {i}. {purchase['product_name']} - ${purchase['total_amount']}")
    
    # Test second page (5-9)
    if has_more_page1:
        customer_id, purchases_page2, has_more_page2 = bot._database_lookup(info, offset=5, limit=5)
        print(f"\n   📄 Page 2 (purchases 6-10):")
        print(f"   Customer ID: {customer_id}")
        print(f"   Purchases returned: {len(purchases_page2)}")
        print(f"   Has more purchases: {has_more_page2}")
        
        if purchases_page2:
            for i, purchase in enumerate(purchases_page2, 6):
                print(f"   {i}. {purchase['product_name']} - ${purchase['total_amount']}")
        
        # Test third page (should be empty)
        if has_more_page2:
            customer_id, purchases_page3, has_more_page3 = bot._database_lookup(info, offset=10, limit=5)
            print(f"\n   📄 Page 3 (purchases 11-15):")
            print(f"   Customer ID: {customer_id}")
            print(f"   Purchases returned: {len(purchases_page3)}")
            print(f"   Has more purchases: {has_more_page3}")
        else:
            print(f"\n   📄 Page 3: No more purchases available")
    
    print("\n✅ Purchase pagination test completed!")
    print("\n🎯 The feature allows users to:")
    print("   - See first 5 purchases initially")
    print("   - Request next 5 purchases if they don't find what they want")
    print("   - Get a graceful message when no more purchases are available")

if __name__ == "__main__":
    test_purchase_pagination()
