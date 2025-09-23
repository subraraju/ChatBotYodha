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
    """Real calendar adapter implementation using Google Calendar API"""
    
    def __init__(self):
        """Initialize with real Google Calendar integration"""
        self.google_adapter = None
        self.enhanced_adapter = None
        
        try:
            # Import and initialize real calendar adapters
            from google_calendar_integration import GoogleCalendarAdapter
            from teams_integration import EnhancedGoogleCalendarAdapter
            
            self.google_adapter = GoogleCalendarAdapter()
            if hasattr(self.google_adapter, 'service') and self.google_adapter.service:
                self.enhanced_adapter = EnhancedGoogleCalendarAdapter(self.google_adapter)
                print("✅ MockCalendarAdapter: Real Google Calendar integration initialized")
            else:
                print("⚠️ MockCalendarAdapter: Google Calendar service not available")
                
        except Exception as e:
            print(f"⚠️ MockCalendarAdapter: Failed to initialize real calendar, will use fallback: {e}")
    
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Retrieve real busy times from Google Calendar API
        
        Args:
            email: Email address to check calendar for
            start: Start time for the search range (timezone-aware)
            end: End time for the search range (timezone-aware)
            
        Returns:
            List of (start_time, end_time) tuples for busy periods
        """
        try:
            # Use the enhanced adapter if available
            if self.enhanced_adapter:
                return self.enhanced_adapter.get_busy_times(email, start, end)
            elif self.google_adapter:
                return self.google_adapter.get_busy_times(email, start, end)
            else:
                print(f"⚠️ No real calendar integration available for {email}")
                return []
                
        except Exception as e:
            print(f"❌ Error retrieving busy times for {email}: {e}")
            return []
        
    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        """
        Book a real meeting using Google Calendar API
        
        Args:
            email: Organizer's email address
            start: Meeting start time (timezone-aware)
            end: Meeting end time (timezone-aware)
            subject: Meeting subject/title
            attendees: List of attendee email addresses
            
        Returns:
            Event ID if successful, None if failed
        """
        try:
            # Use the enhanced adapter if available
            if self.enhanced_adapter:
                event_id = self.enhanced_adapter.book_meeting(email, start, end, subject, attendees)
                if event_id:
                    print(f"✅ Real meeting booked via Teams integration: '{subject}' from {start} to {end}")
                    return event_id
            
            # Fall back to Google Calendar adapter
            if self.google_adapter:
                event_id = self.google_adapter.book_meeting(email, start, end, subject, attendees)
                if event_id:
                    print(f"✅ Real meeting booked via Google Calendar: '{subject}' from {start} to {end}")
                    return event_id
            
            # If no real integration available
            print(f"⚠️ No real calendar integration available - meeting not booked")
            return None
            
        except Exception as e:
            print(f"❌ Error booking real meeting: {e}")
            return None
        
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
                from teams_integration import EnhancedGoogleCalendarAdapter
                from google_calendar_integration import GoogleCalendarAdapter
                
                # First try Google Calendar
                google_adapter = GoogleCalendarAdapter()
                if hasattr(google_adapter, 'service') and google_adapter.service:
                    self.calendar = EnhancedGoogleCalendarAdapter(google_adapter)
                    print("✅ Using REAL Google Calendar + Teams integration")
                else:
                    raise Exception("Google Calendar service not initialized")
                    
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
        # Only move to next week if we're past Thursday or it's Friday afternoon
        current_day = now.weekday()  # Monday=0, Sunday=6
        current_hour = now.hour
        
        # Be less aggressive - only move to next week if:
        # - It's Friday (day 4) or later, OR
        # - It's Thursday (day 3) after 3 PM
        if current_day >= 4 or (current_day >= 3 and current_hour >= 15):
            return 1  # Start from next week
        else:
            return 0  # Start from this week

    def suggest_slots(self, marketer_email: str, attempts: int = 0, now: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """
        Correct logic: Find available slots based on gaps between booked meetings
        1. For each weekday, get booked slots sorted by start time
        2. Find gaps ≥1 hour between consecutive bookings
        3. First slot per unique day
        4. If <3 unique days, add more slots from earliest days
        5. If still <3, try next week
        """
        print(f"🔍 SLOT SELECTION PROCESS - DETAILED LOGGING")
        print(f"🌍 Business hours: {BUSINESS_HOURS_START}:00 AM - {BUSINESS_HOURS_END}:00 PM")
        
        # Get marketer's timezone first
        marketer_timezone = self.calendar.get_user_timezone(marketer_email)
        marketer_tz = pytz.timezone(marketer_timezone)
        print(f"🌍 Marketer: {marketer_email} | Timezone: {marketer_timezone}")
        
        now = now or datetime.now()
        if now.tzinfo is None:
            now = marketer_tz.localize(now)
        else:
            now = now.astimezone(marketer_tz)
            
        print(f"🕐 Current time: {now.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
        
        week_offset = self._choose_start_week_offset(now) + attempts
        start_week = self._week_start(now, week_offset)
        end_week = start_week + timedelta(days=7)
        
        print(f"📅 Target week: {start_week.strftime('%A, %B %d')} to {end_week.strftime('%A, %B %d')}")
        print()
        
        # STEP 1: Get booked slots for the entire week
        print("📋 STEP 1: Getting booked slots for the week")
        busy_times = self.calendar.get_busy_times(marketer_email, start_week, end_week)
        print(f"📊 Retrieved {len(busy_times)} booked time slots")
        
        if busy_times:
            print("🔒 Booked slots this week:")
            for i, (start, end) in enumerate(busy_times, 1):
                print(f"   {i}. {start.strftime('%A %m/%d at %H:%M')} - {end.strftime('%H:%M')}")
        else:
            print("📝 No booked slots found - week appears free")
        print()
        
        # STEP 2: Process each weekday to find gaps
        print("🔍 STEP 2: Finding available gaps for each weekday")
        daily_available_slots = {}
        
        for day_offset in range(5):  # Monday to Friday only
            day_date = (start_week + timedelta(days=day_offset)).date()
            day_name = day_date.strftime('%A')
            
            print(f"📅 Processing {day_name} {day_date.strftime('%m/%d')}:")
            
            # Filter booked slots for this specific day
            day_busy_times = [(start, end) for start, end in busy_times if start.date() == day_date]
            day_busy_times.sort(key=lambda x: x[0])  # Sort by start time
            
            print(f"   📋 Booked slots for {day_name}: {len(day_busy_times)}")
            for j, (start, end) in enumerate(day_busy_times, 1):
                print(f"      {j}. {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            
            # Find gaps between bookings
            day_start = marketer_tz.localize(datetime.combine(day_date, time(BUSINESS_HOURS_START, 0)))
            day_end = marketer_tz.localize(datetime.combine(day_date, time(BUSINESS_HOURS_END, 0)))
            
            available_gaps = []
            
            if not day_busy_times:
                print(f"   ✅ Entire day free: {day_start.strftime('%H:%M')} - {day_end.strftime('%H:%M')}")
                available_gaps.append((day_start, day_end))
            else:
                print(f"   🔍 Looking for gaps between {day_start.strftime('%H:%M')} - {day_end.strftime('%H:%M')}...")
                
                # Gap before first booking
                first_booking_start = day_busy_times[0][0]
                gap_duration_hours = (first_booking_start - day_start).total_seconds() / 3600
                if gap_duration_hours >= 1.0:
                    available_gaps.append((day_start, first_booking_start))
                    print(f"      🟢 Gap before first booking: {day_start.strftime('%H:%M')} - {first_booking_start.strftime('%H:%M')} ({gap_duration_hours:.1f}h)")
                
                # Gaps between consecutive bookings
                for k in range(len(day_busy_times) - 1):
                    gap_start = day_busy_times[k][1]  # End of current booking
                    gap_end = day_busy_times[k + 1][0]  # Start of next booking
                    gap_duration_hours = (gap_end - gap_start).total_seconds() / 3600
                    
                    if gap_duration_hours >= 1.0:
                        available_gaps.append((gap_start, gap_end))
                        print(f"      🟢 Gap between bookings: {gap_start.strftime('%H:%M')} - {gap_end.strftime('%H:%M')} ({gap_duration_hours:.1f}h)")
                
                # Gap after last booking
                last_booking_end = day_busy_times[-1][1]
                gap_duration_hours = (day_end - last_booking_end).total_seconds() / 3600
                if gap_duration_hours >= 1.0:
                    available_gaps.append((last_booking_end, day_end))
                    print(f"      🟢 Gap after last booking: {last_booking_end.strftime('%H:%M')} - {day_end.strftime('%H:%M')} ({gap_duration_hours:.1f}h)")
            
            # Convert gaps to 1-hour slots, filtering out past times
            day_available_slots = []
            for gap_start, gap_end in available_gaps:
                # Skip if gap starts in the past
                effective_start = max(gap_start, now + timedelta(minutes=30))  # 30min buffer
                
                if effective_start >= gap_end:
                    print(f"      ⏰ Gap in the past, skipping")
                    continue
                
                # Create 1-hour slots within this gap
                slot_start = effective_start
                gap_slots = []
                while slot_start + timedelta(hours=1) <= min(gap_end, day_end):
                    slot_end = slot_start + timedelta(hours=1)
                    gap_slots.append((slot_start, slot_end))
                    slot_start += timedelta(hours=1)
                
                day_available_slots.extend(gap_slots)
                print(f"      📍 Created {len(gap_slots)} 1-hour slot(s) in this gap")
            
            if day_available_slots:
                daily_available_slots[day_date] = day_available_slots
                print(f"   ✅ {day_name} total available slots: {len(day_available_slots)}")
                for m, (start, end) in enumerate(day_available_slots, 1):
                    print(f"      {m}. {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            else:
                print(f"   ❌ {day_name}: No available slots")
            print()
        
        # STEP 3: Select first slot per unique day
        print("🎯 STEP 3: Selecting first slot per unique day")
        suggested_slots = []
        
        for check_date in sorted(daily_available_slots.keys()):
            if daily_available_slots[check_date]:
                first_slot = daily_available_slots[check_date][0]
                suggested_slots.append(first_slot)
                day_name = check_date.strftime('%A')
                print(f"   ✅ {day_name}: Selected {first_slot[0].strftime('%H:%M')} - {first_slot[1].strftime('%H:%M')}")
        
        print(f"📊 Step 3 result: {len(suggested_slots)} slots from unique days")
        
        # STEP 4: If less than 3, add more slots from earliest days
        target_slots = 3
        if len(suggested_slots) < target_slots:
            print(f"🔄 STEP 4: Need {target_slots - len(suggested_slots)} more slots, adding from earliest days")
            
            for check_date in sorted(daily_available_slots.keys()):
                if len(suggested_slots) >= target_slots:
                    break
                    
                available_for_day = daily_available_slots[check_date]
                slots_already_from_day = len([s for s in suggested_slots if s[0].date() == check_date])
                
                # Add remaining slots from this day
                for slot in available_for_day[slots_already_from_day:]:
                    if len(suggested_slots) >= target_slots:
                        break
                    suggested_slots.append(slot)
                    day_name = check_date.strftime('%A')
                    print(f"   ➕ {day_name}: Added {slot[0].strftime('%H:%M')} - {slot[1].strftime('%H:%M')}")
        
        # STEP 5: Sort by start time
        print(f"� STEP 5: Sorting {len(suggested_slots)} selected slots by start time")
        suggested_slots.sort(key=lambda x: x[0])
        
        print()
        print("✅ FINAL SELECTED SLOTS:")
        if not suggested_slots:
            print("❌ No available slots found")
            if attempts < 1:
                print("🔄 Trying next week...")
                return self.suggest_slots(marketer_email, attempts + 1, now)
        else:
            for i, (start, end) in enumerate(suggested_slots[:target_slots], 1):
                day_name = start.strftime('%A')
                print(f"   {i}. {day_name} {start.strftime('%m/%d at %H:%M')} - {end.strftime('%H:%M')}")
        
        return suggested_slots[:target_slots]

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
