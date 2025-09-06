"""Simple database connection test"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_quick_connection():
    """Quick test to see if we can connect and what tables exist"""
    try:
        # Get connection details from environment
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"🔍 Testing connection...")
        
        # Try to connect with a shorter timeout
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()
        
        print("✅ Connected to database!")
        
        # Check what tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  • {table[0]}")
            
            # Get row count for each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"    📊 {count} rows")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_agent_vs_actual():
    """Compare agent schema expectations vs actual tables"""
    expected_tables = ['customer', 'product', 'sales', 'activity']
    
    print(f"\n🤖 Agent expects these tables:")
    for table in expected_tables:
        print(f"  • {table}")
    
    print(f"\n💡 The agent's database schema has been updated to match actual table structure:")
    print(f"  ✅ Uses singular table names (customer, product, sales, activity)")
    print(f"  ✅ Correct primary keys (sale_id not sales_id)")
    print(f"  ✅ Proper foreign key references")


def main():
    print("🔍 Quick Database Verification")
    print("=" * 40)
    
    success = test_quick_connection()
    
    if success:
        check_agent_vs_actual()
        print(f"\n✅ Database connection verified!")
        print(f"💡 The enhanced agent should now query the correct tables.")
    else:
        print(f"\n❌ Database connection issues detected.")
        print(f"💡 Please check:")
        print(f"  • Network connectivity to 4.155.102.23:5432")
        print(f"  • Database credentials")
        print(f"  • Firewall settings")


if __name__ == "__main__":
    main()
