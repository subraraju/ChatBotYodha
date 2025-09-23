#!/usr/bin/env python3
"""
Actual Working Marketing Request Patterns
Based on the current implementation in customer_service_bot.py
"""

def show_actual_marketing_patterns():
    """Show the exact patterns that currently work"""
    print("🎯 ACTUALLY WORKING Marketing Request Patterns")
    print("=" * 60)
    print("Based on the current code in _is_marketing_request():")
    print()
    
    # These are the actual regex patterns from the code
    working_patterns = [
        "connect to marketing",
        "contact marketing", 
        "speak to marketing",
        "talk to marketing",
        "schedule.*marketing",  # regex: schedule + anything + marketing
        "meeting with marketing",
        "connect me with marketing",
        "marketing person",
        "connect to the marketing",
        "speak with marketing", 
        "i want to schedule a meeting with marketing"
    ]
    
    print("✅ THESE PHRASES WILL WORK:")
    for i, pattern in enumerate(working_patterns, 1):
        if ".*" in pattern:
            print(f"{i:2d}. \"{pattern}\" (regex pattern)")
            print(f"     Examples: 'schedule a meeting with marketing'")
            print(f"               'schedule appointment with marketing'")
        else:
            print(f"{i:2d}. \"{pattern}\"")
    
    print("\n❌ THESE PHRASES WON'T WORK (from our demo):")
    failing_patterns = [
        "Can I book time with marketing?",
        "I need to meet with marketing", 
        "Can we discuss our marketing needs with someone from your team?",
        "I want to explore marketing opportunities",
        "We need marketing consultation",
        "Connect me with someone from marketing",
        "I'd like to chat with marketing",
        "Can I speak to a marketing representative?",
        "Put me in touch with marketing",
        "I need a marketing call this week",
        "Book me with marketing ASAP"
    ]
    
    for pattern in failing_patterns:
        print(f"   • {pattern}")
    
    print("\n💡 CONVERSION TIPS:")
    print("To make the failing patterns work, users should say:")
    print("   • 'talk to marketing' instead of 'meet with marketing'")  
    print("   • 'connect to marketing' instead of 'connect me with someone from marketing'")
    print("   • 'schedule meeting with marketing' instead of 'book time with marketing'")
    print("   • 'marketing person' for any marketing representative requests")

def show_successful_examples():
    """Show complete working examples"""
    print("\n\n💬 Complete Working Conversation Examples")
    print("=" * 60)
    
    examples = [
        {
            "title": "🎯 Example 1: Direct scheduling",
            "conversation": [
                "User: I want to schedule a meeting with marketing",
                "Bot: Sure — I can help schedule a meeting with marketing. Could you provide the marketing person's email address?",
                "User: john.marketing@company.com", 
                "Bot: I have the email address as **john.marketing@company.com**. Do you confirm this is the marketing person's email? (yes/no)",
                "User: yes",
                "Bot: I found the following available 1-hour slots...",
                "User: 2",
                "Bot: **Great! I've booked the meeting on Wednesday 2025-09-17 09:00.** Meeting id: MOCK-MEETING-john.marketing@company.com-..."
            ]
        },
        {
            "title": "🎯 Example 2: Talk to marketing",
            "conversation": [
                "User: I need to talk to marketing",
                "Bot: Sure — I can help schedule a meeting with marketing. Could you provide the marketing person's email address?",
                "User: sarah@company.com",
                "Bot: I have the email address as **sarah@company.com**. Do you confirm this is the marketing person's email? (yes/no)",
                "User: yes",
                "Bot: [Shows calendar slots...]"
            ]
        },
        {
            "title": "🎯 Example 3: Marketing person",
            "conversation": [
                "User: Connect me with a marketing person",
                "Bot: Sure — I can help schedule a meeting with marketing. Could you provide the marketing person's email address?",
                "User: mike@company.com",
                "Bot: [Continues with booking flow...]"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}")
        print("-" * 40)
        for line in example['conversation']:
            if line.startswith("User:"):
                print(f"👤 {line[5:].strip()}")
            else:
                print(f"🤖 {line[4:].strip()}")

if __name__ == "__main__":
    show_actual_marketing_patterns()
    show_successful_examples()
    
    print("\n" + "=" * 60)
    print("📝 SUMMARY: How Users Can Request Marketing Meetings")
    print("=" * 60)
    print("✅ WORKING phrases:")
    print("   • 'I want to schedule a meeting with marketing'")
    print("   • 'talk to marketing'") 
    print("   • 'speak to marketing'")
    print("   • 'connect to marketing'")
    print("   • 'marketing person'")
    print("   • 'schedule [anything] marketing'")
    print()
    print("🔄 The system then:")
    print("   1. Asks for marketing person's email")
    print("   2. Confirms the email address")
    print("   3. Shows 3 available time slots")
    print("   4. Books the selected slot")
    print("   5. Provides meeting confirmation")
