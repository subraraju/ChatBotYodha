"""
Test the manufacturer contact fallback functionality
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_manufacturer_fallback():
    """Test that the bot provides manufacturer contact when it can't answer questions"""
    print("🧪 Testing Manufacturer Contact Fallback")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ Bot initialized and session started")
        
        # Simulate the conversation flow leading to manufacturer fallback
        test_conversation = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "ShinyLocks 360",  # Select the product
            "How do I replace the internal circuit board?",  # Ask something not in the PDF
            "What is the warranty for the heating element?"  # Ask another question not in PDF
        ]
        
        for i, message in enumerate(test_conversation, 1):
            print(f"\n{'='*20} Message {i} {'='*20}")
            print(f"👤 User: {message}")
            
            try:
                response, updated_session = bot.process_message(message, session)
                session = updated_session
                
                print(f"🤖 Bot Response:")
                print(f"   {response}")
                print(f"📊 Current State: {session.customer_state.value}")
                
                if hasattr(session, 'selected_product') and session.selected_product:
                    print(f"🎯 Selected Product: {session.selected_product}")
                    print(f"🔄 Help Attempts: {session.help_attempts}")
                
                # Check if manufacturer contact info is provided
                if "manufacturer" in response.lower() and "contact" in response.lower():
                    print("✅ Manufacturer contact fallback triggered!")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()
            
            print()
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

def test_no_name_greeting():
    """Test that the bot doesn't give itself a name"""
    print("\n🧪 Testing No-Name Greeting")
    print("=" * 40)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        bot = CustomerServiceBot()
        
        # Test multiple greetings to ensure no names are used
        for i in range(3):
            session = bot.start_new_session()
            response, _ = bot.process_message("Hello", session)
            print(f"Greeting {i+1}: {response}")
            
            # Check for common names
            forbidden_names = ['sarah', 'emily', 'john', 'jane', 'mike', 'lisa', 'my name is', "i'm "]
            name_found = any(name.lower() in response.lower() for name in forbidden_names)
            
            if name_found:
                print("❌ WARNING: Name found in greeting!")
            else:
                print("✅ No name found in greeting")
        
    except Exception as e:
        print(f"❌ Error testing greetings: {e}")

def main():
    """Run the fallback tests"""
    print("🚀 Testing Manufacturer Contact Fallback & No-Name Greeting")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Test no-name greeting
    test_no_name_greeting()
    
    # Test manufacturer fallback
    test_manufacturer_fallback()
    
    print("\n" + "=" * 80)
    print(f"⏰ Test completed at: {datetime.now()}")
    print("🏁 Test finished!")

if __name__ == "__main__":
    main()
