"""Test script for complex cross-range product switching functionality."""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_database
from app.chatbot.customer_service_bot import CustomerServiceBot
from app.chatbot.agent import CustomerSession

def test_cross_range_switching():
    """Test the complex cross-range product switching scenarios."""
    
    # Create bot instance
    bot = CustomerServiceBot()
    
    # Get database session
    db = next(get_database())
    
    try:
        # Create a test user session
        user_session = CustomerSession(
            session_id="test_user_cross_range",
            customer_id=1,  # Assuming customer 1 exists
            conversation_history=[],
            state="GREETING",
            displayed_purchases=[],
            all_purchases=[],
            has_more_purchases=False,
            selected_product=None
        )
        
        print("=== Testing Cross-Range Product Switching ===\n")
        
        # Step 1: Show initial purchases
        print("1. User: I need help with my recent purchase")
        response, user_session = bot.process_message("I need help with my recent purchase", user_session)
        print(f"Bot: {response}\n")
        
        # Step 2: User says "it's not in this list" to trigger auto-pagination
        print("2. User: It's not in this list")
        response, user_session = bot.process_message("It's not in this list", user_session)
        print(f"Bot: {response}\n")
        
        # Step 3: User selects a product from 6-10 range
        print("3. User: Tell me about product 7")
        response, user_session = bot.process_message("Tell me about product 7", user_session)
        print(f"Bot: {response}\n")
        
        # Step 4: User asks a question about the selected product
        print("4. User: What's the warranty on this?")
        response, user_session = bot.process_message("What's the warranty on this?", user_session)
        print(f"Bot: {response}\n")
        
        # Step 5: Now user wants to ask about a different product from the earlier list (1-5)
        print("5. User: Actually, I want to ask about a different product from earlier")
        response, user_session = bot.process_message("Actually, I want to ask about a different product from earlier", user_session)
        print(f"Bot: {response}\n")
        
        # Step 6: User selects a product from 1-5 range
        print("6. User: Tell me about product 2")
        response, user_session = bot.process_message("Tell me about product 2", user_session)
        print(f"Bot: {response}\n")
        
        # Step 7: Test explicit range switching
        print("7. User: show 6-10")
        response, user_session = bot.process_message("show 6-10", user_session)
        print(f"Bot: {response}\n")
        
        # Step 8: Test beyond-range request
        print("8. User: Tell me about product 15")
        response, user_session = bot.process_message("Tell me about product 15", user_session)
        print(f"Bot: {response}\n")
        
        print("=== Cross-Range Product Switching Test Complete ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_cross_range_switching()
