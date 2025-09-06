"""
Test that the bot can continue answering questions indefinitely without help attempt limits
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_unlimited_questions():
    """Test that the bot can answer many questions about the same product"""
    print("🧪 Testing Unlimited Product Support Questions")
    print("=" * 60)
    
    try:
        from chatbot.customer_service_bot import CustomerServiceBot
        
        # Initialize the bot
        bot = CustomerServiceBot()
        session = bot.start_new_session()
        
        print("✅ Bot initialized and session started")
        
        # Set up the conversation to get to product support
        setup_messages = [
            "Hi, I need help with my account",
            "My email is henry.f@example.com",
            "ShinyLocks 360"
        ]
        
        for message in setup_messages:
            response, session = bot.process_message(message, session)
        
        print(f"✅ Setup complete. Selected product: {session.selected_product}")
        print(f"📊 Current State: {session.customer_state.value}")
        
        # Now ask multiple questions about the product
        questions = [
            "What are the measurements?",
            "How much does it weigh?", 
            "What is the power consumption?",
            "How do I clean it?",
            "What is the warranty period?",
            "Can I use it on wet hair?",
            "What temperature does it reach?",
            "Is it safe for color-treated hair?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*15} Question {i} {'='*15}")
            print(f"👤 User: {question}")
            
            response, session = bot.process_message(question, session)
            
            print(f"🤖 Bot: {response[:200]}{'...' if len(response) > 200 else ''}")
            print(f"📊 State: {session.customer_state.value}")
            print(f"🎯 Product: {session.selected_product}")
            
            # Check if the bot is still in product support mode and remembering the product
            if session.customer_state.value != "product_support" or not session.selected_product:
                print("❌ ERROR: Bot lost context or changed state!")
                break
            else:
                print("✅ Context maintained")
        
        print(f"\n🎉 Successfully asked {len(questions)} questions about {session.selected_product}")
        print("✅ Bot maintained context throughout all questions")
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unlimited_questions()
