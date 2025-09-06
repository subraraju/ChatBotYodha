"""Demo script to test session closing and conversation storage functionality."""

import sys
import os
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_azure_storage():
    """Test Azure Blob Storage functionality."""
    try:
        from app.services.azure_storage import AzureBlobStorageService
        
        print("=== Testing Azure Blob Storage ===")
        
        # Initialize service
        azure_service = AzureBlobStorageService()
        print("✅ Azure Blob Storage service initialized")
        
        # Create test conversation data
        test_conversation = {
            "export_metadata": {
                "timestamp": datetime.now().isoformat(),
                "company_name": "Contoso",
                "session_id": "test_session_123",
                "total_messages": 3,
                "app_version": "1.0",
                "export_format": "test_session_closure"
            },
            "session_info": {
                "customer_id": 1,
                "customer_state": "identified",
                "session_start_time": datetime.now().isoformat(),
                "session_end_time": datetime.now().isoformat()
            },
            "conversation": [
                {
                    "message_id": 1,
                    "timestamp": datetime.now().isoformat(),
                    "role": "user",
                    "content": "Hello, I need help with my order"
                },
                {
                    "message_id": 2,
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant", 
                    "content": "I'd be happy to help! Can you provide your email?"
                },
                {
                    "message_id": 3,
                    "timestamp": datetime.now().isoformat(),
                    "role": "user",
                    "content": "Thanks for your help. Goodbye!"
                }
            ]
        }
        
        # Test uploading conversation
        session_id = "test_session_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_url = azure_service.upload_conversation_file(session_id, test_conversation)
        
        if blob_url:
            print(f"✅ Test conversation uploaded successfully to: {blob_url}")
            return True
        else:
            print("❌ Failed to upload test conversation")
            return False
            
    except Exception as e:
        print(f"❌ Azure storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_activity_service():
    """Test Activity Service functionality."""
    try:
        from app.database import get_database
        from app.services.activity_service import ActivityService
        
        print("\n=== Testing Activity Service ===")
        
        db = next(get_database())
        
        # Test getting latest sales_id
        customer_id = 1001  # Use valid customer ID
        sales_id = ActivityService.get_latest_sales_id(db, customer_id)
        print(f"✅ Latest sales_id for customer {customer_id}: {sales_id}")
        
        # Test creating activity record
        session_id = f"{customer_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
        test_url = "yodhaassistant/documents/sessions/test_session.json"
        
        activity_id = ActivityService.create_chatbot_activity(
            db=db,
            customer_id=customer_id,
            session_id=session_id,
            url_data=test_url,
            description="Test chatbot session",
            comments="Testing session closure functionality"
        )
        
        if activity_id:
            print(f"✅ Test activity created with ID: {activity_id}")
            
            # Test updating activity with conversation summary
            test_summary = {
                "export_metadata": {"total_messages": 5},
                "session_info": {"customer_state": "resolved", "recent_purchases": [{"product": "test"}]}
            }
            
            success = ActivityService.update_activity_with_conversation_summary(
                db=db,
                activity_id=activity_id,
                conversation_summary=test_summary
            )
            
            if success:
                print("✅ Activity updated with conversation summary")
            else:
                print("⚠️ Failed to update activity summary")
            
            return True
        else:
            print("❌ Failed to create test activity")
            return False
            
    except Exception as e:
        print(f"❌ Activity service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Run all tests."""
    print("🧪 Testing Session Closure and Conversation Storage\n")
    
    azure_success = test_azure_storage()
    activity_success = test_activity_service()
    
    print(f"\n📊 Test Results:")
    print(f"Azure Blob Storage: {'✅ PASS' if azure_success else '❌ FAIL'}")
    print(f"Activity Service: {'✅ PASS' if activity_success else '❌ FAIL'}")
    
    if azure_success and activity_success:
        print("\n🎉 All tests passed! Session closure functionality is ready.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()
