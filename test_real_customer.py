#!/usr/bin/env python3

"""
Test with real customer email henry.f@example.com
"""
import sys
sys.path.append('.')

from app.chatbot.customer_service_bot import CustomerServiceBot

def test_real_customer():
    print("🧪 Testing with Real Customer: henry.f@example.com")
    print("=" * 60)
    
    # Initialize the bot
    bot = CustomerServiceBot()
    
    # Test with real customer email
    print("1. Testing database lookup with henry.f@example.com...")
    customer_id, purchases, has_more = bot._database_lookup({'email': 'henry.f@example.com'}, offset=0, limit=10)
    
    print(f"   Customer ID: {customer_id}")
    print(f"   Purchases found: {len(purchases)}")
    print(f"   Has more: {has_more}")
    
    if purchases:
        print(f"\n   All purchases retrieved:")
        for i, purchase in enumerate(purchases, 1):
            print(f"   {i:2d}. {purchase['product_name']} - ${purchase['total_amount']} on {purchase['sale_date']}")
        
        # Test pagination logic
        print(f"\n2. Testing pagination logic:")
        first_5 = purchases[:5]
        next_5 = purchases[5:10] if len(purchases) > 5 else []
        
        print(f"   Total purchases: {len(purchases)}")
        print(f"   First 5 purchases: {len(first_5)}")
        print(f"   Next 5 purchases: {len(next_5)}")
        print(f"   Has more after first 5: {len(purchases) > 5}")
        
        print(f"\n3. Simulating user flow:")
        print(f"   Step 1 - Show purchases 1-5:")
        for i, purchase in enumerate(first_5, 1):
            print(f"      {i}. {purchase['product_name']} - {purchase['sale_date']}")
        
        if next_5:
            print(f"\n   Step 2 - Show purchases 6-10:")
            for i, purchase in enumerate(next_5, 6):
                print(f"      {i}. {purchase['product_name']} - {purchase['sale_date']}")
        
    else:
        print("   ❌ No purchases found for this customer")
    
    print("\n✅ Real customer test completed!")

if __name__ == "__main__":
    test_real_customer()
