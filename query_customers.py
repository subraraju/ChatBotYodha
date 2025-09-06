"""
Script to query customer table and fetch sample rows
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        # Get connection parameters from environment
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        print(f"🔍 Connecting to database: {connection_params['host']}:{connection_params['port']}/{connection_params['database']}")
        print(f"   User: {connection_params['user']}")
        
        # Create connection with timeout
        conn = psycopg2.connect(
            **connection_params,
            connect_timeout=10
        )
        
        print("✅ Database connection successful!")
        return conn
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def query_customer_table(conn, limit=10):
    """Query customer table and return results"""
    try:
        # Create cursor that returns dict-like results
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to get customer data
        query = f"""
        SELECT 
            customer_id,
            party_type,
            first_name,
            last_name,
            email,
            phone,
            city,
            state,
            zipcode,
            created_at
        FROM customer 
        ORDER BY customer_id 
        LIMIT {limit};
        """
        
        print(f"🔍 Executing query:")
        print(f"   {query.strip()}")
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"✅ Query executed successfully!")
        print(f"   Found {len(results)} customer records")
        
        cursor.close()
        return results
        
    except psycopg2.Error as e:
        print(f"❌ Database query error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected query error: {e}")
        return None

def display_results(results):
    """Display query results in a formatted way"""
    if not results:
        print("No results to display")
        return
    
    print(f"\n📋 Customer Table Results ({len(results)} rows):")
    print("=" * 80)
    
    for i, row in enumerate(results, 1):
        print(f"\n🔹 Customer {i}:")
        print(f"   ID: {row['customer_id']}")
        print(f"   Name: {row['first_name'] or 'N/A'} {row['last_name'] or 'N/A'}")
        print(f"   Email: {row['email'] or 'N/A'}")
        print(f"   Phone: {row['phone'] or 'N/A'}")
        print(f"   Location: {row['city'] or 'N/A'}, {row['state'] or 'N/A'} {row['zipcode'] or 'N/A'}")
        print(f"   Type: {row['party_type'] or 'N/A'}")
        print(f"   Created: {row['created_at'] or 'N/A'}")

def save_to_csv(results, filename='customer_sample.csv'):
    """Save results to CSV file"""
    if not results:
        print("No data to save")
        return
    
    try:
        # Convert to pandas DataFrame for easy CSV export
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to: {filename}")
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")

def get_table_info(conn):
    """Get information about the customer table structure"""
    try:
        cursor = conn.cursor()
        
        # Query to get column information
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'customer' 
        ORDER BY ordinal_position;
        """
        
        cursor.execute(query)
        columns = cursor.fetchall()
        
        print(f"\n📊 Customer Table Structure:")
        print("-" * 60)
        print(f"{'Column':<20} {'Type':<15} {'Nullable':<10} {'Default'}")
        print("-" * 60)
        
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            default_str = str(column_default)[:15] if column_default else 'None'
            print(f"{column_name:<20} {data_type:<15} {is_nullable:<10} {default_str}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error getting table info: {e}")

def main():
    print("🗄️  Customer Table Query Script")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        print("\n❌ Cannot proceed without database connection")
        print("\n💡 Troubleshooting tips:")
        print("   • Check if the database server is running")
        print("   • Verify network connectivity to 4.155.102.23:5432")
        print("   • Confirm credentials are correct")
        print("   • Check firewall settings")
        return
    
    try:
        # Get table structure info
        get_table_info(conn)
        
        # Query customer data
        print(f"\n🔍 Querying Customer Data...")
        results = query_customer_table(conn, limit=10)
        
        if results:
            # Display results
            display_results(results)
            
            # Ask if user wants to save to CSV
            save_csv = input(f"\n💾 Save results to CSV? (y/n): ").lower().strip()
            if save_csv in ['y', 'yes']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"customer_sample_{timestamp}.csv"
                save_to_csv(results, filename)
            
            # Show summary
            print(f"\n📈 Summary:")
            print(f"   • Total customers found: {len(results)}")
            print(f"   • Customers with email: {sum(1 for r in results if r['email'])}")
            print(f"   • Customers with phone: {sum(1 for r in results if r['phone'])}")
            print(f"   • Complete profiles: {sum(1 for r in results if r['email'] and r['phone'] and r['first_name'])}")
        
        else:
            print("❌ No data retrieved from customer table")
    
    finally:
        # Always close the connection
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    main()
