"""
Test the improved product support context retention
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_context_retention():
    """Test that the bot maintains context after 2 turns and allows continued conversation"""
    print("🧪 Testing Context Retention After 2 Turns")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ Bot initialized and session started")
        
        # Extended conversation to test context retention
        test_conversation = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "ShinyLocks 360",  # Select the product
            "How do I replace the internal circuit board?",  # Question 1 (likely no answer)
            "What is the warranty for the heating element?",  # Question 2 (likely no answer) - should trigger manufacturer contact
            "What are the measurements?",  # Question 3 - should still work and find answer
            "How do I clean this device?",  # Question 4 - test continued context
            "HeatWave Mini",  # Switch to different product
            "What is the temperature range?",  # Question about new product
        ]
        
        for i, message in enumerate(test_conversation, 1):
            print(f"\n{'='*20} Message {i} {'='*20}")
            print(f"👤 User: {message}")
            
            try:
                response, updated_session = bot.process_message(message, session)
                session = updated_session
                
                print(f"🤖 Bot Response:")
                # Truncate long responses for readability
                response_preview = response[:200] + "..." if len(response) > 200 else response
                print(f"   {response_preview}")
                print(f"📊 Current State: {session.customer_state.value}")
                
                if hasattr(session, 'selected_product') and session.selected_product:
                    print(f"🎯 Selected Product: {session.selected_product}")
                    print(f"🔄 Help Attempts: {session.help_attempts}")
                
                # Check for key behaviors
                if i == 5:  # After manufacturer contact
                    if "manufacturer" in response.lower() and "feel free" in response.lower():
                        print("✅ Manufacturer contact provided with continuation invitation!")
                    
                if i == 6:  # Should still answer about same product
                    if session.selected_product == "ShinyLocks 360":
                        print("✅ Context retained - still helping with ShinyLocks 360!")
                    else:
                        print("❌ Context lost - product selection changed unexpectedly")
                
                if i == 8:  # Should switch to HeatWave Mini
                    if session.selected_product == "HeatWave Mini":
                        print("✅ Successfully switched to HeatWave Mini!")
                    else:
                        print("❌ Product switch failed")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()
            
            print()
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

def test_product_switching():
    """Test that users can switch between products easily"""
    print("\n🧪 Testing Product Switching")
    print("=" * 40)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        # Setup customer
        bot.process_message("Hi", session)
        response, session = bot.process_message("henry.f@example.com", session)
        
        # Test switching scenarios
        switch_tests = [
            ("ShinyLocks 360", "ShinyLocks 360"),
            ("I want help with a different product", None),  # Should prompt for selection
            ("2", "HeatWave Mini"),  # Select by number
            ("StyleX Express", "StyleX Express"),  # Switch to another product
        ]
        
        for message, expected_product in switch_tests:
            print(f"\n📝 Testing: {message}")
            response, session = bot.process_message(message, session)
            
            actual_product = getattr(session, 'selected_product', None)
            print(f"Expected: {expected_product}, Got: {actual_product}")
            
            if actual_product == expected_product:
                print("✅ Product selection correct!")
            else:
                print("❌ Product selection mismatch!")
            
            print(f"Response: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Error in switching test: {e}")

def main():
    """Run the context retention tests"""
    print("🚀 Testing Improved Product Support Context")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Test context retention
    test_context_retention()
    
    # Test product switching
    test_product_switching()
    
    print("\n" + "=" * 80)
    print(f"⏰ Test completed at: {datetime.now()}")
    print("🏁 Test finished!")

if __name__ == "__main__":
    main()
