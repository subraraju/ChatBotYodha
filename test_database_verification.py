"""Test database connection and verify tables"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

def test_database_connection():
    """Test if we can connect to the PostgreSQL database"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in environment variables")
            return False
            
        print(f"🔍 Testing connection to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[-1], '***')}")
        
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"   PostgreSQL Version: {version.split(',')[0]}")
            
        return True, engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False, None


def check_existing_tables(engine):
    """Check what tables actually exist in the database"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Found {len(tables)} tables in database:")
        for table in tables:
            print(f"  • {table}")
            
            # Get column info for each table
            columns = inspector.get_columns(table)
            print(f"    Columns: {', '.join([col['name'] for col in columns])}")
        
        return tables
    except Exception as e:
        print(f"❌ Failed to get table information: {e}")
        return []


def check_table_data(engine, tables):
    """Check if tables have data"""
    try:
        with engine.connect() as connection:
            for table in tables[:5]:  # Limit to first 5 tables
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.fetchone()[0]
                    print(f"  📊 {table}: {count} rows")
                except Exception as e:
                    print(f"  ❌ {table}: Error reading - {e}")
    except Exception as e:
        print(f"❌ Failed to check table data: {e}")


def test_agent_database_schema():
    """Test what schema the agent is using"""
    try:
        from chatbot.agent import EnhancedChatAgent
        
        agent = EnhancedChatAgent()
        
        if hasattr(agent, 'database_schema') and agent.database_schema:
            print(f"\n🔍 Agent's Database Schema:")
            print("=" * 50)
            
            # Count tables in agent's schema
            schema_lines = agent.database_schema.split('\n')
            create_table_lines = [line for line in schema_lines if 'CREATE TABLE' in line.upper()]
            
            print(f"Agent thinks there are {len(create_table_lines)} tables:")
            for line in create_table_lines:
                # Extract table name
                table_name = line.split('CREATE TABLE')[-1].split('(')[0].strip()
                print(f"  • {table_name}")
            
            # Show first few lines of schema
            print(f"\nFirst 10 lines of agent schema:")
            for i, line in enumerate(schema_lines[:10]):
                if line.strip():
                    print(f"  {i+1}: {line}")
                    
            return True
        else:
            print("❌ Agent has no database schema loaded")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test agent schema: {e}")
        return False


def compare_schemas(actual_tables):
    """Compare actual database tables with what agent expects"""
    expected_tables = ['customers', 'products', 'sales', 'activities']
    
    print(f"\n🔄 Schema Comparison:")
    print("=" * 30)
    
    print("Expected tables:")
    for table in expected_tables:
        status = "✅" if table in [t.lower() for t in actual_tables] else "❌"
        print(f"  {status} {table}")
    
    print("\nActual tables not in expected:")
    unexpected = [t for t in actual_tables if t.lower() not in expected_tables]
    for table in unexpected:
        print(f"  ❓ {table}")


def main():
    print("🔍 Database Connection and Schema Verification")
    print("=" * 60)
    
    # Test database connection
    success, engine = test_database_connection()
    if not success:
        return
    
    # Check existing tables
    print(f"\n📋 Checking Database Tables...")
    actual_tables = check_existing_tables(engine)
    
    if actual_tables:
        # Check table data
        print(f"\n📊 Checking Table Data...")
        check_table_data(engine, actual_tables)
        
        # Test agent schema
        print(f"\n🤖 Checking Agent Schema...")
        test_agent_database_schema()
        
        # Compare schemas
        compare_schemas(actual_tables)
        
        print(f"\n💡 Summary:")
        print(f"  • Database connection: Working ✅")
        print(f"  • Tables found: {len(actual_tables)}")
        print(f"  • Agent schema loaded: {'✅' if 'Enhanced' in str(type(agent)) else '❌'}")
    
    else:
        print("⚠️  No tables found in database. You may need to run table creation scripts.")


if __name__ == "__main__":
    main()
