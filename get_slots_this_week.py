#!/usr/bin/env python3
"""
Retrieve available marketing slots for this week
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.chatbot.marketing_scheduler import MarketingScheduler
from datetime import datetime, timezone
import pytz

def get_slots_this_week():
    """Retrieve available marketing slots for this week"""
    print("📅 Retrieving Available Marketing Slots This Week")
    print("=" * 60)
    
    # Initialize the scheduler
    scheduler = MarketingScheduler(calendar_adapter=None)  # Uses Mock for demo, but will try real calendar first
    marketer_email = "nagakartheek.ds@gmail.com"  # Real marketing team member in IST
    
    print(f"👤 Marketing Person: {marketer_email}")
    print(f"🌍 Expected Timezone: Asia/Kolkata (IST)")
    print()
    
    # Use actual current time 
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)  # Get actual current time in IST
    
    print(f"🕐 Current time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
    print(f"🔍 Searching for available slots for {marketer_email}...")
    print()
    
    # Get available slots
    slots = scheduler.suggest_slots(marketer_email, attempts=0, now=current_time)
    
    print()
    print("📋 Available Slots This Week:")
    print("-" * 40)
    
    if not slots:
        print("❌ No available slots found for this week.")
        print("💡 Try checking next week or contact the marketing team directly.")
        return []
    
    # Display the slots in a user-friendly format
    for i, (start, end) in enumerate(slots, 1):
        day_name = start.strftime('%A')
        date_str = start.strftime('%B %d, %Y')
        time_str = start.strftime('%I:%M %p')
        end_time_str = end.strftime('%I:%M %p')
        timezone_str = start.strftime('%Z')
        
        print(f"  {i}. {day_name}, {date_str}")
        print(f"     🕐 {time_str} - {end_time_str} {timezone_str}")
        print()
    
    print(f"📊 Total: {len(slots)} available slot{'s' if len(slots) != 1 else ''} found")
    print()
    print("💼 To book a slot, use the marketing chatbot or contact the team directly.")
    print("=" * 60)
    
    return slots

if __name__ == "__main__":
    available_slots = get_slots_this_week()
    
    # Also show raw data for debugging
    if available_slots:
        print()
        print("🔧 Debug Info:")
        for i, (start, end) in enumerate(available_slots, 1):
            print(f"  Slot {i}: {start} to {end}")
