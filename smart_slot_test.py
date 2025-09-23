#!/usr/bin/env python3
"""
Smart Slot Scheduling Implementation
"""
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional
import pytz


def smart_suggest_slots(calendar, marketer_email: str, attempts: int = 0, now: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
    """
    Smart slot suggestion with prioritization:
    1. First try to find 3+ slots on different days (preferred)
    2. If not enough different days, allow multiple slots per day
    3. If still not enough, try next week
    """
    BUSINESS_HOURS_START = 9
    BUSINESS_HOURS_END = 17
    
    # Get marketer's timezone first
    marketer_timezone = calendar.get_user_timezone(marketer_email)
    print(f"🌍 Using timezone for {marketer_email}: {marketer_timezone}")
    
    # Create timezone-aware datetime objects
    marketer_tz = pytz.timezone(marketer_timezone)
    
    now = now or datetime.now()
    # Make now timezone-aware if it's not already
    if now.tzinfo is None:
        now = marketer_tz.localize(now)
    else:
        now = now.astimezone(marketer_tz)
        
    # Calculate week
    def _choose_start_week_offset(now_dt):
        # If today is in start_next_week_days, start with next week (offset 1), else this week (0)
        if now_dt.weekday() in [3, 4, 5, 6]:  # Thu, Fri, Sat, Sun
            return 1
        return 0
        
    def _week_start(base_date, week_offset=0):
        monday = base_date - timedelta(days=base_date.weekday())
        result = (monday + timedelta(weeks=week_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        return result
        
    week_offset = _choose_start_week_offset(now) + attempts
    start_week = _week_start(now, week_offset)
    end_week = start_week + timedelta(days=7)

    # Search business hours only: 9 AM to 4 PM (so 1-hour slots end by 5 PM)
    candidate_hours = list(range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
    print(f"📋 Smart strategy: Searching for slots between {BUSINESS_HOURS_START}:00 AM and {BUSINESS_HOURS_END}:00 PM")
    
    # Get busy times once
    busy = calendar.get_busy_times(marketer_email, start_week, end_week)
    
    # PHASE 1: Try to get one slot per day (preferred)
    print("🎯 Phase 1: Looking for one slot per different day (preferred)")
    suggested_different_days = []
    days_with_slots = set()
    
    for day in range(0, 7):
        day_date = (start_week + timedelta(days=day)).date()
        
        # Skip weekends (Saturday=5, Sunday=6)  
        if day_date.weekday() >= 5:
            continue
        
        day_name = day_date.strftime('%A')
        print(f"   🔍 Checking {day_name}...")
        
        # Try to find one good slot for this day
        found_slot_for_day = False
        for h in candidate_hours:
            if found_slot_for_day:
                break
                
            # Create timezone-aware datetime objects in marketer's timezone
            naive_slot_start = datetime.combine(day_date, time(h, 0))
            slot_start = marketer_tz.localize(naive_slot_start)
            slot_end = slot_start + timedelta(hours=1)
            
            # Ensure both times are in the same timezone for proper comparison
            now_in_marketer_tz = now.astimezone(marketer_tz) if now.tzinfo else marketer_tz.localize(now)
            
            # ensure slot is in future (with timezone-aware comparison)
            if slot_start <= now_in_marketer_tz:
                continue
                
            # check conflicts
            conflict = False
            for bstart, bend in busy:
                if slot_start < bend and slot_end > bstart:
                    conflict = True
                    break
                    
            if not conflict:
                suggested_different_days.append((slot_start, slot_end))
                days_with_slots.add(day_date)
                print(f"   ✅ {day_name}: Found slot at {slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}")
                found_slot_for_day = True
                
        if not found_slot_for_day:
            print(f"   ❌ {day_name}: No available slots")
    
    print(f"📊 Phase 1 Result: Found {len(suggested_different_days)} slots on different days")
    
    # PHASE 2: If we don't have enough different days, add more slots from available days
    suggested = suggested_different_days.copy()
    max_total_slots = 6
    
    if len(suggested) < 3:
        print(f"🔄 Phase 2: Only {len(suggested)} different days available, looking for additional slots on same days...")
        
        for day in range(0, 7):
            if len(suggested) >= max_total_slots:
                break
                
            day_date = (start_week + timedelta(days=day)).date()
            
            # Skip weekends
            if day_date.weekday() >= 5:
                continue
            
            day_name = day_date.strftime('%A')
            daily_slots_added = 0
            
            for h in candidate_hours:
                if len(suggested) >= max_total_slots:
                    break
                
                # Create timezone-aware datetime objects
                naive_slot_start = datetime.combine(day_date, time(h, 0))
                slot_start = marketer_tz.localize(naive_slot_start)
                slot_end = slot_start + timedelta(hours=1)
                
                # Skip if already in suggested list
                if any(existing[0] == slot_start for existing in suggested):
                    continue
                
                # Ensure both times are in the same timezone for proper comparison
                now_in_marketer_tz = now.astimezone(marketer_tz) if now.tzinfo else marketer_tz.localize(now)
                
                # ensure slot is in future
                if slot_start <= now_in_marketer_tz:
                    continue
                    
                # check conflicts
                conflict = False
                for bstart, bend in busy:
                    if slot_start < bend and slot_end > bstart:
                        conflict = True
                        break
                        
                if not conflict:
                    suggested.append((slot_start, slot_end))
                    daily_slots_added += 1
                    print(f"   ➕ {day_name}: Added additional slot at {slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}")
            
            if daily_slots_added > 0:
                total_for_day = daily_slots_added + (1 if day_date in days_with_slots else 0)
                print(f"   📅 {day_name}: {total_for_day} total slot(s)")
    
    # Sort by start time
    suggested.sort(key=lambda x: x[0])
    
    print(f"📊 Final result: Found {len(suggested)} available slots")
    
    # If we didn't find enough slots and attempts < 2, suggest trying next week
    if len(suggested) < 3 and attempts < 2:
        print(f"⚠️ Only found {len(suggested)} slots this week, may need to check next week")
        
    return suggested


if __name__ == "__main__":
    print("🧠 Testing Smart Slot Strategy Implementation")
    print("=" * 60)
    
    import sys
    sys.path.append(".")
    
    try:
        from google_calendar_integration import GoogleCalendarAdapter
        
        calendar = GoogleCalendarAdapter()
        marketer_email = "nagakartheek.ds@gmail.com"
        
        slots = smart_suggest_slots(calendar, marketer_email, attempts=0)
        
        if slots:
            print(f"\n📊 Result: Found {len(slots)} slots")
            
            # Analyze the distribution
            days_with_slots = {}
            for i, (start, end) in enumerate(slots):
                day_key = start.strftime('%A %Y-%m-%d')
                if day_key not in days_with_slots:
                    days_with_slots[day_key] = []
                days_with_slots[day_key].append((start, end))
                print(f"   {i+1}. {start.strftime('%A %B %d at %H:%M')} - {end.strftime('%H:%M')} IST")
            
            print(f"\n📈 Distribution Analysis:")
            unique_days = len(days_with_slots)
            print(f"   • {unique_days} different days")
            
            for day, day_slots in days_with_slots.items():
                print(f"   • {day}: {len(day_slots)} slot(s)")
            
            if unique_days >= 3:
                print("   ✅ SUCCESS: Found slots on 3+ different days (optimal)")
            elif unique_days >= 2:
                print("   ⚠️ PARTIAL: Found slots on 2 different days (acceptable)")  
            else:
                print("   ❌ SUBOPTIMAL: All slots on same day (fallback scenario)")
                
        else:
            print("❌ No slots found")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
