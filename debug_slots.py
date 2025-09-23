#!/usr/bin/env python3
"""
Debug slot retrieval to see what's happening with this week vs next week
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.chatbot.marketing_scheduler import MarketingScheduler
from datetime import datetime, timezone, timedelta
import pytz

def debug_slot_retrieval():
    """Debug what's happening with week calculation"""
    print("🔍 DEBUGGING SLOT RETRIEVAL")
    print("=" * 60)
    
    scheduler = MarketingScheduler(calendar_adapter=None)
    marketer_email = "nagakartheek.ds@gmail.com"
    
    # Use actual current time 
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    print(f"👤 Marketing Person: {marketer_email}")
    print(f"🕐 Current time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
    print(f"📅 Current day index: {current_time.weekday()} (Monday=0, Sunday=6)")
    print(f"🕐 Current hour: {current_time.hour}")
    print()
    
    # Test week offset logic
    week_offset = scheduler._choose_start_week_offset(current_time)
    print(f"🔢 Week offset chosen: {week_offset}")
    
    start_week = scheduler._week_start(current_time, week_offset)
    end_week = start_week + timedelta(days=7)
    
    print(f"📅 Start week: {start_week.strftime('%A, %B %d, %Y')}")
    print(f"📅 End week: {end_week.strftime('%A, %B %d, %Y')}")
    print()
    
    # Test both this week (offset=0) and next week (offset=1)
    print("🔍 TESTING THIS WEEK (offset=0):")
    print("-" * 40)
    
    this_week_start = scheduler._week_start(current_time, 0)
    this_week_end = this_week_start + timedelta(days=7)
    print(f"📅 This week range: {this_week_start.strftime('%A %m/%d')} to {this_week_end.strftime('%A %m/%d')}")
    
    slots_this_week = scheduler.suggest_slots(marketer_email, attempts=0, now=current_time)
    print(f"📊 Slots found this week: {len(slots_this_week)}")
    for i, (start, end) in enumerate(slots_this_week, 1):
        print(f"  {i}. {start.strftime('%A %m/%d at %H:%M')} - {end.strftime('%H:%M')}")
    
    print()
    print("🔍 TESTING WITH FORCED THIS WEEK:")
    print("-" * 40)
    
    # Force this week by setting time to earlier in the day
    morning_time = current_time.replace(hour=10, minute=0)  # 10 AM
    print(f"🕐 Forced time: {morning_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
    
    slots_forced = scheduler.suggest_slots(marketer_email, attempts=0, now=morning_time)
    print(f"📊 Slots found with morning time: {len(slots_forced)}")
    for i, (start, end) in enumerate(slots_forced, 1):
        print(f"  {i}. {start.strftime('%A %m/%d at %H:%M')} - {end.strftime('%H:%M')}")

if __name__ == "__main__":
    debug_slot_retrieval()
