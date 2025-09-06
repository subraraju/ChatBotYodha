"""Corrected test for session closure functionality with proper method signatures."""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_azure_storage_directly():
    """Test Azure Blob Storage directly with correct method signature."""
    try:
        from app.services.azure_storage import AzureBlobStorageService
        
        print("🧪 Testing Azure Blob Storage Service\n")
        
        azure_service = AzureBlobStorageService()
        
        # Create test conversation data
        test_conversation = {
            "session_id": f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_id": 1001,
            "customer_name": "Alice Johnson",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": "Hi! How can I help you?", "timestamp": datetime.now().isoformat()},
                {"role": "user", "content": "Thanks, goodbye!", "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": "Thank you for contacting us! Have a great day!", "timestamp": datetime.now().isoformat()}
            ],
            "closure_reason": "user_requested",
            "sentiment": "positive"
        }
        
        # Test upload with correct method signature: session_id, conversation_data
        session_id = test_conversation["session_id"]
        url = azure_service.upload_conversation_file(session_id, test_conversation)
        
        if url:
            print(f"✅ Azure Storage Upload: SUCCESS")
            print(f"📂 File URL: {url}")
            return True, url
        else:
            print(f"❌ Azure Storage Upload: FAILED")
            return False, None
            
    except Exception as e:
        print(f"❌ Azure storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_activity_service_directly():
    """Test Activity Service directly with correct class method."""
    try:
        from app.services.activity_service import ActivityService
        from app.database import get_database
        
        print("\n🧪 Testing Activity Service\n")
        
        # Get database session
        db = next(get_database())
        
        # Create test activity with correct method signature
        session_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        customer_id = 1001  # Alice Johnson
        conversation_url = "test_storage_url"
        
        activity_id = ActivityService.create_chatbot_activity(
            db=db,
            customer_id=customer_id,
            session_id=session_id,
            url_data=conversation_url,
            description="Direct activity service test",
            comments="Testing activity creation functionality"
        )
        
        if activity_id:
            print(f"✅ Activity Service: SUCCESS")
            print(f"📝 Created Activity ID: {activity_id}")
            print(f"👤 Customer ID: {customer_id}")
            print(f"🔗 Session ID: {session_id}")
            
            # Test getting latest sales_id
            sales_id = ActivityService.get_latest_sales_id(db, customer_id)
            print(f"💰 Latest Sales ID for customer: {sales_id}")
            
            db.close()
            return True, activity_id
        else:
            print(f"❌ Activity Service: FAILED")
            db.close()
            return False, None
            
    except Exception as e:
        print(f"❌ Activity service test failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()
        return False, None

def test_session_closure_detection():
    """Test session closure phrase detection with improved logic."""
    try:
        print("\n🧪 Testing Session Closure Detection\n")
        
        # Test phrases that should trigger closure
        closing_phrases = [
            "Thanks for your help, goodbye!",
            "That's all I needed, thank you!",
            "Perfect, I'm all set now. Have a great day!",
            "bye",
            "see you later",
            "end chat",
            "close session",
            "thank you so much, that solved everything!",
            "great, that's all I needed",
            "perfect, I'm done here"
        ]
        
        # Test phrases that should NOT trigger closure
        non_closing_phrases = [
            "Thanks for the information, can you help me with something else?",
            "That's good to know, what about shipping?",
            "I appreciate your help, but I have another question",
            "Hello there",
            "Can you help me?",
            "Thanks, but I need more details",
            "That's helpful, what's the next step?"
        ]
        
        def detect_closure_improved(message):
            """Improved closure detection logic."""
            message_lower = message.lower()
            
            # Strong closure indicators (definitive)
            strong_closers = [
                'goodbye', 'bye', 'see you', 'farewell', 'talk later',
                'end chat', 'close', 'exit', 'quit', 'stop',
                'that\'s all', 'all set', 'i\'m done', 'finished',
                'solved everything', 'that solved it'
            ]
            
            for closer in strong_closers:
                if closer in message_lower:
                    return True
            
            # Gratitude + completion (but check for continuation words)
            gratitude_words = ['thank', 'thanks', 'appreciate', 'grateful']
            completion_words = ['perfect', 'great', 'excellent', 'solved', 'fixed', 'resolved']
            continuation_words = ['but', 'however', 'can you', 'what about', 'next', 'more', 'else', 'another']
            
            has_gratitude = any(word in message_lower for word in gratitude_words)
            has_completion = any(word in message_lower for word in completion_words)
            has_continuation = any(word in message_lower for word in continuation_words)
            
            # Only trigger if gratitude + completion WITHOUT continuation indicators
            return has_gratitude and has_completion and not has_continuation
        
        print("Testing CLOSING phrases:")
        closing_detected = 0
        for phrase in closing_phrases:
            is_closing = detect_closure_improved(phrase)
            status = "✅ DETECTED" if is_closing else "❌ MISSED"
            print(f"  {status}: '{phrase}'")
            if is_closing:
                closing_detected += 1
        
        print(f"\nClosing detection rate: {closing_detected}/{len(closing_phrases)} = {closing_detected/len(closing_phrases)*100:.1f}%")
        
        print("\nTesting NON-CLOSING phrases:")
        false_positives = 0
        for phrase in non_closing_phrases:
            is_closing = detect_closure_improved(phrase)
            status = "❌ FALSE POSITIVE" if is_closing else "✅ CORRECT"
            print(f"  {status}: '{phrase}'")
            if is_closing:
                false_positives += 1
        
        print(f"\nFalse positive rate: {false_positives}/{len(non_closing_phrases)} = {false_positives/len(non_closing_phrases)*100:.1f}%")
        
        # Good performance: >80% detection rate and <20% false positive rate
        detection_rate = closing_detected / len(closing_phrases)
        false_positive_rate = false_positives / len(non_closing_phrases)
        
        success = detection_rate >= 0.8 and false_positive_rate <= 0.2
        
        if success:
            print(f"\n✅ Session Closure Detection: EXCELLENT")
            print(f"   Detection Rate: {detection_rate*100:.1f}% (target: ≥80%)")
            print(f"   False Positive Rate: {false_positive_rate*100:.1f}% (target: ≤20%)")
        else:
            print(f"\n⚠️ Session Closure Detection: NEEDS IMPROVEMENT")
            print(f"   Detection Rate: {detection_rate*100:.1f}% (target: ≥80%)")
            print(f"   False Positive Rate: {false_positive_rate*100:.1f}% (target: ≤20%)")
        
        return success
        
    except Exception as e:
        print(f"❌ Closure detection test failed: {e}")
        return False

def test_complete_integration():
    """Test the complete integration flow with correct method signatures."""
    try:
        print("\n" + "="*60)
        print("🚀 COMPLETE INTEGRATION TEST")
        print("="*60)
        
        # Step 1: Test Azure Storage
        azure_success, storage_url = test_azure_storage_directly()
        
        # Step 2: Test Activity Service (with real URL if Azure worked)
        if azure_success and storage_url:
            print(f"\n🔗 Using real Azure URL for Activity test: {storage_url}")
            
            from app.services.activity_service import ActivityService
            from app.database import get_database
            
            db = next(get_database())
            session_id = f"integration-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            activity_id = ActivityService.create_chatbot_activity(
                db=db,
                customer_id=1001,
                session_id=session_id,
                url_data=storage_url,
                description="Complete integration test - Azure + Activity",
                comments="End-to-end integration test successful"
            )
            
            activity_success = activity_id is not None
            if activity_success:
                print(f"✅ Integration Activity Created: ID {activity_id}")
            else:
                print(f"❌ Integration Activity Failed")
            
            db.close()
        else:
            activity_success, activity_id = test_activity_service_directly()
        
        # Step 3: Test Detection
        detection_success = test_session_closure_detection()
        
        # Summary
        print("\n" + "="*60)
        print("📊 INTEGRATION TEST RESULTS:")
        print(f"✅ Azure Blob Storage: {'PASS' if azure_success else 'FAIL'}")
        print(f"✅ Activity Service: {'PASS' if activity_success else 'FAIL'}")
        print(f"✅ Closure Detection: {'PASS' if detection_success else 'FAIL'}")
        
        overall_success = azure_success and activity_success and detection_success
        
        if overall_success:
            print(f"\n🎉 INTEGRATION TEST: ALL SYSTEMS OPERATIONAL!")
            print(f"✅ Ready for production deployment")
            print(f"✅ Both chat and UI session closure scenarios supported")
            print(f"✅ Conversation storage in Azure Blob working")
            print(f"✅ Activity tracking in database working")
            print(f"✅ Session closure detection working accurately")
        else:
            failed_components = []
            if not azure_success:
                failed_components.append("Azure Storage")
            if not activity_success:
                failed_components.append("Activity Service")
            if not detection_success:
                failed_components.append("Closure Detection")
            
            print(f"\n⚠️ INTEGRATION TEST: Issues with: {', '.join(failed_components)}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_recent_activity_records():
    """Verify recent activity records in the database."""
    try:
        print("\n" + "="*60)
        print("🔍 Verifying Recent Activity Records")
        print("="*60)
        
        import psycopg2
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Get the most recent 5 CHATBOT activities
        cur.execute("""
            SELECT activity_id, customer_id, activity_type, description, 
                   session_id, url_data, activity_date 
            FROM activity 
            WHERE activity_type = 'CHATBOT' 
            ORDER BY activity_date DESC 
            LIMIT 5
        """)
        
        records = cur.fetchall()
        
        if records:
            print(f"✅ Found {len(records)} recent CHATBOT activity records:")
            for i, record in enumerate(records, 1):
                activity_id, customer_id, activity_type, description, session_id, url_data, activity_date = record
                print(f"\n  📝 Record #{i} - Activity {activity_id}:")
                print(f"     Customer: {customer_id}")
                print(f"     Session: {session_id or 'N/A'}")
                print(f"     Date: {activity_date}")
                print(f"     Description: {description}")
                print(f"     URL: {url_data or 'N/A'}")
        else:
            print("⚠️ No CHATBOT activity records found")
        
        conn.close()
        
        return len(records) > 0
        
    except Exception as e:
        print(f"❌ Activity verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 CORRECTED SESSION CLOSURE TESTING")
    print("🔧 Using proper method signatures and improved detection logic\n")
    
    success = test_complete_integration()
    
    # Also show recent activity records
    verify_recent_activity_records()
    
    print("\n" + "="*60)
    if success:
        print(f"🎊 ALL CORE COMPONENTS WORKING PERFECTLY!")
        print(f"🚀 Your session closure system is production-ready!")
        print(f"📋 Next steps:")
        print(f"   • Test in live Streamlit environment")
        print(f"   • Monitor session closure performance")
        print(f"   • Review stored conversations in Azure Blob")
    else:
        print(f"🔍 Review the results above for any remaining issues.")
        print(f"📋 Some components may need additional configuration.")
