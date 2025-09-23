import sys
sys.path.append('app')
from chatbot.customer_service_bot import CustomerServiceBot

bot = CustomerServiceBot()

# Test the problematic messages
test_messages = [
    'What is the warranty period?',
    'How do I charge this device?',
    'What about my Bluetooth Speaker?',
    '2',
    'what about charging',
    'What\'s the length?'
]

print("Testing _is_explicit_product_switch_request function:")
print("=" * 50)

for msg in test_messages:
    result = bot._is_explicit_product_switch_request(msg)
    print(f'Message: "{msg}"')
    print(f'Explicit switch: {result}')
    print()
