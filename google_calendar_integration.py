"""
Real Google Calendar Integration for Marketing Scheduler
This replaces the MockCalendarAdapter with actual Google Calendar API access
Includes timezone-aware scheduling for marketing persons
"""
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import timezone utilities
try:
    from timezone_utils import TimezoneManager
except ImportError:
    # Fallback if timezone_utils is not available
    class TimezoneManager:
        @staticmethod
        def get_user_timezone(service, email: str) -> str:
            return 'UTC'
        
        @staticmethod
        def create_timezone_aware_datetime(date: datetime, hour: int, timezone_str: str) -> datetime:
            return pytz.UTC.localize(date.replace(hour=hour, minute=0, second=0, microsecond=0))

# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]


class GoogleCalendarAdapter:
    """Real Google Calendar integration with timezone awareness"""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize Google Calendar adapter
        
        Args:
            credentials_file: Path to Google OAuth credentials JSON
            token_file: Path to store OAuth tokens
        """
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.token_file = token_file or os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
        self.service = None
        self.timezone_cache = {}  # Cache for user timezones
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("🔄 Refreshed Google Calendar credentials")
                except Exception as e:
                    print(f"❌ Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_file}\\n"
                        f"Please download OAuth 2.0 credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ Successfully authenticated with Google Calendar")
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                print(f"💾 Saved credentials to {self.token_file}")
        
        # Build the service
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar service initialized")
    
    def get_user_timezone(self, email: str) -> str:
        """
        Get and cache the user's timezone
        
        Args:
            email: User's email address
            
        Returns:
            Timezone string (e.g., 'America/New_York', 'Asia/Kolkata')
        """
        if email in self.timezone_cache:
            return self.timezone_cache[email]
        
        # Get timezone using TimezoneManager
        user_timezone = TimezoneManager.get_user_timezone(self.service, email)
        
        # Cache the result
        self.timezone_cache[email] = user_timezone
        print(f"🌍 Using timezone for {email}: {user_timezone}")
        
        return user_timezone
    
    def get_busy_times(self, email: str, start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Get busy times for a specific email from Google Calendar (timezone-aware)
        
        Args:
            email: Email address to check calendar for
            start: Start time for the query (naive datetime - will be converted to user's timezone)
            end: End time for the query (naive datetime - will be converted to user's timezone)
            
        Returns:
            List of (start_time, end_time) tuples for busy periods (in user's local timezone)
        """
        try:
            # Get user's timezone
            user_timezone = self.get_user_timezone(email)
            user_tz = pytz.timezone(user_timezone)
            
            # Convert naive datetime to user's timezone
            if start.tzinfo is None:
                start_tz = user_tz.localize(start)
            else:
                start_tz = start.astimezone(user_tz)
                
            if end.tzinfo is None:
                end_tz = user_tz.localize(end)
            else:
                end_tz = end.astimezone(user_tz)
            
            # Convert to UTC for API call (API expects UTC)
            start_utc = start_tz.astimezone(pytz.UTC)
            end_utc = end_tz.astimezone(pytz.UTC)
            
            # Prepare the freebusy query with proper timezone formatting
            body = {
                'timeMin': start_utc.isoformat(),
                'timeMax': end_utc.isoformat(),
                'timeZone': user_timezone,  # Use user's timezone instead of UTC
                'items': [{'id': email}]
            }
            
            # Execute the freebusy query
            print(f"🔍 Querying Google Calendar for {email} from {start_tz.strftime('%Y-%m-%d %H:%M %Z')} to {end_tz.strftime('%Y-%m-%d %H:%M %Z')}")
            result = self.service.freebusy().query(body=body).execute()
            
            busy_times = []
            calendars = result.get('calendars', {})
            # print(calendars)

            if email in calendars:
                calendar_info = calendars[email]
                
                # Check for errors in the calendar response
                if 'errors' in calendar_info:
                    print(f"⚠️ Calendar errors for {email}: {calendar_info['errors']}")
                    return []
                
                busy_periods = calendar_info.get('busy', [])
                for period in busy_periods:
                    # Parse the datetime strings more carefully
                    start_str = period['start']
                    end_str = period['end']
                    
                    # Handle both RFC3339 formats (with and without 'Z')
                    if start_str.endswith('Z'):
                        busy_start_utc = datetime.fromisoformat(start_str[:-1] + '+00:00')
                    else:
                        busy_start_utc = datetime.fromisoformat(start_str)
                    
                    if end_str.endswith('Z'):
                        busy_end_utc = datetime.fromisoformat(end_str[:-1] + '+00:00')
                    else:
                        busy_end_utc = datetime.fromisoformat(end_str)
                    
                    # Convert UTC times to user's timezone
                    busy_start_local = busy_start_utc.astimezone(user_tz)
                    busy_end_local = busy_end_utc.astimezone(user_tz)
                    
                    # Keep timezone-aware for proper comparison with timezone-aware slots
                    busy_times.append((busy_start_local, busy_end_local))
                
                print(f"📅 Found {len(busy_periods)} busy periods for {email} (in {user_timezone})")
                for i, (bs, be) in enumerate(busy_times[:3], 1):  # Show first 3
                    print(f"   {i}. {bs.strftime('%Y-%m-%d %H:%M')} - {be.strftime('%H:%M')} ({user_timezone})")
                if len(busy_times) > 3:
                    print(f"   ... and {len(busy_times) - 3} more")
                    
            else:
                print(f"⚠️ No calendar access for {email} - may need permission or email doesn't exist")
                
                # Show what calendars are available in the response
                available_calendars = list(calendars.keys())
                if available_calendars:
                    print(f"📧 Available calendars in response: {available_calendars}")
            
            return busy_times
            
        except HttpError as error:
            print(f"❌ Google Calendar API error: {error}")
            
            # More specific error handling
            if error.resp.status == 400:
                print("🚨 Bad Request Error - This usually means:")
                print("   • Invalid email address format")
                print("   • Invalid datetime format") 
                print("   • Missing required parameters")
                print(f"   • Request details: {body}")
            elif error.resp.status == 403:
                print("🔑 Calendar access denied. User may need to grant permissions.")
            elif error.resp.status == 404:
                print("📅 Calendar not found for this email address.")
            
            # Try to get more details from the error
            try:
                error_details = error.content.decode('utf-8')
                print(f"🔍 Detailed error: {error_details}")
            except:
                pass
                
            return []
        except Exception as error:
            print(f"❌ Unexpected error in get_busy_times: {error}")
            return []
    
    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: List[str]) -> Optional[str]:
        """
        Create a Google Calendar event with professional meeting template (timezone-aware)
        
        Args:
            email: Organizer email (calendar owner)
            start: Meeting start time (naive datetime in organizer's local timezone)
            end: Meeting end time (naive datetime in organizer's local timezone)
            subject: Meeting subject
            attendees: List of attendee emails
            
        Returns:
            Event ID if successful, None if failed
        """
        try:
            # Get organizer's timezone
            organizer_timezone = self.get_user_timezone(email)
            organizer_tz = pytz.timezone(organizer_timezone)
            
            # Convert naive datetimes to timezone-aware (organizer's timezone)
            if start.tzinfo is None:
                start_tz = organizer_tz.localize(start)
            else:
                start_tz = start.astimezone(organizer_tz)
                
            if end.tzinfo is None:
                end_tz = organizer_tz.localize(end)
            else:
                end_tz = end.astimezone(organizer_tz)
            
            # Import timezone configuration
            try:
                from user_timezone_config import get_user_timezone_override, get_business_hours_for_timezone
                override_tz = get_user_timezone_override(email)
                if override_tz:
                    organizer_timezone = override_tz
                    print(f"🌍 Using configured timezone for {email}: {organizer_timezone}")
            except ImportError:
                pass
            
            # Create professional meeting description with timezone info
            attendee_list = '\n'.join(f'• {attendee}' for attendee in attendees)
            
            meeting_description = f"""📞 {subject}

🗓️ Meeting Details:
• Date: {start_tz.strftime('%A, %B %d, %Y')}
• Time: {start_tz.strftime('%H:%M')} - {end_tz.strftime('%H:%M')} ({organizer_timezone})
• Duration: {int((end_tz - start_tz).total_seconds() / 3600)} hour(s)

👥 Attendees:
{attendee_list}

🌍 Timezone Information:
• Meeting scheduled in: {organizer_timezone}
• Local time zone applied for marketing team member
• All times shown in organizer's local timezone

📋 Meeting Agenda:
• Welcome and introductions
• Discuss customer requirements and needs  
• Product/service overview and demonstration
• Technical Q&A session
• Pricing and package options
• Next steps and follow-up actions

💻 Meeting Connection Options:
📞 Phone Conference: Will be coordinated via email
🎥 Video Call Options:
  • Microsoft Teams (if available)
  • Zoom (backup option)
  • Google Meet (alternative)
  • Phone call (always available)

📧 Meeting Coordination:
• This meeting was automatically scheduled via ChatBot Assistant
• Meeting organizer will send connection details closer to meeting time
• Please check your email 15 minutes before the meeting for dial-in information

🔔 Important Notes:
• Please confirm your attendance by responding to this calendar invitation
• For any questions or schedule changes, contact: {email}
• If you need to reschedule, please provide at least 2 hours notice

📞 Emergency Contact:
• For urgent questions: Reply to this invitation
• For technical issues: Contact your meeting organizer directly

✅ This professional meeting invitation includes:
• Timezone-aware scheduling ({organizer_timezone})
• Multiple connection options (Teams, Zoom, Phone)
• Comprehensive agenda and preparation notes
• Clear contact information for coordination

Thank you for scheduling through our automated system!
Best regards,
ChatBot Assistant Team"""

            # Prepare the event with professional template and timezone
            event = {
                'summary': subject,
                'start': {
                    'dateTime': start_tz.isoformat(),
                    'timeZone': organizer_timezone,
                },
                'end': {
                    'dateTime': end_tz.isoformat(), 
                    'timeZone': organizer_timezone,
                },
                'attendees': [{'email': attendee} for attendee in attendees],
                'description': meeting_description,
                'location': f'Scheduled in {organizer_timezone} timezone',
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                        {'method': 'popup', 'minutes': 15},       # 15 minutes
                    ],
                },
                'transparency': 'opaque',  # Show as busy
                'visibility': 'default',
            }
            
            # Create the event
            # Create event with proper attendee configuration
            created_event = self.service.events().insert(
                calendarId='primary',  # Creates in authenticated account's calendar
                body=event,
                sendUpdates='all'  # Send email invitations to all attendees
            ).execute()
            
            event_id = created_event.get('id')
            print(f"✅ Created Google Calendar event: {event_id}")
            print(f"🌍 Event timezone: {organizer_timezone}")
            print(f"🕘 Event time: {start_tz.strftime('%A, %B %d, %Y at %H:%M %Z')} - {end_tz.strftime('%H:%M %Z')}")
            print(f"📧 Invitations sent to: {', '.join(attendees)}")
            
            # Verify attendees were added correctly
            created_attendees = created_event.get('attendees', [])
            print(f"👥 Confirmed attendees: {len(created_attendees)} people")
            for attendee in created_attendees:
                status = attendee.get('responseStatus', 'unknown')
                email = attendee.get('email', 'unknown')
                print(f"   - {email}: {status}")
            
            return event_id
            
        except HttpError as error:
            print(f"❌ Failed to create calendar event: {error}")
            if error.resp.status == 403:
                print("🔑 Insufficient permissions to create calendar events")
            return None
        except Exception as error:
            print(f"❌ Unexpected error in book_meeting: {error}")
            return None
    
    def get_calendar_info(self):
        """Get information about available calendars"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            print(f"📅 Found {len(calendars)} calendars:")
            for calendar in calendars:
                print(f"  - {calendar['summary']} ({calendar['id']})")
            
            return calendars
        except Exception as error:
            print(f"❌ Error getting calendar info: {error}")
            return []


# Test function for the Google Calendar integration
def test_google_calendar_integration():
    """Test the Google Calendar integration"""
    try:
        print("🧪 Testing Google Calendar Integration")
        print("=" * 50)
        
        # Initialize adapter
        adapter = GoogleCalendarAdapter()
        
        # Get calendar info
        print("\\n📋 Getting calendar information...")
        calendars = adapter.get_calendar_info()
        
        # Test busy times query
        print("\\n🔍 Testing busy times query...")
        start_time = datetime.now()
        end_time = start_time + timedelta(days=7)
        
        # Test with a known email (replace with actual test email)
        test_email = "your-test-email@gmail.com"
        busy_times = adapter.get_busy_times(test_email, start_time, end_time)
        
        print(f"Busy times for {test_email}:")
        for busy_start, busy_end in busy_times:
            print(f"  - {busy_start} to {busy_end}")
        
        print("\\n✅ Google Calendar integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_google_calendar_integration()
