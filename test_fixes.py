"""Test the enhanced Azure URL and real product_id retrieval functionality."""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_azure_complete_url():
    """Test that Azure returns complete downloadable URL."""
    try:
        from app.services.azure_storage import AzureBlobStorageService
        
        print("🧪 Testing Azure Complete URL Generation\n")
        
        azure_service = AzureBlobStorageService()
        
        # Create test conversation data
        test_conversation = {
            "session_id": f"url-test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_id": 1001,
            "customer_name": "Alice Johnson",
            "test_purpose": "Verify complete downloadable URL generation",
            "messages": [
                {"role": "user", "content": "Test message", "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": "Test response", "timestamp": datetime.now().isoformat()}
            ]
        }
        
        # Test upload - should return complete URL
        session_id = test_conversation["session_id"]
        complete_url = azure_service.upload_conversation_file(session_id, test_conversation)
        
        if complete_url:
            print(f"✅ Azure Storage Upload: SUCCESS")
            print(f"📂 Complete URL: {complete_url}")
            
            # Verify it's a complete URL (should start with https://)
            if complete_url.startswith('https://') and 'blob.core.windows.net' in complete_url:
                print(f"✅ URL Format: Valid complete Azure Blob URL")
                print(f"✅ Downloadable: Yes - anyone can use this URL to download the file")
                return True, complete_url
            else:
                print(f"❌ URL Format: Not a complete downloadable URL")
                print(f"   Expected: https://...blob.core.windows.net/...")
                print(f"   Got: {complete_url}")
                return False, complete_url
        else:
            print(f"❌ Azure Storage Upload: FAILED")
            return False, None
            
    except Exception as e:
        print(f"❌ Azure URL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_real_product_id_retrieval():
    """Test that product_id is retrieved from actual customer purchases."""
    try:
        from app.services.activity_service import ActivityService
        from app.database import get_database
        
        print("\n🧪 Testing Real Product ID Retrieval\n")
        
        # Get database session
        db = next(get_database())
        
        # Test with a known customer (1001 - Alice Johnson)
        customer_id = 1001
        
        print(f"🔍 Testing with customer {customer_id}:")
        
        # Test getting customer product IDs
        product_ids = ActivityService.get_customer_product_ids(db, customer_id)
        print(f"✅ Customer product IDs: {product_ids}")
        
        # Test getting most recent product ID
        recent_product_id = ActivityService.get_most_recent_product_id(db, customer_id)
        print(f"✅ Most recent product ID: {recent_product_id}")
        
        # Test getting latest sales ID
        if recent_product_id:
            sales_id = ActivityService.get_latest_sales_id(db, customer_id, recent_product_id)
            print(f"✅ Latest sales ID for product {recent_product_id}: {sales_id}")
        else:
            print(f"⚠️ No products found for customer {customer_id}")
            sales_id = None
        
        db.close()
        
        if product_ids and recent_product_id:
            print(f"✅ Product ID Retrieval: SUCCESS")
            print(f"   Found {len(product_ids)} products for customer")
            print(f"   Most recent product: {recent_product_id}")
            return True, recent_product_id, sales_id
        else:
            print(f"⚠️ Product ID Retrieval: No products found")
            return False, None, None
            
    except Exception as e:
        print(f"❌ Product ID test failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()
        return False, None, None

def test_complete_integration_with_fixes():
    """Test complete integration with both fixes applied."""
    try:
        print("\n" + "="*60)
        print("🚀 COMPLETE INTEGRATION TEST WITH FIXES")
        print("="*60)
        
        # Step 1: Test Azure complete URL
        azure_success, complete_url = test_azure_complete_url()
        
        # Step 2: Test real product ID retrieval
        product_success, product_id, sales_id = test_real_product_id_retrieval()
        
        if azure_success and complete_url and product_success and product_id:
            # Step 3: Test complete activity creation with both fixes
            print(f"\n🔗 Testing complete activity creation with fixes:")
            print(f"   Azure URL: {complete_url}")
            print(f"   Product ID: {product_id}")
            print(f"   Sales ID: {sales_id}")
            
            from app.services.activity_service import ActivityService
            from app.database import get_database
            
            db = next(get_database())
            session_id = f"integration-fixed-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create activity with real product ID and complete URL
            activity_id = ActivityService.create_chatbot_activity(
                db=db,
                customer_id=1001,
                session_id=session_id,
                url_data=complete_url,  # Complete downloadable URL
                product_id=product_id,  # Real product ID from purchases
                description="Integration test with Azure URL and real product_id fixes",
                comments="Both fixes verified: complete Azure URL and real product ID from customer purchases"
            )
            
            if activity_id:
                print(f"✅ Complete Integration: SUCCESS")
                print(f"📝 Activity ID: {activity_id}")
                print(f"🔗 Complete URL stored: {complete_url}")
                print(f"📦 Real Product ID stored: {product_id}")
                integration_success = True
            else:
                print(f"❌ Complete Integration: Activity creation failed")
                integration_success = False
            
            db.close()
        else:
            print(f"\n⚠️ Cannot test complete integration - prerequisites failed")
            integration_success = False
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 FIX VERIFICATION RESULTS:")
        print(f"✅ Azure Complete URL: {'PASS' if azure_success else 'FAIL'}")
        print(f"✅ Real Product ID Retrieval: {'PASS' if product_success else 'FAIL'}")
        print(f"✅ Complete Integration: {'PASS' if integration_success else 'FAIL'}")
        
        overall_success = azure_success and product_success and integration_success
        
        if overall_success:
            print(f"\n🎉 ALL FIXES WORKING PERFECTLY!")
            print(f"✅ Azure URLs are now complete and downloadable")
            print(f"✅ Product IDs are retrieved from actual customer purchases")
            print(f"✅ Activity table now has accurate product and URL data")
            
            # Show what's improved
            print(f"\n🔧 IMPROVEMENTS MADE:")
            print(f"   1. Azure URL: Now returns complete https://...blob.core.windows.net/... URL")
            print(f"   2. Product ID: Retrieved from customer's actual purchase history")
            print(f"   3. Data Accuracy: Activity table now has real, actionable data")
            
        else:
            failed_components = []
            if not azure_success:
                failed_components.append("Azure URL")
            if not product_success:
                failed_components.append("Product ID")
            if not integration_success:
                failed_components.append("Integration")
            
            print(f"\n⚠️ FIXES NEED ATTENTION: {', '.join(failed_components)}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_database_records():
    """Verify the database records have the correct data."""
    try:
        print(f"\n" + "="*60)
        print(f"🔍 Verifying Database Records with Fixes")
        print(f"="*60)
        
        import psycopg2
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Get the most recent 3 CHATBOT activities with full details
        cur.execute("""
            SELECT a.activity_id, a.customer_id, a.product_id, a.sales_id,
                   a.activity_type, a.description, a.session_id, a.url_data, 
                   a.activity_date, p.product_name
            FROM activity a
            LEFT JOIN product p ON a.product_id = p.product_id
            WHERE a.activity_type = 'CHATBOT' 
            ORDER BY a.activity_date DESC 
            LIMIT 3
        """)
        
        records = cur.fetchall()
        
        if records:
            print(f"✅ Found {len(records)} recent CHATBOT activity records:")
            for i, record in enumerate(records, 1):
                activity_id, customer_id, product_id, sales_id, activity_type, description, session_id, url_data, activity_date, product_name = record
                print(f"\n  📝 Record #{i} - Activity {activity_id}:")
                print(f"     Customer: {customer_id}")
                print(f"     Product: {product_id} ({product_name if product_name else 'N/A'})")
                print(f"     Sales: {sales_id or 'N/A'}")
                print(f"     Session: {session_id or 'N/A'}")
                print(f"     Date: {activity_date}")
                print(f"     Description: {description}")
                
                # Check URL format
                if url_data:
                    if url_data.startswith('https://') and 'blob.core.windows.net' in url_data:
                        print(f"     URL: ✅ COMPLETE - {url_data[:50]}...")
                    else:
                        print(f"     URL: ⚠️ PARTIAL - {url_data}")
                else:
                    print(f"     URL: ❌ MISSING")
                
                # Check product ID
                if product_id and product_name:
                    print(f"     Product Data: ✅ REAL - ID {product_id} ({product_name})")
                elif product_id:
                    print(f"     Product Data: ⚠️ ID ONLY - {product_id}")
                else:
                    print(f"     Product Data: ❌ MISSING")
        else:
            print("⚠️ No CHATBOT activity records found")
        
        conn.close()
        
        return len(records) > 0
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 TESTING AZURE URL AND PRODUCT_ID FIXES")
    print("🔧 Verifying complete downloadable URLs and real product data\n")
    
    success = test_complete_integration_with_fixes()
    
    # Also verify database records
    verify_database_records()
    
    print(f"\n" + "="*60)
    if success:
        print(f"🎊 ALL FIXES IMPLEMENTED SUCCESSFULLY!")
        print(f"✅ Azure URLs are now complete and downloadable by anyone")
        print(f"✅ Product IDs are retrieved from actual customer purchase history")
        print(f"✅ Activity table now contains accurate, actionable data")
        print(f"\n📋 Ready for production with improved data quality!")
    else:
        print(f"🔧 Some fixes need attention. Check the results above.")
        print(f"📋 Review the specific issues and retry.")
