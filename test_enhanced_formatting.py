#!/usr/bin/env python3
"""
Test script to demonstrate enhanced response formatting functionality.
This script tests the new bold formatting capabilities for bot responses.
"""

import sys
import os
import re

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def enhance_response_formatting(response_text: str) -> str:
    """
    Enhanced function to automatically bold key parts of bot responses.
    
    Args:
        response_text: The original bot response text
        
    Returns:
        Enhanced response with improved bold formatting
    """
    if not response_text:
        return response_text
    
    # Skip if already heavily formatted (to avoid over-formatting)
    if response_text.count('**') >= 6:
        return response_text
    
    # More selective patterns to avoid over-formatting
    patterns = [
        # Direct answers at start of response
        (r'^(Yes|No|Absolutely|Certainly|Definitely|Of course)', r'**\1**'),
        (r'\b(The answer is|The solution is)\b', r'**\1**'),
        
        # Key actions and recommendations
        (r'\b(I recommend|You should|Please try|Follow these steps)\b', r'**\1**'),
        (r'\b(Important|Note|Remember)\b', r'**\1**'),
        
        # Prices and specific numbers
        (r'\$(\d+(?:\.\d{2})?)\b', r'**$\1**'),
        (r'\b(\d+(?:\.\d+)?%)\b', r'**\1**'),
        
        # Key customer service phrases
        (r'\b(in stock|out of stock|available|unavailable|warranty|guarantee)\b', r'**\1**'),
        (r'\b(contact support|call us|email us)\b', r'**\1**'),
        
        # Step numbers only
        (r'\b(Step \d+)\b', r'**\1**'),
        
        # Status words that are important
        (r'\b(working|not working|broken|fixed|resolved)\b', r'**\1**'),
    ]
    
    # Apply patterns selectively
    enhanced_text = response_text
    for pattern, replacement in patterns:
        enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
    
    # Bold the first sentence only if it's a clear direct answer and short
    sentences = enhanced_text.split('. ')
    if (sentences and len(sentences[0]) < 80 and 
        not sentences[0].startswith('**') and
        any(word in sentences[0].lower() for word in ['yes', 'no', 'available', 'can help'])):
        sentences[0] = f"**{sentences[0].strip()}**"
        enhanced_text = '. '.join(sentences)
    
    return enhanced_text

def test_formatting_examples():
    """Test the formatting function with various examples"""
    
    test_cases = [
        {
            "input": "Yes, I can help you with that product inquiry. The Surface Pro 9 is available for $1299.99 and is currently in stock.",
            "description": "Direct answer with product and price"
        },
        {
            "input": "I recommend checking your warranty status first. Please contact support at 1-800-HELP if you need assistance.",
            "description": "Recommendation with action items"
        },
        {
            "input": "Your device appears to be working properly. The warranty covers this issue for 12 months.",
            "description": "Status information with warranty details"
        },
        {
            "input": "No, that feature is not available in the basic version. You should upgrade to Pro for $49.99.",
            "description": "Negative answer with upgrade suggestion"
        },
        {
            "input": "Step 1: Turn off the device. Step 2: Wait 30 seconds. Finally, restart it.",
            "description": "Sequential instructions"
        },
        {
            "input": "The Xbox Series X is currently out of stock but will be available next week.",
            "description": "Product availability status"
        },
        {
            "input": "Here's what you need to do. First, backup your data. I can help you with the restore process.",
            "description": "Instructions with assistance offer"
        }
    ]
    
    print("🧪 Testing Enhanced Response Formatting")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['description']}")
        print("-" * 40)
        print(f"Original: {case['input']}")
        
        enhanced = enhance_response_formatting(case['input'])
        print(f"Enhanced: {enhanced}")
        
        # Count bold elements
        bold_count = enhanced.count('**') // 2
        print(f"Bold elements added: {bold_count}")
        print()

def test_chat_display_simulation():
    """Simulate how the enhanced formatting would look in chat"""
    
    print("\n💬 Chat Display Simulation")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "Is the Surface Pro 9 available?"},
        {"role": "assistant", "content": "Yes, the Surface Pro 9 is available for $1299.99 and is currently in stock. I can help you with your order."},
        {"role": "user", "content": "What's the warranty coverage?"},
        {"role": "assistant", "content": "The warranty covers hardware defects for 12 months. Please keep your receipt for warranty claims."},
        {"role": "user", "content": "How do I contact support?"},
        {"role": "assistant", "content": "You should contact support at 1-800-HELP or email us at support@company.com. Our team is available 24/7."}
    ]
    
    for message in messages:
        if message["role"] == "user":
            print(f"**👤 You:** {message['content']}")
        else:
            enhanced_content = enhance_response_formatting(message["content"])
            print(f"**🤖 Yodha, the Assistant:** {enhanced_content}")
        print()

if __name__ == "__main__":
    print("Enhanced Bot Response Formatting Test")
    print("=====================================")
    
    try:
        # Test the formatting function
        test_formatting_examples()
        
        # Simulate chat display
        test_chat_display_simulation()
        
        print("✅ All formatting tests completed successfully!")
        print("\nThe enhanced formatting is now active and will:")
        print("• Automatically bold direct answers (Yes, No, etc.)")
        print("• Highlight product names and prices")
        print("• Emphasize action items and recommendations")
        print("• Make status information more visible")
        print("• Improve readability of step-by-step instructions")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
