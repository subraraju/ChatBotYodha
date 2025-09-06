"""
Query products purchased by a specific customer
"""
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# Load environment variables
load_dotenv()

def get_customer_products(customer_id=1008):
    """
    Fetch all products purchased by a specific customer
    """
    try:
        # Get database connection string
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in environment variables")
            return None
            
        print(f"🔍 Connecting to database...")
        print(f"🆔 Fetching products for customer ID: {customer_id}")
        
        # Connect to database with timeout
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Query to get products purchased by the customer with purchase details
        query = """
        SELECT 
            c.customer_id,
            c.first_name,
            c.last_name,
            c.email,
            p.product_id,
            p.product_name,
            p.category,
            p.type,
            p.price,
            s.quantity,
            s.sale_date,
            s.total_amount,
            s.sale_id
        FROM customer c
        JOIN sales s ON c.customer_id = s.customer_id
        JOIN product p ON s.product_id = p.product_id
        WHERE c.customer_id = %s
        ORDER BY s.sale_date DESC
        LIMIT 20;
        """
        
        print(f"🔍 Executing query...")
        cursor.execute(query, (customer_id,))
        
        # Fetch results
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Found {len(results)} product purchases for customer {customer_id}")
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(results, columns=column_names)
            
            # Display results
            print(f"\n📋 Products purchased by Customer {customer_id}:")
            print("=" * 80)
            
            # Customer info (from first row)
            if len(df) > 0:
                first_row = df.iloc[0]
                print(f"Customer: {first_row['first_name']} {first_row['last_name']}")
                print(f"Email: {first_row['email']}")
                print(f"Total Purchases Found: {len(df)}")
                print()
            
            # Display purchase details
            for index, row in df.iterrows():
                print(f"{index + 1:2d}. {row['product_name']}")
                print(f"    Category: {row['category']} | Type: {row['type']}")
                print(f"    Price: ${row['price']} | Quantity: {row['quantity']} | Total: ${row['total_amount']}")
                print(f"    Purchase Date: {row['sale_date']} | Sale ID: {row['sale_id']}")
                print()
            
            # Save to CSV
            filename = f"customer_{customer_id}_products.csv"
            df.to_csv(filename, index=False)
            print(f"📁 Data saved to: {filename}")
            
            # Summary statistics
            print(f"\n📊 Summary for Customer {customer_id}:")
            print(f"  • Total Purchases: {len(df)}")
            print(f"  • Total Amount Spent: ${df['total_amount'].sum():.2f}")
            print(f"  • Average Order Value: ${df['total_amount'].mean():.2f}")
            print(f"  • Unique Products: {df['product_id'].nunique()}")
            print(f"  • Date Range: {df['sale_date'].min()} to {df['sale_date'].max()}")
            
            # Category breakdown
            category_summary = df.groupby('category')['total_amount'].agg(['count', 'sum']).round(2)
            print(f"\n🏷️ Category Breakdown:")
            for category, stats in category_summary.iterrows():
                print(f"  • {category}: {stats['count']} purchases, ${stats['sum']:.2f}")
            
            return df
            
        else:
            print(f"❌ No products found for customer ID: {customer_id}")
            
            # Check if customer exists
            cursor.execute("SELECT customer_id, first_name, last_name FROM customer WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            
            if customer_info:
                print(f"✅ Customer exists: {customer_info[1]} {customer_info[2]}")
                print("   But no purchase history found.")
            else:
                print(f"❌ Customer ID {customer_id} does not exist in database")
            
            return None
            
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 This might be due to:")
        print("  • Network connectivity issues")
        print("  • Database server being down")
        print("  • Firewall blocking the connection")
        return None
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("🔐 Database connection closed")


def get_all_products_for_customer(customer_id=1008):
    """
    Alternative query - get all available products with purchase status for customer
    """
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()
        
        # Query to show all products with purchase status for the customer
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.type,
            p.price,
            p.stock_quantity,
            CASE 
                WHEN s.customer_id IS NOT NULL THEN 'Purchased'
                ELSE 'Not Purchased'
            END as purchase_status,
            COALESCE(s.quantity, 0) as quantity_bought,
            COALESCE(s.total_amount, 0) as amount_spent,
            s.sale_date as last_purchase_date
        FROM product p
        LEFT JOIN sales s ON p.product_id = s.product_id AND s.customer_id = %s
        ORDER BY 
            CASE WHEN s.customer_id IS NOT NULL THEN 0 ELSE 1 END,
            s.sale_date DESC NULLS LAST,
            p.product_name
        LIMIT 50;
        """
        
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        
        if results:
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=column_names)
            
            print(f"\n🛍️ All Products with Purchase Status for Customer {customer_id}:")
            print("=" * 100)
            
            purchased_products = df[df['purchase_status'] == 'Purchased']
            not_purchased = df[df['purchase_status'] == 'Not Purchased']
            
            print(f"✅ Products Purchased ({len(purchased_products)}):")
            for _, row in purchased_products.iterrows():
                print(f"  • {row['product_name']} ({row['category']}) - Qty: {row['quantity_bought']}, Spent: ${row['amount_spent']}")
            
            print(f"\n🛒 Products Available but Not Purchased ({len(not_purchased)}):")
            for _, row in not_purchased.head(10).iterrows():  # Show first 10
                print(f"  • {row['product_name']} ({row['category']}) - Price: ${row['price']}")
            
            filename = f"customer_{customer_id}_all_products.csv"
            df.to_csv(filename, index=False)
            print(f"\n📁 Complete product list saved to: {filename}")
            
            return df
            
    except Exception as e:
        print(f"❌ Error in alternative query: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def main():
    """Main function to run the customer products query"""
    
    # Get customer ID from command line or use default
    customer_id = 1008
    if len(sys.argv) > 1:
        try:
            customer_id = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid customer ID. Using default: 1008")
    
    print(f"🚀 Customer Products Query Tool")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run main query
    df1 = get_customer_products(customer_id)
    
    # Run alternative query
    print("\n" + "=" * 60)
    df2 = get_all_products_for_customer(customer_id)
    
    if df1 is not None or df2 is not None:
        print(f"\n✅ Query completed successfully!")
        print(f"💡 Try different customer IDs: python query_customer_products.py 1001")
    else:
        print(f"\n❌ Query failed. Check database connection.")


if __name__ == "__main__":
    main()
