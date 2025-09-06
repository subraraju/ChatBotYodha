"""
Test script for product support functionality
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_product_support_flow():
    """Test the product support flow with PDF search"""
    print("🛠️ Testing Product Support Flow")
    print("=" * 50)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ New session started")
        
        # Test conversation flow with product support
        test_messages = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "2",  # Select item 2 (HeatWave Mini)
            "How do I clean this product?",
            "What's the warranty period?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"👤 User: {message}")
            
            # Process the message
            response, updated_session = bot.process_message(message, session)
            session = updated_session
            
            print(f"🤖 Bot: {response}")
            print(f"📊 State: {session.customer_state.value}")
            
            if session.selected_product:
                print(f"🎯 Selected Product: {session.selected_product}")
                print(f"🔄 Help Attempts: {session.help_attempts}")
            
            print()
            
    except Exception as e:
        print(f"❌ Error testing product support flow: {e}")
        import traceback
        traceback.print_exc()

def test_product_extraction():
    """Test product extraction from user input"""
    print("\n🔍 Testing Product Extraction")
    print("=" * 50)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        bot = CustomerServiceBot()
        
        # Mock purchases
        mock_purchases = [
            {'product_name': 'StyleX Express'},
            {'product_name': 'HeatWave Mini'},
            {'product_name': 'ShinyLocks 360'},
            {'product_name': 'GlamStyle Max'}
        ]
        
        test_inputs = [
            "2",
            "heatwave",
            "mini",
            "StyleX",
            "shinylocks",
            "5",  # Invalid number
            "random product"  # Non-matching product
        ]
        
        for test_input in test_inputs:
            result = bot._extract_product_from_input(test_input, mock_purchases)
            print(f"Input: '{test_input}' -> Product: {result}")
            
    except Exception as e:
        print(f"❌ Error testing product extraction: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🧪 Product Support Functionality Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Test 1: Product support flow
    test_product_support_flow()
    
    # Test 2: Product extraction
    test_product_extraction()
    
    print("\n" + "=" * 60)
    print(f"⏰ Test completed at: {datetime.now()}")
    print("🏁 All tests finished!")

if __name__ == "__main__":
    main()
