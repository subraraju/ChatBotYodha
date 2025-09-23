"""
Marketing Scheduler module
- Provides a pluggable CalendarAdapter interface
- Includes a MockCalendarAdapter for local testing
- MarketingScheduler suggests 3 1-hour slots across different days
- Now supports real Google Calendar + Teams integration
"""
import os
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional

# Import real calendar integration
try:
    from google_calendar_integration import GoogleCalendarAdapter
    REAL_CALENDAR_AVAILABLE = True
    print("✅ Google Calendar integration available")
except ImportError as e:
    REAL_CALENDAR_AVAILABLE = False
    print(f"⚠️ Google Calendar integration not available: {e}")

# Try Teams integration (optional)
try:
    from teams_integration import EnhancedGoogleCalendarAdapter
    TEAMS_AVAILABLE = True
    print("✅ Teams integration available")
except ImportError as e:
    TEAMS_AVAILABLE = False
    print(f"⚠️ Teams integration not available: {e}")

START_NEXT_WEEK_DAYS = os.getenv("MARKETING_START_NEXT_WEEK_DAYS", "3,4,5,6")  # Thu(3), Fri(4), Sat(5), Sun(6) by default
MAX_ATTEMPTS = int(os.getenv("MARKETING_MAX_ATTEMPTS", "2"))

# Business hours configuration - 9 AM to 5 PM
BUSINESS_HOURS_START = int(os.getenv("MARKETING_BUSINESS_HOURS_START", "9"))  # 9 AM
BUSINESS_HOURS_END = int(os.getenv("MARKETING_BUSINESS_HOURS_END", "17"))     # 5 PM (17:00)


class CalendarAdapter:
    """Abstract calendar adapter interface. Implement real adapters (Google, Outlook) by subclassing."""
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        """Return list of (busy_start, busy_end) datetimes for the given email between start and end."""
        raise NotImplementedError

    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        """Book a meeting and return confirmation id or link. Return None on failure."""
        raise NotImplementedError


class MockCalendarAdapter(CalendarAdapter):
    """A simple mock calendar that treats almost all times as free for testing."""
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        # For testing we can simulate a couple of busy blocks
        busy = []
        # Example: every Tuesday 10-11 busy
        cur = start
        while cur < end:
            if cur.weekday() == 1:  # Tuesday
                busy_start = datetime.combine(cur.date(), time(10, 0))
                busy_end = datetime.combine(cur.date(), time(11, 0))
                busy.append((busy_start, busy_end))
            cur += timedelta(days=1)
        return busy

    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        # Mock success - return a fake meeting id
        return f"MOCK-MEETING-{email}-{int(start.timestamp())}"


class MarketingScheduler:
    def __init__(self, calendar_adapter: Optional[CalendarAdapter] = None, max_attempts: int = MAX_ATTEMPTS):
        # Use real calendar if available, otherwise mock
        if calendar_adapter:
            self.calendar = calendar_adapter
        elif REAL_CALENDAR_AVAILABLE:
            try:
                # Try enhanced version with Teams first, fallback to Google-only
                if TEAMS_AVAILABLE:
                    try:
                        from teams_integration import EnhancedGoogleCalendarAdapter
                        self.calendar = EnhancedGoogleCalendarAdapter()
                        print("✅ Using Google Calendar + Teams integration")
                    except Exception as teams_error:
                        print(f"⚠️ Teams integration failed: {teams_error}")
                        self.calendar = GoogleCalendarAdapter()
                        print("✅ Using Google Calendar only (no Teams)")
                else:
                    self.calendar = GoogleCalendarAdapter()
                    print("✅ Using Google Calendar only")
            except Exception as e:
                print(f"⚠️ Failed to initialize real calendar, using mock: {e}")
                self.calendar = MockCalendarAdapter()
        else:
            self.calendar = MockCalendarAdapter()
            print("⚠️ Real calendar integration not available, using mock")
        
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
        # If today is in start_next_week_days, start with next week (offset 1), else this week (0)
        if now.weekday() in self.start_next_week_days:
            return 1
        return 0

    def suggest_slots(self, marketer_email: str, attempts: int = 0, now: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """
        Smart slot suggestion with prioritization:
        1. First try to find 3+ slots on different days (preferred)
        2. If not enough different days, allow multiple slots per day
        3. If still not enough, try next week
        attempts: 0 -> first week (or this week depending on weekday), 1 -> next week, etc.
        """
        # Get marketer's timezone first
        marketer_timezone = self.calendar.get_user_timezone(marketer_email)
        print(f"🌍 Using timezone for {marketer_email}: {marketer_timezone}")
        
        # Create timezone-aware datetime objects
        import pytz
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

        # Search business hours only: 9 AM to 4 PM (so 1-hour slots end by 5 PM)
        candidate_hours = list(range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
        print(f"📋 Smart strategy: Searching for slots between {BUSINESS_HOURS_START}:00 AM and {BUSINESS_HOURS_END}:00 PM")
        
        # Get busy times once
        busy = self.calendar.get_busy_times(marketer_email, start_week, end_week)
        
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
        
        now = now or datetime.now()
        # Make now timezone-aware if it's not already
        if now.tzinfo is None:
            now = marketer_tz.localize(now)
        else:
            now = now.astimezone(marketer_tz)
            
        week_offset = self._choose_start_week_offset(now) + attempts
        start_week = self._week_start(now, week_offset)
        end_week = start_week + timedelta(days=7)

        # Search business hours only: 9 AM to 4 PM (so 1-hour slots end by 5 PM)
        candidate_hours = list(range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
        print(f"📋 Searching for slots between {BUSINESS_HOURS_START}:00 AM and {BUSINESS_HOURS_END}:00 PM")
        
        suggested = []
        max_slots = 6  # Show up to 6 slots instead of 3
        days_considered = 0

        # Get busy times once
        busy = self.calendar.get_busy_times(marketer_email, start_week, end_week)

        for day in range(0, 7):
            if len(suggested) >= max_slots:
                break
            day_date = (start_week + timedelta(days=day)).date()
            
            # Skip weekends (Saturday=5, Sunday=6)  
            if day_date.weekday() >= 5:
                continue
                
            days_considered += 1
            daily_slots = []  # Track slots found for this day
            
            for h in candidate_hours:
                if len(suggested) >= max_slots:
                    break
                # Create timezone-aware datetime objects in marketer's timezone
                naive_slot_start = datetime.combine(day_date, time(h, 0))
                slot_start = marketer_tz.localize(naive_slot_start)
                slot_end = slot_start + timedelta(hours=1)
                
                # Ensure both times are in the same timezone for proper comparison
                now_in_marketer_tz = now.astimezone(marketer_tz) if now.tzinfo else marketer_tz.localize(now)
                
                # ensure slot is in future (with timezone-aware comparison)
                if slot_start <= now_in_marketer_tz:
                    print(f"   ⏰ Skipping past slot: {slot_start.strftime('%A %H:%M')} (now: {now_in_marketer_tz.strftime('%A %H:%M')})")
                    continue
                # check conflicts
                conflict = False
                for bstart, bend in busy:
                    # overlap check
                    if slot_start < bend and slot_end > bstart:
                        conflict = True
                        break
                if not conflict:
                    suggested.append((slot_start, slot_end))
                    daily_slots.append((slot_start, slot_end))
                    print(f"✅ Found available business hours slot: {slot_start.strftime('%A %Y-%m-%d %H:%M')} - {slot_end.strftime('%H:%M')} ({marketer_timezone})")
            
            # Log how many slots found for this day
            if daily_slots:
                day_name = daily_slots[0][0].strftime('%A')
                print(f"   � {day_name}: {len(daily_slots)} slot(s) available")
                    
        print(f"�📊 Found {len(suggested)} available slots during business hours ({BUSINESS_HOURS_START}:00 AM - {BUSINESS_HOURS_END}:00 PM)")
        
        # If we didn't find enough slots and attempts < 2, suggest trying next week
        if len(suggested) < 3 and attempts < 2:
            print(f"⚠️ Only found {len(suggested)} slots this week, may need to check next week")
            
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
            start, end = slots[selected_slot_index]
            
            # Create professional meeting subject and attendees
            subject = f"Marketing Consultation - {start.strftime('%B %d, %Y')}"
            attendees = [user_email, marketer_email]
            
            print(f"📅 Booking meeting:")
            print(f"   Subject: {subject}")
            print(f"   Time: {start.strftime('%A %B %d, %Y at %I:%M %p')} - {end.strftime('%I:%M %p')}")
            print(f"   Attendees: {', '.join(attendees)}")
            
            # Book the meeting
            event_id = self.book_slot(marketer_email, start, end, subject, attendees)
            
            if event_id:
                print(f"✅ Meeting booked successfully! Event ID: {event_id}")
            else:
                print(f"❌ Failed to book meeting")
                
            return event_id
            
        except Exception as e:
            print(f"❌ Error booking meeting: {e}")
            return None
