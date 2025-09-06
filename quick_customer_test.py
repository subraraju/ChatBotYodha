"""
Simple customer table query script with multiple connection methods
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection_simple():
    """Simple connection test"""
    print("🔍 Testing database connection...")
    
    try:
        # Connection string from environment
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in environment")
            return None
            
        print(f"   Using: {DATABASE_URL.split('@')[0]}@***")
        
        # Try connection with short timeout
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        print("✅ Connection successful!")
        
        return conn
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 This might be a network/firewall issue")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def quick_customer_query(conn):
    """Quick query to get customer data"""
    try:
        cursor = conn.cursor()
        
        # Simple query
        query = "SELECT customer_id, first_name, last_name, email FROM customer LIMIT 5;"
        print(f"🔍 Executing: {query}")
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"✅ Found {len(rows)} customers:")
        
        for row in rows:
            customer_id, first_name, last_name, email = row
            print(f"   {customer_id}: {first_name} {last_name} ({email})")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def main():
    print("🗄️  Quick Customer Table Test")
    print("=" * 40)
    
    # Test connection
    conn = test_connection_simple()
    
    if conn:
        # Try query
        success = quick_customer_query(conn)
        conn.close()
        
        if success:
            print("\n🎉 Database query successful!")
        else:
            print("\n❌ Query failed but connection worked")
    else:
        print("\n❌ Cannot connect to database")
        print("\n🔧 Possible solutions:")
        print("   1. Check if database server is running")
        print("   2. Verify network connectivity")
        print("   3. Confirm firewall allows connection to port 5432")
        print("   4. Try connecting from database management tool first")

if __name__ == "__main__":
    main()
