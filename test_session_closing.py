#!/usr/bin/env python3
"""
Test script to verify session closing detection functionality.
This script tests various ways users might indicate they want to close the session.
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from chatbot.customer_service_bot import CustomerServiceBot, CustomerSession, CustomerState
from models.pydantic_models import ChatMessage

def test_session_closing_detection():
    """Test the session closing detection with various messages"""
    
    # Initialize the bot
    bot = CustomerServiceBot("Test Company")
    
    # Test cases for session closing detection
    test_cases = [
        # Explicit closures
        {"message": "goodbye", "should_close": True, "description": "Simple goodbye"},
        {"message": "bye", "should_close": True, "description": "Simple bye"},
        {"message": "thanks, bye", "should_close": True, "description": "Thanks and bye"},
        
        # "I'm good" patterns
        {"message": "I'm good", "should_close": True, "description": "I'm good"},
        {"message": "Im good", "should_close": True, "description": "Im good (no apostrophe)"},
        {"message": "I am good", "should_close": True, "description": "I am good"},
        {"message": "All good", "should_close": True, "description": "All good"},
        {"message": "I'm all set", "should_close": True, "description": "I'm all set"},
        
        # Contextual patterns with gratitude
        {"message": "I'm good, thanks", "should_close": True, "description": "I'm good with thanks"},
        {"message": "All good, thank you", "should_close": True, "description": "All good with thank you"},
        {"message": "Perfect, thanks", "should_close": True, "description": "Perfect with thanks"},
        {"message": "Great, thank you", "should_close": True, "description": "Great with thank you"},
        
        # Should NOT close
        {"message": "I'm good at programming", "should_close": False, "description": "I'm good at (something) - should not close"},
        {"message": "Good morning", "should_close": False, "description": "Good morning - should not close"},
        {"message": "That's good to know", "should_close": False, "description": "That's good to know - should not close"},
        {"message": "I'm good, but can you help with something else?", "should_close": False, "description": "I'm good but asking for more help"},
        
        # Polite endings
        {"message": "Thank you very much", "should_close": True, "description": "Thank you very much"},
        {"message": "Thanks so much", "should_close": True, "description": "Thanks so much"},
        {"message": "Much appreciated", "should_close": True, "description": "Much appreciated"},
        
        # Edge cases
        {"message": "That's all", "should_close": True, "description": "That's all"},
        {"message": "I'm done", "should_close": True, "description": "I'm done"},
        {"message": "All set", "should_close": True, "description": "All set"},
    ]
    
    print("🧪 Testing Session Closing Detection")
    print("=" * 60)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        message = case["message"]
        expected = case["should_close"]
        description = case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Message: '{message}'")
        print(f"Expected to close: {expected}")
        
        # Test the detection
        actual = bot._detect_session_closing(message)
        print(f"Actual result: {actual}")
        
        # Check if correct
        is_correct = actual == expected
        print(f"Result: {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        
        if is_correct:
            correct_predictions += 1
        
        print("-" * 40)
    
    accuracy = (correct_predictions / total_tests) * 100
    print(f"\n📊 Test Results:")
    print(f"Correct predictions: {correct_predictions}/{total_tests}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("✅ Session closing detection is working well!")
    elif accuracy >= 70:
        print("⚠️ Session closing detection needs some improvement")
    else:
        print("❌ Session closing detection needs significant improvement")

def test_full_session_flow():
    """Test the complete session flow with closing"""
    
    print("\n💬 Testing Full Session Flow with Closing")
    print("=" * 60)
    
    # Initialize bot and session
    bot = CustomerServiceBot("Test Company")
    session = CustomerSession(
        session_id="test-session-001"
    )
    session.customer_id = 1
    session.customer_state = CustomerState.IDENTIFIED  # Use correct state name
    session.created_at = datetime.now()
    session.updated_at = datetime.now()
    session.messages = []
    
    # Simulate a conversation
    test_conversation = [
        "Hello, I need help with my order",
        "What's the status of order #12345?",
        "I'm good, thanks!"  # This should trigger session closure
    ]
    
    for i, user_message in enumerate(test_conversation, 1):
        print(f"\nStep {i}: User says: '{user_message}'")
        
        # Process the message
        bot_response, updated_session = bot.process_message(user_message, session)
        
        print(f"Bot response: '{bot_response}'")
        print(f"Session state: {updated_session.customer_state}")
        print(f"Messages in session: {len(updated_session.messages)}")
        
        # Update session for next iteration
        session = updated_session
        
        # If session was closed, break
        if updated_session.customer_state == CustomerState.UNKNOWN:
            print("🔚 Session was closed!")
            break
    
    print(f"\nFinal session state: {session.customer_state}")
    print(f"Total messages: {len(session.messages)}")

if __name__ == "__main__":
    print("Session Closing Detection Test")
    print("==============================")
    
    try:
        # Test the detection logic
        test_session_closing_detection()
        
        # Test the full flow
        test_full_session_flow()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
