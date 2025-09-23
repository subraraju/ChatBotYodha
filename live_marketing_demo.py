#!/usr/bin/env python3
"""
Live Demo: Working Marketing Requests
Test the actual working patterns with real bot responses
"""
import sys
sys.path.append(".")

from app.chatbot.customer_service_bot import CustomerServiceBot, CustomerSession


def live_marketing_demo():
    """Live demo of working marketing request patterns"""
    print("🎬 LIVE MARKETING BOOKING DEMO")
    print("=" * 50)

    bot = CustomerServiceBot("TestCorp")
    
    # Demo the working patterns
    working_examples = [
        "I want to schedule a meeting with marketing",
        "talk to marketing", 
        "contact marketing",
        "speak to marketing",
        "schedule appointment with marketing",
        "meeting with marketing",
        "connect me with marketing",
        "marketing person",
    ]
    
    print("🎯 Testing Working Patterns:")
    print("-" * 30)
    
    for i, request in enumerate(working_examples, 1):
        session = CustomerSession(f"demo_{i}")
        print(f"\n{i}. 👤 \"{request}\"")
        
        response, _ = bot.process_message(request, session)
        if "schedule a meeting with marketing" in response.lower():
            print("   ✅ TRIGGERS MARKETING FLOW")
            print(f"   🤖 {response[:60]}...")
        else:
            print("   ❌ Does not trigger marketing")
            print(f"   🤖 {response[:60]}...")

def complete_booking_demo():
    """Demo a complete booking flow"""
    print("\n\n🎬 COMPLETE BOOKING FLOW DEMO")  
    print("=" * 50)
    
    bot = CustomerServiceBot("TestCorp")
    session = CustomerSession("complete_demo")
    
    # Step 1: Request marketing meeting
    print("\n📞 Step 1: Customer requests marketing meeting")
    response1, session = bot.process_message("I want to schedule a meeting with marketing", session)
    print("👤 Customer: I want to schedule a meeting with marketing")
    print(f"🤖 Bot: {response1}")
    
    # Step 2: Provide email
    print("\n📧 Step 2: Customer provides email")
    response2, session = bot.process_message("nagakartheek.ds@gmail.com", session)
    print("👤 Customer: nagakartheek.ds@gmail.com")
    print(f"🤖 Bot: {response2}")
    
    # Step 3: Confirm email
    print("\n✅ Step 3: Customer confirms email")
    response3, session = bot.process_message("yes", session)
    print("👤 Customer: yes")
    print(f"🤖 Bot: {response3}")
    
    # Step 4: Select time slot
    print("\n⏰ Step 4: Customer selects time slot")
    response4, session = bot.process_message("2", session)
    print("👤 Customer: 2")
    print(f"🤖 Bot: {response4}")
    
    print("\n🎉 BOOKING COMPLETE!")
    print("📊 Final State:", session.customer_state)
    if hasattr(session, 'marketing_flow'):
        mf = session.marketing_flow
        if mf and mf.get('booking'):
            booking = mf['booking']
            print(f"📅 Meeting Booked: {booking.get('start', 'N/A')}")
            print(f"🆔 Meeting ID: {booking.get('meeting_id', 'N/A')}")

def show_alternative_phrasings():
    """Show how to rephrase non-working requests"""
    print("\n\n💡 ALTERNATIVE PHRASINGS GUIDE")
    print("=" * 50)
    
    alternatives = [
        {
            "wrong": "Can I book time with marketing?",
            "right": "I want to schedule a meeting with marketing"
        },
        {
            "wrong": "I need to meet with marketing", 
            "right": "I need to talk to marketing"
        },
        {
            "wrong": "Connect me with someone from marketing",
            "right": "Connect me with marketing"
        },
        {
            "wrong": "Can I speak to a marketing representative?",
            "right": "Connect me with a marketing person"
        },
        {
            "wrong": "Book me with marketing ASAP",
            "right": "Schedule meeting with marketing"
        },
        {
            "wrong": "I need a marketing consultation",
            "right": "Schedule appointment with marketing"
        }
    ]
    
    for alt in alternatives:
        print(f"\n❌ Won't work: \"{alt['wrong']}\"")
        print(f"✅ Will work:  \"{alt['right']}\"")


if __name__ == "__main__":
    try:
        live_marketing_demo()
        complete_booking_demo() 
        show_alternative_phrasings()
        
        print("\n" + "=" * 50)
        print("📋 QUICK REFERENCE:")
        print("✅ Say: 'I want to schedule a meeting with marketing'")
        print("✅ Say: 'talk to marketing'") 
        print("✅ Say: 'marketing person'")
        print("✅ Say: 'schedule [anything] marketing'")
        print()
        print("Then provide the marketer's email when asked!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
