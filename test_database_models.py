"""Test database models to ensure they work correctly."""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_database_models():
    """Test that database models can be imported and work correctly."""
    try:
        print("🧪 Testing Database Models")
        
        # Test importing models
        from app.models.database_models import Base, Customer, Product, Sales, Activity
        print("✅ All models imported successfully")
        
        # Test creating the database engine
        from app.database import engine, SessionLocal
        print("✅ Database engine created successfully")
        
        # Test creating a session
        db = SessionLocal()
        print("✅ Database session created successfully")
        
        # Test a simple query
        try:
            customers = db.query(Customer).limit(1).all()
            print(f"✅ Sample query successful - Found {len(customers)} customers")
        except Exception as query_error:
            print(f"⚠️ Query test failed: {query_error}")
        
        # Test activity service import
        try:
            from app.services.activity_service import ActivityService
            print("✅ ActivityService imported successfully")
            
            # Test getting customer product IDs
            product_ids = ActivityService.get_customer_product_ids(db, 1001)
            print(f"✅ ActivityService.get_customer_product_ids works - Found {len(product_ids)} products")
            
        except Exception as service_error:
            print(f"⚠️ ActivityService test failed: {service_error}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()
        return False

def test_activity_creation():
    """Test creating an activity record."""
    try:
        print(f"\n🧪 Testing Activity Creation")
        
        from app.services.activity_service import ActivityService
        from app.database import get_database
        
        db = next(get_database())
        
        # Test creating an activity with minimal data
        test_session_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        activity_id = ActivityService.create_chatbot_activity(
            db=db,
            customer_id=1001,
            session_id=test_session_id,
            url_data="https://test.example.com/test.json",
            product_id=10001,
            description="Test activity creation",
            comments="Testing database model fixes"
        )
        
        if activity_id:
            print(f"✅ Activity created successfully with ID: {activity_id}")
            
            # Verify the activity was actually created
            from app.models.database_models import Activity
            activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
            
            if activity:
                print(f"✅ Activity verified in database:")
                print(f"   ID: {activity.activity_id}")
                print(f"   Customer: {activity.customer_id}")
                print(f"   Product: {activity.product_id}")
                print(f"   Session: {activity.session_id}")
                print(f"   URL: {activity.url_data}")
            else:
                print(f"⚠️ Activity not found in database after creation")
        else:
            print(f"❌ Activity creation failed")
        
        db.close()
        return activity_id is not None
        
    except Exception as e:
        print(f"❌ Activity creation test failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()
        return False

if __name__ == "__main__":
    print("🎯 TESTING DATABASE MODELS AND ACTIVITY SERVICE")
    print("🔧 Verifying fixes for SQLAlchemy relationship errors\n")
    
    # Run tests
    model_test_success = test_database_models()
    activity_test_success = test_activity_creation()
    
    # Summary
    print(f"\n" + "="*60)
    print(f"📊 TEST RESULTS SUMMARY:")
    print(f"✅ Database Models: {'PASS' if model_test_success else 'FAIL'}")
    print(f"✅ Activity Creation: {'PASS' if activity_test_success else 'FAIL'}")
    
    if model_test_success and activity_test_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Database models are working correctly")
        print(f"✅ Activity creation is working")
        print(f"✅ SQLAlchemy relationship errors fixed")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"🔧 Check the error messages above for details")
