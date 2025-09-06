"""
Quick test for manufacturer contact fallback logic
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_manufacturer_fallback_logic():
    """Test the 2-attempt manufacturer contact logic"""
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("Testing manufacturer contact fallback logic...")
        
        # Setup
        bot.process_message("Hi", session)
        response, session = bot.process_message("henry.f@example.com", session)
        response, session = bot.process_message("ShinyLocks 360", session)
        
        print(f"Initial setup complete. Help attempts: {session.help_attempts}")
        
        # First failed attempt
        response, session = bot.process_message("How to fix the nuclear reactor?", session)
        print(f"After question 1 - Help attempts: {session.help_attempts}")
        print(f"Response length: {len(response)} chars")
        
        # Second failed attempt - should trigger manufacturer contact
        response, session = bot.process_message("How to launch into space?", session)
        print(f"After question 2 - Help attempts: {session.help_attempts}")
        print(f"Manufacturer contact triggered: {'manufacturer' in response.lower()}")
        print(f"Feel free message included: {'feel free' in response.lower()}")
        
        # Third question - should work normally again
        response, session = bot.process_message("What are the measurements?", session)
        print(f"After question 3 - Help attempts: {session.help_attempts}")
        print(f"Still helping with product: {session.selected_product}")
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manufacturer_fallback_logic()
