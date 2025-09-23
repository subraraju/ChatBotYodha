#!/usr/bin/env python3
"""
Correct slot retrieval logic based on actual calendar gaps
"""

import os
import sys
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional
import pytz

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from user_timezone_config import get_user_timezone_override

# Constants
BUSINESS_HOURS_START = int(os.getenv('BUSINESS_HOURS_START', '9'))
BUSINESS_HOURS_END = int(os.getenv('BUSINESS_HOURS_END', '17'))
MIN_SLOT_DURATION_HOURS = 1  # Configurable minimum gap
TARGET_SLOTS = 3  # Configurable target number of slots

class RealisticMarketingScheduler:
    def __init__(self):
        self.min_gap_hours = MIN_SLOT_DURATION_HOURS
        self.target_slots = TARGET_SLOTS
        
    def get_booked_slots(self, email: str, date: datetime.date, timezone_str: str) -> List[Tuple[datetime, datetime]]:
        """Get booked slots for a specific date - replace with real calendar integration"""
        # TODO: Replace with real Google Calendar API call
        # For now, mock some realistic bookings
        
        tz = pytz.timezone(timezone_str)
        
        # Mock realistic bookings based on the day
        mock_bookings = []
        
        if date.weekday() == 0:  # Monday
            # 10:00-11:00 and 14:00-15:30 booked
            mock_bookings = [
                (tz.localize(datetime.combine(date, time(10, 0))), 
                 tz.localize(datetime.combine(date, time(11, 0)))),
                (tz.localize(datetime.combine(date, time(14, 0))), 
                 tz.localize(datetime.combine(date, time(15, 30))))
            ]
        elif date.weekday() == 1:  # Tuesday  
            # 10:00-11:30 and 13:00-14:00 and 16:00-17:00 booked
            mock_bookings = [
                (tz.localize(datetime.combine(date, time(10, 0))), 
                 tz.localize(datetime.combine(date, time(11, 30)))),
                (tz.localize(datetime.combine(date, time(13, 0))), 
                 tz.localize(datetime.combine(date, time(14, 0)))),
                (tz.localize(datetime.combine(date, time(16, 0))), 
                 tz.localize(datetime.combine(date, time(17, 0))))
            ]
        elif date.weekday() == 2:  # Wednesday
            # 9:00-10:30, 11:00-12:00, 13:00-16:00 booked (very busy)
            mock_bookings = [
                (tz.localize(datetime.combine(date, time(9, 0))), 
                 tz.localize(datetime.combine(date, time(10, 30)))),
                (tz.localize(datetime.combine(date, time(11, 0))), 
                 tz.localize(datetime.combine(date, time(12, 0)))),
                (tz.localize(datetime.combine(date, time(13, 0))), 
                 tz.localize(datetime.combine(date, time(16, 0))))
            ]
        elif date.weekday() == 3:  # Thursday
            # 11:00-12:00 booked (light day)
            mock_bookings = [
                (tz.localize(datetime.combine(date, time(11, 0))), 
                 tz.localize(datetime.combine(date, time(12, 0))))
            ]
        elif date.weekday() == 4:  # Friday
            # 9:30-10:30, 15:00-16:00 booked
            mock_bookings = [
                (tz.localize(datetime.combine(date, time(9, 30))), 
                 tz.localize(datetime.combine(date, time(10, 30)))),
                (tz.localize(datetime.combine(date, time(15, 0))), 
                 tz.localize(datetime.combine(date, time(16, 0))))
            ]
            
        return sorted(mock_bookings, key=lambda x: x[0])  # Sort by start time
        
    def find_gaps_in_day(self, date: datetime.date, booked_slots: List[Tuple[datetime, datetime]], 
                         timezone_str: str, current_time: datetime) -> List[Tuple[datetime, datetime]]:
        """Find available gaps of min_gap_hours between booked slots"""
        
        tz = pytz.timezone(timezone_str)
        
        # Business hours boundaries
        day_start = tz.localize(datetime.combine(date, time(BUSINESS_HOURS_START, 0)))
        day_end = tz.localize(datetime.combine(date, time(BUSINESS_HOURS_END, 0)))
        
        available_gaps = []
        
        if not booked_slots:
            # Entire day is free
            available_gaps.append((day_start, day_end))
        else:
            # Check gap before first booking
            first_booking_start = booked_slots[0][0]
            if (first_booking_start - day_start).total_seconds() >= self.min_gap_hours * 3600:
                available_gaps.append((day_start, first_booking_start))
            
            # Check gaps between consecutive bookings
            for i in range(len(booked_slots) - 1):
                gap_start = booked_slots[i][1]  # End of current booking
                gap_end = booked_slots[i + 1][0]  # Start of next booking
                
                gap_duration = (gap_end - gap_start).total_seconds()
                if gap_duration >= self.min_gap_hours * 3600:
                    available_gaps.append((gap_start, gap_end))
            
            # Check gap after last booking
            last_booking_end = booked_slots[-1][1]
            if (day_end - last_booking_end).total_seconds() >= self.min_gap_hours * 3600:
                available_gaps.append((last_booking_end, day_end))
        
        # Filter out past slots and convert gaps to 1-hour slots
        available_slots = []
        for gap_start, gap_end in available_gaps:
            # Skip if gap starts in the past
            if gap_start <= current_time:
                # Adjust gap start to current time + buffer
                gap_start = max(gap_start, current_time + timedelta(minutes=30))
                
            # Create 1-hour slots within this gap
            slot_start = gap_start
            while slot_start + timedelta(hours=self.min_gap_hours) <= gap_end:
                slot_end = slot_start + timedelta(hours=self.min_gap_hours)
                if slot_end <= day_end:  # Don't exceed business hours
                    available_slots.append((slot_start, slot_end))
                slot_start += timedelta(hours=1)  # Next potential slot
                
        return available_slots
        
    def suggest_slots(self, marketer_email: str, week_offset: int = 0, 
                     now: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """
        Implement the correct logic:
        1. Get booked slots for each weekday
        2. Find gaps ≥1 hour between bookings
        3. First slot per unique day
        4. If <3 days, add more slots from earliest days
        5. If still <3, try next week
        """
        
        # Get timezone
        timezone_str = get_user_timezone_override(marketer_email) or "Asia/Kolkata"
        tz = pytz.timezone(timezone_str)
        
        current_time = now or datetime.now(tz)
        print(f"🌍 Using timezone: {timezone_str}")
        print(f"🕐 Current time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
        
        # Get the Monday of the target week
        monday = current_time - timedelta(days=current_time.weekday())
        target_monday = monday + timedelta(weeks=week_offset)
        
        print(f"🗓️  Checking week starting: {target_monday.strftime('%A, %B %d, %Y')}")
        print()
        
        # Step 1 & 2: Get available slots for each weekday
        daily_available_slots = {}
        
        for day_offset in range(5):  # Monday to Friday
            check_date = (target_monday + timedelta(days=day_offset)).date()
            day_name = check_date.strftime('%A')
            
            print(f"📅 {day_name} {check_date.strftime('%m/%d')}:")
            
            # Get booked slots for this day
            booked_slots = self.get_booked_slots(marketer_email, check_date, timezone_str)
            
            if booked_slots:
                print(f"   📋 Booked slots:")
                for start, end in booked_slots:
                    print(f"      🔒 {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            else:
                print(f"   📋 No bookings found")
            
            # Find available gaps
            available_slots = self.find_gaps_in_day(check_date, booked_slots, timezone_str, current_time)
            
            if available_slots:
                daily_available_slots[check_date] = available_slots
                print(f"   ✅ Available gaps:")
                for start, end in available_slots:
                    print(f"      🟢 {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            else:
                print(f"   ❌ No available gaps")
            print()
        
        if not daily_available_slots:
            print(f"❌ No available slots found for week of {target_monday.strftime('%B %d')}")
            if week_offset < 2:  # Step 6: Try next week
                print("🔄 Trying next week...")
                return self.suggest_slots(marketer_email, week_offset + 1, now)
            else:
                return []
        
        # Step 4: Get first slot per unique day
        suggested_slots = []
        for check_date in sorted(daily_available_slots.keys()):
            if daily_available_slots[check_date]:
                # Take the first available slot for this day
                first_slot = daily_available_slots[check_date][0]
                suggested_slots.append(first_slot)
        
        print(f"📊 Step 4 result: Found {len(suggested_slots)} unique days with slots")
        
        # Step 5: If less than target, add more slots from earliest days
        if len(suggested_slots) < self.target_slots:
            print(f"🔄 Need {self.target_slots - len(suggested_slots)} more slots...")
            
            for check_date in sorted(daily_available_slots.keys()):
                if len(suggested_slots) >= self.target_slots:
                    break
                    
                available_for_day = daily_available_slots[check_date]
                slots_already_from_day = len([s for s in suggested_slots 
                                            if s[0].date() == check_date])
                
                # Add remaining slots from this day
                for slot in available_for_day[slots_already_from_day:]:
                    if len(suggested_slots) >= self.target_slots:
                        break
                    suggested_slots.append(slot)
        
        # Sort by start time
        suggested_slots.sort(key=lambda x: x[0])
        
        print(f"✅ Final result: {len(suggested_slots)} slots selected")
        return suggested_slots[:self.target_slots]

def test_realistic_scheduler():
    """Test the realistic scheduler"""
    print("🧪 TESTING REALISTIC MARKETING SCHEDULER")
    print("=" * 60)
    
    scheduler = RealisticMarketingScheduler()
    marketer_email = "nagakartheek.ds@gmail.com"
    
    # Use current time 
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    slots = scheduler.suggest_slots(marketer_email, week_offset=0, now=current_time)
    
    print()
    print("📋 SUGGESTED SLOTS:")
    print("-" * 30)
    
    if not slots:
        print("❌ No slots available")
    else:
        for i, (start, end) in enumerate(slots, 1):
            day_name = start.strftime('%A')
            date_str = start.strftime('%B %d, %Y')
            time_str = start.strftime('%I:%M %p')
            end_time_str = end.strftime('%I:%M %p')
            
            print(f"{i}. {day_name}, {date_str}")
            print(f"   🕐 {time_str} - {end_time_str} IST")
            print()

if __name__ == "__main__":
    test_realistic_scheduler()
