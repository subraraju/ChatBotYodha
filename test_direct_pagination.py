#!/usr/bin/env python3

"""
Direct test of the enhanced purchase pagination feature
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def test_direct_pagination():
    print("🧪 Direct Testing Enhanced Purchase Pagination Feature")
    print("=" * 60)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    
    # Test the database lookup directly with mock data
    print("1. Testing direct database lookup for 10 purchases...")
    customer_info = {"email": "test@example.com"}
    customer_id, all_purchases, has_more = bot._database_lookup(customer_info, offset=0, limit=10)
    
    print(f"   Customer ID: {customer_id}")
    print(f"   Total purchases retrieved: {len(all_purchases)}")
    print(f"   Has more available: {has_more}")
    
    if all_purchases:
        print(f"\n   All 10 purchases:")
        for i, purchase in enumerate(all_purchases, 1):
            print(f"   {i:2d}. {purchase['product_name']} - ${purchase['total_amount']} on {purchase['sale_date']}")
        
        # Test showing first 5
        print(f"\n2. Simulating showing first 5 purchases (1-5):")
        first_5 = all_purchases[:5]
        for i, purchase in enumerate(first_5, 1):
            print(f"   {i}. {purchase['product_name']} - {purchase['sale_date']}")
        
        # Test showing next 5
        print(f"\n3. Simulating showing next 5 purchases (6-10):")
        next_5 = all_purchases[5:10] if len(all_purchases) > 5 else []
        if next_5:
            for i, purchase in enumerate(next_5, 6):
                print(f"   {i}. {purchase['product_name']} - {purchase['sale_date']}")
        else:
            print("   No more purchases available")
        
        # Test pagination logic
        print(f"\n4. Pagination Logic Tests:")
        print(f"   Total purchases: {len(all_purchases)}")
        print(f"   Show first 5: {len(first_5)} purchases")
        print(f"   Has more after first 5: {len(all_purchases) > 5}")
        print(f"   Show next 5: {len(next_5)} purchases")
        print(f"   Has more after 10: {len(all_purchases) > 10}")
        
    else:
        print("   ❌ No purchases found")
    
    print("\n✅ Direct pagination test completed!")

if __name__ == "__main__":
    test_direct_pagination()
