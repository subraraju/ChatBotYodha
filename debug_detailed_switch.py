import sys
sys.path.append('app')
from chatbot.customer_service_bot import CustomerServiceBot
import re

def debug_explicit_switch_request(message):
    """Debug version of _is_explicit_product_switch_request with detailed output"""
    message_lower = message.lower().strip()
    print(f'\n=== Debugging: "{message}" ===')
    
    # Direct number references (1, 2, 3, etc.) - these are explicit
    number_patterns = [
        r'^\d+$',  # Just a number: "7"
        r'product\s+(\d+)',  # "product 7"
        r'number\s+(\d+)',   # "number 7"
        r'item\s+(\d+)',     # "item 7"
        r'(\d+)(?:st|nd|rd|th)',  # "7th", "1st", "2nd", "3rd"
    ]
    
    for pattern in number_patterns:
        if re.search(pattern, message_lower):
            print(f'✅ MATCH: Number pattern "{pattern}"')
            return True
    
    # Explicit switching phrases
    explicit_switch_phrases = [
        'switch to', 'change to', 'help with', 'ask about',
        'different product', 'other product', 'another product',
        'switch product', 'change product', 'different item',
        'instead of', 'rather than', 'not this', 'not that',
        'i have questions about', 'i have a question about',
        'can you help me with', 'what about', 'how about',
        'now i need help with', 'now about', 'next i want to ask about',
        'i also have', 'i also need help with', 'also about',
        'let me ask about', 'can i ask about', 'i want to ask about'
    ]
    
    # Check for explicit switching language
    for phrase in explicit_switch_phrases:
        if phrase in message_lower:
            print(f'✅ MATCH: Explicit phrase "{phrase}"')
            return True
    
    # Product name at the beginning of a sentence (likely explicit)
    # E.g., "Wireless Headphones Pro - how do I..."
    if re.match(r'^[A-Z][a-zA-Z\s]+\s*[-:]', message):
        print(f'✅ MATCH: Product name pattern (starts with capital)')
        return True
    
    # Check for explicit product names with clear context indicators
    context_indicators = [
        'about my', 'about the', 'regarding my', 'regarding the',
        'with my', 'with the', 'for my', 'for the',
        'my other', 'the other', 'instead'
    ]
    
    for indicator in context_indicators:
        if indicator in message_lower:
            print(f'✅ MATCH: Context indicator "{indicator}"')
            return True
    
    # Very short messages that are likely product names (but not questions)
    if (len(message.split()) <= 3 and len(message) > 5 and 
        not message_lower.startswith(('what', 'how', 'when', 'where', 'why', 'can', 'could', 'would', 'do', 'does'))):
        print(f'✅ MATCH: Short message pattern (not a question)')
        return True
    
    # Check for question transition patterns that indicate switching
    # Only match when followed by product-related words or "my"/"the"
    question_transition_patterns = [
        'what about my', 'what about the', 'how about my', 'how about the',
        'and what about my', 'and what about the', 'now what about my', 'now what about the',
        'can you tell me about my', 'can you tell me about the',
        'i need to know about my', 'i need to know about the'
    ]
    
    for pattern in question_transition_patterns:
        if pattern in message_lower:
            print(f'✅ MATCH: Question transition pattern "{pattern}"')
            return True
    
    # Check if the message starts with a question word followed by explicit product reference
    # This covers cases like "What about my Bluetooth Speaker?" but not "What is the warranty?"
    # Only match if they mention "my [product]" or "the [product]" in a switching context
    if re.match(r'^(what|how)\s+about\s+(my|the)\s+\w', message_lower):
        print(f'✅ MATCH: Question about product pattern')
        return True
    
    print('❌ NO MATCH: No explicit switching pattern detected')
    return False

# Test the problematic messages
test_messages = [
    'What is the warranty period?',
    'How do I charge this device?', 
    'What about my Bluetooth Speaker?',
    '2',
    'what about charging',
    "What's the length?"
]

print("Detailed debugging of switch detection:")
print("=" * 60)

for msg in test_messages:
    result = debug_explicit_switch_request(msg)
    print(f'Final result: {result}')
