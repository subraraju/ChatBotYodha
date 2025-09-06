"""
Simple script to fetch customer products - tries multiple customer IDs
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def quick_customer_products(customer_id=1008):
    """Quick fetch of customer products with error handling"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"🔍 Trying customer ID: {customer_id}")
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        cursor = conn.cursor()
        
        # Simple query to get customer's products
        query = """
        SELECT 
            c.first_name, c.last_name, c.email,
            p.product_name, p.category, p.price,
            s.quantity, s.total_amount, s.sale_date
        FROM customer c
        JOIN sales s ON c.customer_id = s.customer_id  
        JOIN product p ON s.product_id = p.product_id
        WHERE c.customer_id = %s
        ORDER BY s.sale_date DESC
        LIMIT 10;
        """
        
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Found {len(results)} purchases for customer {customer_id}:")
            customer_name = f"{results[0][0]} {results[0][1]}"
            customer_email = results[0][2]
            print(f"📧 Customer: {customer_name} ({customer_email})")
            print()
            
            for i, row in enumerate(results, 1):
                print(f"{i:2d}. {row[3]} ({row[4]})")
                print(f"    ${row[5]} x {row[6]} = ${row[7]} on {row[8]}")
                print()
            
            return True
        else:
            print(f"❌ No purchases found for customer {customer_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def find_customers_with_purchases():
    """Find some customer IDs that have purchases"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        cursor = conn.cursor()
        
        # Get customers with purchases
        query = """
        SELECT DISTINCT c.customer_id, c.first_name, c.last_name, COUNT(s.sale_id) as purchase_count
        FROM customer c
        JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.first_name, c.last_name
        ORDER BY purchase_count DESC
        LIMIT 10;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            print(f"🛍️ Customers with purchases:")
            for row in results:
                print(f"  ID {row[0]}: {row[1]} {row[2]} ({row[3]} purchases)")
            
            return [row[0] for row in results]  # Return customer IDs
        else:
            print("❌ No customers with purchases found")
            return []
            
    except Exception as e:
        print(f"❌ Error finding customers: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    print("🚀 Quick Customer Products Query")
    print("=" * 40)
    
    # Try default customer ID
    success = quick_customer_products(1008)
    
    if not success:
        print("\n🔍 Looking for customers with purchases...")
        customer_ids = find_customers_with_purchases()
        
        if customer_ids:
            print(f"\n🎯 Trying first customer with purchases (ID: {customer_ids[0]}):")
            quick_customer_products(customer_ids[0])

if __name__ == "__main__":
    main()
