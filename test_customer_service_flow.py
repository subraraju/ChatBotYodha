"""
Test script to verify customer service bot SQL retrieval and chat flow
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_database_lookup():
    """Test the database lookup functionality directly"""
    print("🔍 Testing Database Lookup Functionality")
    print("=" * 50)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        print("✅ CustomerServiceBot initialized successfully")
        
        # Test customer info
        test_info = {'email': 'henry.f@example.com'}
        print(f"\n🧪 Testing with email: {test_info['email']}")
        
        # Call the database lookup method directly
        customer_id, purchases = bot._database_lookup(test_info)
        
        print(f"\n📊 Results:")
        print(f"Customer ID: {customer_id}")
        print(f"Number of purchases: {len(purchases) if purchases else 0}")
        
        if customer_id:
            print(f"\n👤 Customer Information:")
            print(f"  - Customer ID: {customer_id}")
            print(f"  - Updated Info: {test_info}")
            
            if purchases:
                print(f"\n🛍️ Recent Purchases ({len(purchases)} items):")
                for i, purchase in enumerate(purchases, 1):
                    print(f"  {i}. {purchase.get('product_name', 'N/A')}")
                    print(f"     Category: {purchase.get('category', 'N/A')}")
                    print(f"     Price: ${purchase.get('price', 0):.2f}")
                    print(f"     Quantity: {purchase.get('quantity', 1)}")
                    print(f"     Total: ${purchase.get('total_amount', 0):.2f}")
                    print(f"     Date: {purchase.get('sale_date', 'N/A')}")
                    print()
            else:
                print("  - No recent purchases found")
        else:
            print("❌ Customer not found in database")
            
    except Exception as e:
        print(f"❌ Error testing database lookup: {e}")
        import traceback
        traceback.print_exc()

def test_chat_flow():
    """Test the complete chat flow with customer identification"""
    print("\n\n💬 Testing Complete Chat Flow")
    print("=" * 50)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ New session started")
        print(f"Initial state: {session.customer_state.value}")
        
        # Test conversation flow
        test_messages = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "Can you show me my recent purchases?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"👤 User: {message}")
            
            # Process the message
            response, updated_session = bot.process_message(message, session)
            session = updated_session
            
            print(f"🤖 Bot: {response}")
            print(f"📊 State: {session.customer_state.value}")
            
            if session.customer_id:
                print(f"🆔 Customer ID: {session.customer_id}")
            
            if session.customer_info:
                print(f"📝 Customer Info: {session.customer_info}")
            
            if session.recent_purchases:
                print(f"🛍️ Purchases loaded: {len(session.recent_purchases)} items")
            
            print()
            
    except Exception as e:
        print(f"❌ Error testing chat flow: {e}")
        import traceback
        traceback.print_exc()

def test_specific_customer_queries():
    """Test specific customer queries in the database"""
    print("\n\n🔍 Testing Specific Customer Database Queries")
    print("=" * 50)
    
    try:
        import psycopg2
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL not configured")
            return
        
        print(f"🔗 Connecting to database...")
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=8)
        cursor = conn.cursor()
        
        print("✅ Database connection successful")
        
        # Test query 1: Find customer by email
        print(f"\n🔍 Query 1: Finding customer by email 'henry.f@example.com'")
        cursor.execute("""
            SELECT customer_id, first_name, last_name, email, phone, city, state 
            FROM customer 
            WHERE LOWER(email) = LOWER(%s)
        """, ('henry.f@example.com',))
        
        customer_result = cursor.fetchone()
        
        if customer_result:
            customer_id, first_name, last_name, email, phone, city, state = customer_result
            print(f"✅ Customer found:")
            print(f"   ID: {customer_id}")
            print(f"   Name: {first_name} {last_name}")
            print(f"   Email: {email}")
            print(f"   Phone: {phone}")
            print(f"   Location: {city}, {state}")
            
            # Test query 2: Get recent purchases for this customer
            print(f"\n🔍 Query 2: Finding recent purchases for customer ID {customer_id}")
            cursor.execute("""
                SELECT 
                    p.product_name,
                    p.category,
                    p.type,
                    p.price,
                    s.quantity,
                    s.total_amount,
                    s.sale_date,
                    s.sales_id
                FROM sales s
                JOIN product p ON s.product_id = p.product_id
                WHERE s.customer_id = %s
                ORDER BY s.sale_date DESC
                LIMIT 5;
            """, (customer_id,))
            
            purchases = cursor.fetchall()
            
            if purchases:
                print(f"✅ Found {len(purchases)} recent purchases:")
                for i, purchase in enumerate(purchases, 1):
                    product_name, category, product_type, price, quantity, total_amount, sale_date, sales_id = purchase
                    print(f"   {i}. {product_name}")
                    print(f"      Category: {category} | Type: {product_type}")
                    print(f"      Unit Price: ${price:.2f} | Qty: {quantity}")
                    print(f"      Total: ${total_amount:.2f}")
                    print(f"      Date: {sale_date} | Sales ID: {sales_id}")
                    print()
            else:
                print("❌ No purchases found for this customer")
        else:
            print("❌ Customer not found with email 'henry.f@example.com'")
            
            # Let's check what customers do exist
            print(f"\n🔍 Query 3: Checking existing customers with email patterns")
            cursor.execute("""
                SELECT customer_id, first_name, last_name, email 
                FROM customer 
                WHERE email LIKE '%henry%' OR email LIKE '%@example.com'
                LIMIT 10
            """)
            
            similar_customers = cursor.fetchall()
            if similar_customers:
                print(f"✅ Found {len(similar_customers)} similar customers:")
                for customer in similar_customers:
                    print(f"   ID: {customer[0]} | {customer[1]} {customer[2]} | {customer[3]}")
            else:
                print("❌ No similar customers found")
                
        cursor.close()
        conn.close()
        print("\n✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Error testing database queries: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🧪 Customer Service Bot SQL Retrieval Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Test 1: Direct database lookup
    test_database_lookup()
    
    # Test 2: Complete chat flow
    test_chat_flow()
    
    # Test 3: Raw database queries
    test_specific_customer_queries()
    
    print("\n" + "=" * 60)
    print(f"⏰ Test completed at: {datetime.now()}")
    print("🏁 All tests finished!")

if __name__ == "__main__":
    main()
