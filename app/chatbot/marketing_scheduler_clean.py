#!/usr/bin/env python3
"""
Marketing Scheduler - Clean Version
Handles scheduling meetings with marketing team members using smart slot distribution
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

# Constants from environment or defaults
BUSINESS_HOURS_START = int(os.getenv('BUSINESS_HOURS_START', '9'))
BUSINESS_HOURS_END = int(os.getenv('BUSINESS_HOURS_END', '17'))
START_NEXT_WEEK_DAYS = os.getenv('START_NEXT_WEEK_DAYS', '1,2,3')  # Mon, Tue, Wed
MAX_ATTEMPTS = int(os.getenv('MAX_SCHEDULING_ATTEMPTS', '2'))

class CalendarAdapter:
    """Abstract base for calendar integrations"""
    
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        raise NotImplementedError
        
    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        raise NotImplementedError
        
    def get_user_timezone(self, email: str) -> str:
        return "Asia/Kolkata"  # Default

class MockCalendarAdapter(CalendarAdapter):
    """Mock implementation for testing"""
    
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        # Mock some busy times - assume 13:00-14:00 on Tuesday is busy
        # and 10:00-11:00 and 11:00-12:00 on Wednesday are busy
        mock_busy = []
        
        # Tuesday 13:00-14:00 busy
        tuesday = start + timedelta(days=1)  # Assuming start is Monday
        if tuesday.date() <= end.date():
            busy_start = datetime.combine(tuesday.date(), time(13, 0))
            busy_end = datetime.combine(tuesday.date(), time(14, 0))
            
            # Make timezone-aware
            tz = pytz.timezone('Asia/Kolkata')
            busy_start = tz.localize(busy_start)
            busy_end = tz.localize(busy_end)
            mock_busy.append((busy_start, busy_end))
        
        # Wednesday 10:00-12:00 busy
        wednesday = start + timedelta(days=2)  # Assuming start is Monday
        if wednesday.date() <= end.date():
            busy_start1 = datetime.combine(wednesday.date(), time(10, 0))
            busy_end1 = datetime.combine(wednesday.date(), time(11, 0))
            busy_start2 = datetime.combine(wednesday.date(), time(11, 0))
            busy_end2 = datetime.combine(wednesday.date(), time(12, 0))
            
            # Make timezone-aware
            tz = pytz.timezone('Asia/Kolkata')
            busy_start1 = tz.localize(busy_start1)
            busy_end1 = tz.localize(busy_end1)
            busy_start2 = tz.localize(busy_start2)
            busy_end2 = tz.localize(busy_end2)
            mock_busy.extend([(busy_start1, busy_end1), (busy_start2, busy_end2)])
        
        return mock_busy
        
    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        print(f"📧 Mock: Booked meeting '{subject}' from {start} to {end} for {email}")
        return f"mock-event-{datetime.now().timestamp()}"
        
    def get_user_timezone(self, email: str) -> str:
        return get_user_timezone_override(email) or "Asia/Kolkata"

class MarketingScheduler:
    def __init__(self, calendar_adapter: Optional[CalendarAdapter] = None, max_attempts: int = MAX_ATTEMPTS):
        # Initialize calendar adapter
        if calendar_adapter:
            self.calendar = calendar_adapter
        else:
            # Try to use real calendar integration if available
            try:
                from app.api.teams import EnhancedGoogleCalendarAdapter
                from app.api.google_calendar_integration import GoogleCalendarAdapter
                
                # First try Google Calendar
                google_adapter = GoogleCalendarAdapter()
                if hasattr(google_adapter, 'service') and google_adapter.service:
                    self.calendar = EnhancedGoogleCalendarAdapter(google_adapter)
                    print("✅ Using Google Calendar + Teams integration")
                else:
                    raise Exception("Google Calendar not available")
                    
            except Exception as e:
                print(f"⚠️ Failed to initialize real calendar, using mock: {e}")
                self.calendar = MockCalendarAdapter()
        
        self.max_attempts = max_attempts
        self.start_next_week_days = [int(x) for x in START_NEXT_WEEK_DAYS.split(",") if x.strip().isdigit()]

    def _week_start(self, base_date: datetime, week_offset: int = 0) -> datetime:
        # Return Monday of the week for base_date + week_offset weeks
        # Preserve timezone information
        monday = base_date - timedelta(days=base_date.weekday())
        result = (monday + timedelta(weeks=week_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # If the original base_date was timezone-aware, keep the same timezone
        if base_date.tzinfo is not None:
            # Replace just changes the time components, keeping the timezone
            return result
        else:
            return result

    def _choose_start_week_offset(self, now: datetime) -> int:
        # If it's past Wednesday or it's late in the day, start from next week
        current_day = now.weekday()  # Monday=0, Sunday=6
        current_hour = now.hour
        
        if current_day >= 2 or (current_day >= 1 and current_hour >= 16):  # Wed+ or Tue after 4pm
            return 1  # Start from next week
        else:
            return 0  # Start from this week

    def suggest_slots(self, marketer_email: str, attempts: int = 0, now: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """
        Suggest available meeting slots using smart distribution strategy
        Prioritizes different days first, then limits to 3 total slots for better UX
        """
        print(f"🌍 Smart strategy: Searching for slots between {BUSINESS_HOURS_START}:00 AM and {BUSINESS_HOURS_END}:00 PM")
        
        # Get marketer's timezone first
        marketer_timezone = self.calendar.get_user_timezone(marketer_email)
        print(f"🌍 Using timezone for {marketer_email}: {marketer_timezone}")
        
        # Create timezone-aware datetime objects
        marketer_tz = pytz.timezone(marketer_timezone)
        
        now = now or datetime.now()
        # Make now timezone-aware if it's not already
        if now.tzinfo is None:
            now = marketer_tz.localize(now)
        else:
            now = now.astimezone(marketer_tz)
            
        week_offset = self._choose_start_week_offset(now) + attempts
        start_week = self._week_start(now, week_offset)
        end_week = start_week + timedelta(days=7)

        # Search business hours only: 9 AM to 5 PM (so 1-hour slots end by 5 PM)
        candidate_hours = list(range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
        
        # Get busy times once
        busy = self.calendar.get_busy_times(marketer_email, start_week, end_week)
        
        # PHASE 1: Find one slot per different day (preferred)
        print(f"🎯 Phase 1: Looking for one slot per different day (preferred)")
        suggested_different_days = []
        days_with_slots = set()

        for day in range(0, 7):
            if len(suggested_different_days) >= 4:  # Find max 4 different days initially
                break
                
            day_date = (start_week + timedelta(days=day)).date()
            
            # Skip weekends (Saturday=5, Sunday=6)
            if day_date.weekday() >= 5:
                continue
                
            day_name = day_date.strftime('%A')
            print(f"   🔍 Checking {day_name}...")
            found_slot_for_day = False
            
            # Look for just ONE slot per day in Phase 1
            for h in candidate_hours:
                # Create timezone-aware datetime objects in marketer's timezone
                naive_slot_start = datetime.combine(day_date, time(h, 0))
                slot_start = marketer_tz.localize(naive_slot_start)
                slot_end = slot_start + timedelta(hours=1)
                
                # Ensure both times are in the same timezone for proper comparison
                now_in_marketer_tz = now.astimezone(marketer_tz) if now.tzinfo else marketer_tz.localize(now)
                
                # Ensure slot is in future
                if slot_start <= now_in_marketer_tz:
                    continue
                    
                # Check conflicts
                conflict = False
                for bstart, bend in busy:
                    # Ensure busy times are also timezone-aware for comparison
                    if bstart.tzinfo is None:
                        bstart = marketer_tz.localize(bstart)
                    if bend.tzinfo is None:
                        bend = marketer_tz.localize(bend)
                        
                    if slot_start < bend and slot_end > bstart:
                        conflict = True
                        break
                        
                if not conflict:
                    suggested_different_days.append((slot_start, slot_end))
                    days_with_slots.add(day_date)
                    print(f"   ✅ {day_name}: Found slot at {slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}")
                    found_slot_for_day = True
                    break  # Only take first available slot for this day in Phase 1
                    
            if not found_slot_for_day:
                print(f"   ❌ {day_name}: No available slots")
        
        print(f"📊 Phase 1 Result: Found {len(suggested_different_days)} slots on different days")
        
        # Limit to exactly 3 slots for better user experience
        max_total_slots = 3
        suggested = suggested_different_days[:max_total_slots]
        
        print(f"📊 Final result: Found {len(suggested)} available slots during business hours ({BUSINESS_HOURS_START}:00 AM - {BUSINESS_HOURS_END}:00 PM)")
        
        # Sort by start time
        suggested.sort(key=lambda x: x[0])
        
        return suggested

    def book_slot(self, marketer_email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        return self.calendar.book_meeting(marketer_email, start, end, subject, attendees)

    def book_meeting(self, user_email: str, marketer_email: str, selected_slot_index: int, attempts: int = 0) -> Optional[str]:
        """
        Book a meeting by selecting from available slots
        
        Args:
            user_email: Email of the user requesting the meeting
            marketer_email: Email of the marketing person
            selected_slot_index: Index of the selected slot (0-based)
            attempts: Number of previous attempts (for retry logic)
            
        Returns:
            Event ID if successful, None if failed
        """
        try:
            # Get available slots
            slots = self.suggest_slots(marketer_email, attempts)
            
            if not slots:
                print(f"❌ No available slots found for booking")
                return None
            
            if selected_slot_index >= len(slots):
                print(f"❌ Invalid slot index: {selected_slot_index} (only {len(slots)} slots available)")
                return None
            
            # Get the selected slot
            start_time, end_time = slots[selected_slot_index]
            
            # Create meeting subject
            subject = f"Meeting with {user_email}"
            attendees = [user_email, marketer_email]
            
            # Book the meeting
            print(f"📅 Booking meeting: {subject}")
            print(f"   📅 Time: {start_time} to {end_time}")
            print(f"   👥 Attendees: {', '.join(attendees)}")
            
            event_id = self.book_slot(marketer_email, start_time, end_time, subject, attendees)
            
            if event_id:
                print(f"✅ Meeting booked successfully! Event ID: {event_id}")
                return event_id
            else:
                print(f"❌ Failed to book meeting")
                return None
                
        except Exception as e:
            print(f"❌ Error booking meeting: {e}")
            return None
