"""
Google Calendar integration — find available slots, book meetings.

Wraps the Google Calendar API (v3).  Falls back gracefully when
credentials are not configured.

Usage:
    from app.services.calendar_service import calendar_service
    slots = await calendar_service.suggest_slots("marketer@example.com")
    event_id = await calendar_service.book_meeting(slot, subject, attendees)
"""

import logging
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# Try importing google-api-python-client (optional dep)
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    _GCAL_AVAILABLE = True
except ImportError:
    _GCAL_AVAILABLE = False
    logger.info("google-api-python-client not installed — calendar disabled")

try:
    import pytz
except ImportError:
    pytz = None  # type: ignore


# ── Helpers ───────────────────────────────────────────────────────────

def _tz():
    """Return target timezone object."""
    if pytz:
        return pytz.timezone(settings.MEETING_TIMEZONE)
    from datetime import timezone as _tz_mod
    return _tz_mod.utc


def _week_start(base: datetime, offset: int = 0) -> datetime:
    """Monday 00:00 of the week *offset* weeks from *base*."""
    monday = base - timedelta(days=base.weekday()) + timedelta(weeks=offset)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def _should_skip_to_next_week(now: datetime) -> bool:
    """True if it's Friday or later, or Thursday after 3 PM."""
    wd = now.weekday()  # Mon=0
    if wd >= 4:  # Fri, Sat, Sun
        return True
    if wd == 3 and now.hour >= 15:  # Thursday after 3 PM
        return True
    return False


# ── Calendar Service ──────────────────────────────────────────────────

class CalendarService:
    """Suggest available meeting slots and book them via Google Calendar."""

    def __init__(self) -> None:
        self._service = None
        self.biz_start = settings.BUSINESS_HOURS_START
        self.biz_end = settings.BUSINESS_HOURS_END
        self.max_attempts = settings.MAX_SCHEDULING_ATTEMPTS

        if _GCAL_AVAILABLE and settings.GOOGLE_CALENDAR_CREDENTIALS_FILE:
            self._init_google()

    @property
    def ready(self) -> bool:
        return self._service is not None

    # ── public: slots ─────────────────────────────────────────────────

    async def suggest_slots(
        self,
        marketer_email: str,
        attempt: int = 0,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return up to 3 one-hour slots on different days this/next week.

        Each slot: {"start": iso, "end": iso, "display": "Mon Jun 5 10:00-11:00 AM"}
        """
        tz = _tz()
        now = now or datetime.now(tz)
        week_offset = 1 if _should_skip_to_next_week(now) else 0
        week_offset += attempt

        monday = _week_start(now, week_offset)
        busy = await self._get_busy(marketer_email, monday, monday + timedelta(days=5))

        slots = self._find_free_slots(monday, busy, now, tz)

        # Pick first slot per unique day, aim for 3
        by_day: Dict[int, Dict] = {}
        for s in slots:
            day = datetime.fromisoformat(s["start"]).weekday()
            if day not in by_day:
                by_day[day] = s
            if len(by_day) >= 3:
                break

        result = list(by_day.values())

        # If < 3 and another attempt allowed, recurse into next week
        if len(result) < 3 and attempt < self.max_attempts - 1:
            more = await self.suggest_slots(marketer_email, attempt + 1, now)
            for s in more:
                if len(result) >= 3:
                    break
                result.append(s)

        return result[:3]

    # ── public: book ──────────────────────────────────────────────────

    async def book_meeting(
        self,
        start_iso: str,
        end_iso: str,
        subject: str,
        attendees: List[str],
        description: str = "",
    ) -> Optional[str]:
        """
        Create a Google Calendar event. Returns event_id or None.
        """
        if not self.ready:
            logger.warning("Calendar not configured — mock-booking")
            return "mock-event-id"

        body: Dict[str, Any] = {
            "summary": subject,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": settings.MEETING_TIMEZONE},
            "end": {"dateTime": end_iso, "timeZone": settings.MEETING_TIMEZONE},
            "attendees": [{"email": e} for e in attendees],
            "reminders": {"useDefault": True},
        }

        if settings.TEAMS_MEETING_ENABLED:
            body["conferenceData"] = {
                "createRequest": {"requestId": f"meet-{start_iso}"}
            }

        try:
            event = (
                self._service.events()
                .insert(calendarId="primary", body=body, conferenceDataVersion=1)
                .execute()
            )
            logger.info("Calendar event created: %s", event.get("id"))
            return event.get("id")
        except Exception as exc:
            logger.error("Failed to create calendar event: %s", exc)
            return None

    # ── private ───────────────────────────────────────────────────────

    def _init_google(self) -> None:
        """Load credentials and build the Calendar API service."""
        import json
        from google.oauth2.credentials import Credentials

        cred_path = settings.GOOGLE_CALENDAR_CREDENTIALS_FILE
        try:
            with open(cred_path) as f:
                cred_data = json.load(f)
            creds = Credentials.from_authorized_user_info(cred_data)
            self._service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar service initialised")
        except Exception as exc:
            logger.warning("Could not init Google Calendar: %s", exc)

    async def _get_busy(
        self, email: str, start: datetime, end: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """Query free/busy for *email* in [start, end)."""
        if not self.ready:
            return []

        tz_str = settings.MEETING_TIMEZONE
        body = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "timeZone": tz_str,
            "items": [{"id": email}],
        }
        try:
            resp = self._service.freebusy().query(body=body).execute()
            busy_raw = resp["calendars"].get(email, {}).get("busy", [])
            return [
                (
                    datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                    datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
                )
                for b in busy_raw
            ]
        except Exception as exc:
            logger.error("FreeBusy query failed: %s", exc)
            return []

    def _find_free_slots(
        self,
        monday: datetime,
        busy: List[Tuple[datetime, datetime]],
        now: datetime,
        tz: Any,
    ) -> List[Dict[str, Any]]:
        """Generate 1-hour free slots Mon–Fri, excluding busy & past."""
        slots: List[Dict[str, Any]] = []
        buffer = now + timedelta(minutes=30)

        for day_offset in range(5):  # Mon-Fri
            day_start = monday + timedelta(days=day_offset)
            ws = day_start.replace(hour=self.biz_start, minute=0, second=0)
            we = day_start.replace(hour=self.biz_end, minute=0, second=0)

            # Collect busy intervals for this day
            day_busy = [
                (max(b[0], ws), min(b[1], we))
                for b in busy
                if b[1] > ws and b[0] < we
            ]
            day_busy.sort()

            # Walk through gaps
            cursor = ws
            for bs, be in day_busy:
                while cursor + timedelta(hours=1) <= bs:
                    if cursor >= buffer:
                        slots.append(self._slot_dict(cursor, tz))
                    cursor += timedelta(hours=1)
                cursor = max(cursor, be)

            # After last busy block
            while cursor + timedelta(hours=1) <= we:
                if cursor >= buffer:
                    slots.append(self._slot_dict(cursor, tz))
                cursor += timedelta(hours=1)

        return slots

    @staticmethod
    def _slot_dict(start: datetime, tz: Any) -> Dict[str, Any]:
        end = start + timedelta(hours=1)
        # Use platform-safe formatting (%-d is Linux-only, %#d is Windows-only)
        day = str(start.day)  # no zero-padding, works everywhere
        display = f"{start.strftime('%a %b')} {day} {start.strftime('%I:%M')}-{end.strftime('%I:%M %p')}"
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "display": display,
        }


# ── Singleton ─────────────────────────────────────────────────────────

calendar_service = CalendarService()
