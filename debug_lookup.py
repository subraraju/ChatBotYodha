#!/usr/bin/env python3

"""
Debug the database lookup issue
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def debug_database_lookup():
    print("🔍 Debugging Database Lookup Issue")
    print("=" * 50)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    
    # Test the database lookup directly with various inputs
    test_cases = [
        {"email": "test@example.com"},
        {"phone": "555-123-4567"},
        {"email": "user@domain.com", "phone": "555-999-1234"},
        {}  # Empty info
    ]
    
    for i, customer_info in enumerate(test_cases, 1):
        print(f"\n{i}. Testing with info: {customer_info}")
        try:
            customer_id, purchases, has_more = bot._database_lookup(customer_info, offset=0, limit=10)
            print(f"   Result: customer_id={customer_id}, purchases={len(purchases)}, has_more={has_more}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test the mock fallback directly
    print(f"\n5. Testing mock fallback directly:")
    try:
        customer_id, purchases, has_more = bot._mock_database_lookup_fallback({"email": "test@example.com"}, 0, 10)
        print(f"   Mock result: customer_id={customer_id}, purchases={len(purchases)}, has_more={has_more}")
        if purchases:
            print(f"   First purchase: {purchases[0]['product_name']}")
    except Exception as e:
        print(f"   Mock error: {e}")

if __name__ == "__main__":
    debug_database_lookup()
