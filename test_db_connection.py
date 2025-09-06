#!/usr/bin/env python3
"""
Database Connection Test Script
Tests the PostgreSQL database connection using credentials from .env file
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_psycopg2_connection():
    """Test connection using psycopg2 directly"""
    print("\n" + "="*50)
    print("Testing PostgreSQL Connection with psycopg2")
    print("="*50)
    
    try:
        # Connect using individual parameters
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        # Create cursor and test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"📊 Database: {current_db[0]}")
        print(f"👤 User: {current_user[0]}")
        print(f"🔧 PostgreSQL Version: {db_version[0]}")
        
        # Test if we can list tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("📋 No tables found in the public schema")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print("❌ psycopg2 connection failed:")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print("❌ Unexpected error:")
        print(f"   Error: {e}")
        return False

def test_sqlalchemy_connection():
    """Test connection using SQLAlchemy (used by the application)"""
    print("\n" + "="*50)
    print("Testing SQLAlchemy Connection")
    print("="*50)
    
    try:
        database_url = os.getenv('DATABASE_URL')
        print(f"🔗 Connection URL: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            
            result = connection.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            
            print("✅ SQLAlchemy connection successful!")
            print(f"📊 Database: {db_info[0]}")
            print(f"👤 User: {db_info[1]}")
            print(f"🔧 Version: {db_info[2]}")
            
            # Test table information
            result = connection.execute(text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"📋 Database schema information:")
                for table_name, table_type in tables:
                    print(f"  - {table_name} ({table_type})")
            else:
                print("📋 No tables found - database may need initialization")
        
        return True
        
    except SQLAlchemyError as e:
        print("❌ SQLAlchemy connection failed:")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print("❌ Unexpected error:")
        print(f"   Error: {e}")
        return False

def test_app_database_module():
    """Test the application's database module if it exists"""
    print("\n" + "="*50)
    print("Testing Application Database Module")
    print("="*50)
    
    try:
        # Try to import the app's database module
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app.database import engine, SessionLocal
        
        print("✅ Database module imported successfully")
        
        # Test session creation
        session = SessionLocal()
        result = session.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        session.close()
        
        print("✅ Database session created successfully")
        print(f"📊 Connected to: {db_info[0]} as {db_info[1]}")
        
        return True
        
    except ImportError as e:
        print("⚠️  Could not import app database module:")
        print(f"   {e}")
        return False
    except Exception as e:
        print("❌ Error testing app database module:")
        print(f"   Error: {e}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    print("🔍 Database Connection Test")
    print("📅 Date: " + str(os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip()))
    
    # Display configuration (without password)
    print("\n📋 Configuration:")
    print(f"   Host: {os.getenv('DB_HOST')}")
    print(f"   Port: {os.getenv('DB_PORT')}")
    print(f"   Database: {os.getenv('DB_NAME')}")
    print(f"   User: {os.getenv('DB_USER')}")
    print(f"   Password: {'*' * len(os.getenv('DB_PASSWORD', ''))}")
    
    # Run tests
    test_results = []
    test_results.append(("psycopg2 Direct", test_psycopg2_connection()))
    test_results.append(("SQLAlchemy", test_sqlalchemy_connection()))
    test_results.append(("App Database Module", test_app_database_module()))
    
    # Summary
    print("\n" + "="*50)
    print("🏁 Test Summary")
    print("="*50)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All database connections are working!")
    elif passed_tests > 0:
        print("⚠️  Some connections work, but there may be configuration issues")
    else:
        print("💥 All database connections failed - check your configuration")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
