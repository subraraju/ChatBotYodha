#!/usr/bin/env python3
"""
Debug the marketing scheduler slot detection
"""
import os
import sys
from datetime import datetime, timedelta, time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.chatbot.marketing_scheduler import MarketingScheduler, BUSINESS_HOURS_START, BUSINESS_HOURS_END

def debug_slot_detection():
    """Debug why no slots are being found"""
    print("🔍 Debugging Marketing Scheduler Slot Detection")
    print("=" * 60)
    
    scheduler = MarketingScheduler()
    marketer_email = "nagakartheek.ds@gmail.com"
    
    # Simulate the suggest_slots logic manually
    now = datetime.now()
    print(f"⏰ Current time: {now}")
    
    # Get the week being searched
    week_offset = scheduler._choose_start_week_offset(now) + 0  # attempts = 0
    start_week = scheduler._week_start(now, week_offset)
    end_week = start_week + timedelta(days=7)
    
    print(f"📅 Searching week: {start_week.date()} to {end_week.date()}")
    
    # Get busy times
    print(f"\n🔍 Getting busy times for {marketer_email}...")
    busy = scheduler.calendar.get_busy_times(marketer_email, start_week, end_week)
    
    print(f"⏰ Busy periods in search week:")
    for i, (bstart, bend) in enumerate(busy, 1):
        print(f"   {i}. {bstart.strftime('%a %m/%d %H:%M')} - {bend.strftime('%H:%M')}")
    
    # Check each day
    candidate_hours = list(range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
    print(f"\n📋 Candidate hours: {candidate_hours} (business hours {BUSINESS_HOURS_START}-{BUSINESS_HOURS_END})")
    
    suggested = []
    
    for day in range(0, 7):
        day_date = (start_week + timedelta(days=day)).date()
        weekday = day_date.weekday()
        day_name = day_date.strftime('%A')
        
        # Skip weekends
        if weekday >= 5:
            print(f"\n📅 {day_name} {day_date}: ⏩ SKIPPED (weekend)")
            continue
            
        print(f"\n📅 {day_name} {day_date}: 🔍 CHECKING")
        
        day_slots_found = 0
        for h in candidate_hours:
            slot_start = datetime.combine(day_date, time(h, 0))
            slot_end = slot_start + timedelta(hours=1)
            
            # Check if slot is in future
            if slot_start <= now:
                print(f"   {h:2d}:00-{h+1:2d}:00 ⏰ PAST (slot is {slot_start}, now is {now})")
                continue
            
            # Check conflicts
            conflict = False
            conflict_detail = ""
            for bstart, bend in busy:
                if slot_start < bend and slot_end > bstart:
                    conflict = True
                    conflict_detail = f"conflicts with {bstart.strftime('%m/%d %H:%M')}-{bend.strftime('%H:%M')}"
                    break
            
            if conflict:
                print(f"   {h:2d}:00-{h+1:2d}:00 ❌ BUSY ({conflict_detail})")
            else:
                # Check if we already have a slot for this day
                day_already_used = any(s[0].date() == slot_start.date() for s in suggested)
                if day_already_used:
                    print(f"   {h:2d}:00-{h+1:2d}:00 ✅ FREE but day already used")
                else:
                    suggested.append((slot_start, slot_end))
                    day_slots_found += 1
                    print(f"   {h:2d}:00-{h+1:2d}:00 ✅ AVAILABLE -> SELECTED")
                    
                    if len(suggested) >= 3:
                        break
        
        print(f"   📊 Day summary: {day_slots_found} slots found")
        if len(suggested) >= 3:
            break
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total slots found: {len(suggested)}")
    
    if suggested:
        print(f"   ✅ Available slots:")
        for i, (start, end) in enumerate(suggested, 1):
            print(f"     {i}. {start.strftime('%a %m/%d %H:%M')} - {end.strftime('%H:%M')}")
    else:
        print(f"   ❌ No available slots found")
        print(f"\n💡 Possible reasons:")
        print(f"   • All business hours slots are busy")
        print(f"   • All future slots are in the past relative to current time")
        print(f"   • Calendar API returned incorrect busy times")

def test_time_calculations():
    """Test the time calculation logic"""
    print(f"\n\n⚙️ Testing Time Calculation Logic")
    print("=" * 50)
    
    now = datetime.now()
    scheduler = MarketingScheduler()
    
    # Test week offset calculation
    week_offset = scheduler._choose_start_week_offset(now)
    print(f"📅 Current weekday: {now.strftime('%A')} (weekday={now.weekday()})")
    print(f"📅 Week offset chosen: {week_offset}")
    
    # Test week start calculation
    start_week = scheduler._week_start(now, week_offset)
    print(f"📅 Week start: {start_week}")
    
    # Test some candidate times
    print(f"\n⏰ Sample future business hour slots:")
    candidate_hours = [9, 10, 11, 14, 15, 16]  # Sample hours
    
    for days_ahead in range(1, 8):  # Next 7 days
        test_date = (now + timedelta(days=days_ahead)).date()
        if test_date.weekday() >= 5:  # Skip weekends
            continue
            
        for hour in candidate_hours[:2]:  # Just show first 2 hours per day
            slot_time = datetime.combine(test_date, time(hour, 0))
            is_future = slot_time > now
            status = "✅ FUTURE" if is_future else "❌ PAST"
            
            print(f"   {slot_time.strftime('%a %m/%d %H:%M')}: {status}")
            
            if is_future:
                break  # Found one future slot for this day

if __name__ == "__main__":
    debug_slot_detection()
    test_time_calculations()
