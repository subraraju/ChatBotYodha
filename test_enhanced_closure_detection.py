"""Test the enhanced session closure detection for contextual scenarios."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_contextual_closure_detection():
    """Test the enhanced closure detection with contextual scenarios."""
    try:
        from app.chatbot.customer_service_bot import CustomerServiceBot
        
        print("🧪 Testing Enhanced Contextual Session Closure Detection\n")
        
        bot = CustomerServiceBot()
        
        # Test cases that should trigger closure (your specific scenario and similar)
        closure_test_cases = [
            # Your specific anxiety-inducing scenario
            "I am good, thank you very much",
            "I'm good, thank you very much", 
            "Im good, thanks so much",
            "All good, thank you",
            
            # Similar contextual patterns
            "Perfect, thank you!",
            "Great, thanks for the help",
            "Excellent, thank you so much",
            "Wonderful, I appreciate it",
            
            # Resolution-based patterns
            "Problem solved, thank you",
            "Issue resolved, thanks",
            "All resolved, thank you very much",
            "Everything is clear, thanks",
            
            # Satisfaction patterns
            "I have what I need, thank you",
            "That's what I needed, thanks",
            "Got what I needed, thank you very much",
            
            # Polite endings
            "Thank you very much",
            "Thanks so much",
            "Much appreciated",
            "Really appreciate it",
            "Thanks a lot",
            
            # Original strong closers (should still work)
            "Goodbye",
            "Bye",
            "That's all, thanks",
            "I'm done, thank you"
        ]
        
        # Test cases that should NOT trigger closure
        non_closure_test_cases = [
            # Continuation scenarios
            "I'm good, thank you, but can you help me with something else?",
            "Perfect, thank you, but what about shipping?",
            "Great, thanks, however I have another question",
            "Thank you very much, can you also tell me about returns?",
            "Thanks, but I need more information",
            "I appreciate it, but could you help me with warranty?",
            "Thank you, what about the warranty?",
            "Thanks, what's the next step?",
            
            # Regular conversation
            "Hello there",
            "Can you help me?",
            "What about the product features?",
            "How does shipping work?",
            "I need technical support"
        ]
        
        print("🔍 Testing CLOSURE scenarios (should detect session ending):")
        closure_detected = 0
        for i, test_case in enumerate(closure_test_cases, 1):
            is_closing = bot._detect_session_closing(test_case)
            status = "✅ DETECTED" if is_closing else "❌ MISSED"
            print(f"  {i:2d}. {status}: '{test_case}'")
            if is_closing:
                closure_detected += 1
        
        closure_rate = closure_detected / len(closure_test_cases)
        print(f"\n📊 Closure Detection Rate: {closure_detected}/{len(closure_test_cases)} = {closure_rate*100:.1f}%")
        
        print("\n🔍 Testing NON-CLOSURE scenarios (should continue conversation):")
        false_positives = 0
        for i, test_case in enumerate(non_closure_test_cases, 1):
            is_closing = bot._detect_session_closing(test_case)
            status = "❌ FALSE POSITIVE" if is_closing else "✅ CORRECT"
            print(f"  {i:2d}. {status}: '{test_case}'")
            if is_closing:
                false_positives += 1
        
        false_positive_rate = false_positives / len(non_closure_test_cases)
        print(f"\n📊 False Positive Rate: {false_positives}/{len(non_closure_test_cases)} = {false_positive_rate*100:.1f}%")
        
        # Performance assessment
        print(f"\n" + "="*60)
        print(f"📈 PERFORMANCE ASSESSMENT:")
        print(f"✅ Closure Detection Rate: {closure_rate*100:.1f}% (target: ≥85%)")
        print(f"✅ False Positive Rate: {false_positive_rate*100:.1f}% (target: ≤15%)")
        
        success = closure_rate >= 0.85 and false_positive_rate <= 0.15
        
        if success:
            print(f"\n🎉 ENHANCED DETECTION: EXCELLENT PERFORMANCE!")
            print(f"✅ Your specific anxiety scenario is now handled correctly")
            print(f"✅ Contextual understanding significantly improved")
        else:
            print(f"\n⚠️ ENHANCED DETECTION: Needs further tuning")
            if closure_rate < 0.85:
                print(f"   • Low closure detection rate")
            if false_positive_rate > 0.15:
                print(f"   • High false positive rate")
        
        # Specific test for your anxiety scenario
        print(f"\n" + "="*60)
        print(f"🎯 YOUR SPECIFIC ANXIETY SCENARIO TEST:")
        your_scenario = "I am good, thank you very much"
        is_detected = bot._detect_session_closing(your_scenario)
        
        if is_detected:
            print(f"✅ SUCCESS: '{your_scenario}' is now correctly detected as session closure!")
            print(f"🤖 The bot will now properly end the session instead of asking how to help")
        else:
            print(f"❌ FAILED: '{your_scenario}' is still not detected as closure")
        
        return success and is_detected
        
    except Exception as e:
        print(f"❌ Enhanced closure detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 ENHANCED CONTEXTUAL CLOSURE DETECTION TEST")
    print("🚀 Solving the 'anxious developer moments' problem!\n")
    
    success = test_contextual_closure_detection()
    
    if success:
        print(f"\n🎊 PROBLEM SOLVED!")
        print(f"✅ No more anxious moments with contextual misunderstandings")
        print(f"✅ The bot now understands satisfaction + gratitude = goodbye")
        print(f"✅ Enhanced detection maintains accuracy while being more contextually aware")
    else:
        print(f"\n🔧 Further tuning needed. Check the results above.")
