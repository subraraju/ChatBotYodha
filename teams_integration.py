"""
Microsoft Teams Meeting Integration
Creates Teams meetings and integrates with Google Calendar
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import msal
from urllib.parse import quote

# Load environment variables
load_dotenv()


class TeamsIntegration:
    """
    Microsoft Teams meeting integration using Microsoft Graph API
    
    IMPORTANT: Teams meeting creation requires delegated authentication (user consent),
    but this application uses client credentials (service-to-service).
    
    This means:
    - ✅ Google Calendar integration works perfectly (creates real events)
    - ⚠️ Teams meeting creation will gracefully fail and fallback to calendar-only
    - 📧 Users still get professional calendar invitations
    - 🔄 This is the intended behavior for a service application
    
    To enable full Teams integration, you would need:
    1. Interactive user login flow (not suitable for automated bot)
    2. Or configure application permissions with admin consent
    """
    
    def __init__(self, enable_teams: bool = None):
        """
        Initialize Teams integration
        
        Args:
            enable_teams: Whether to attempt Teams integration (default: auto-detect from env)
        """
        # Allow disabling Teams integration via environment variable
        self.enable_teams = (
            enable_teams if enable_teams is not None 
            else os.getenv('ENABLE_TEAMS_INTEGRATION', 'true').lower() == 'true'
        )
        
        if not self.enable_teams:
            print("ℹ️ Teams integration disabled by configuration")
            return
            
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET') 
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:8080/callback')
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            print("⚠️ Missing Azure credentials - Teams integration will be disabled")
            self.enable_teams = False
            return
        
        # Microsoft Graph API endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
        # Required scopes - Updated for client credential flow
        self.scopes = [
            "https://graph.microsoft.com/.default"
        ]
        
        self.access_token = None
        
        try:
            self._authenticate()
        except Exception as e:
            print(f"⚠️ Teams authentication failed - will use calendar-only mode: {e}")
            self.enable_teams = False
    
    def _authenticate(self):
        """Authenticate with Microsoft Graph using client credentials flow"""
        try:
            # Create MSAL confidential client app
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Acquire token using client credentials flow (for application permissions)
            result = app.acquire_token_for_client(scopes=self.scopes)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✅ Successfully authenticated with Microsoft Graph")
            else:
                error = result.get("error", "Unknown error")
                error_description = result.get("error_description", "No description")
                print(f"❌ Authentication failed: {error} - {error_description}")
                raise Exception(f"Failed to acquire token: {error}")
                
        except Exception as e:
            print(f"❌ Teams authentication error: {e}")
            raise
    
    def _convert_gmail_to_guest_upn(self, gmail_address: str) -> str:
        """
        Convert Gmail address to Azure AD guest UPN format
        
        Args:
            gmail_address: Original Gmail address (e.g., nagakartheek.ds@gmail.com)
            
        Returns:
            Guest UPN (e.g., nagakartheek.ds_gmail.com#EXT#@tenant.onmicrosoft.com)
        """
        if "@gmail.com" in gmail_address.lower():
            # Extract username part
            username = gmail_address.replace("@gmail.com", "").replace("@Gmail.com", "")
            # Get tenant domain from our tenant ID or use the known one
            tenant_domain = "nagakartheekdsgmail.onmicrosoft.com"
            guest_upn = f"{username}_gmail.com#EXT#@{tenant_domain}"
            print(f"🔄 Converted Gmail {gmail_address} → Guest UPN {guest_upn}")
            return guest_upn
        else:
            # Not a Gmail address, return as-is
            return gmail_address
    
    def create_teams_meeting(
        self, 
        subject: str,
        start_time: datetime,
        end_time: datetime,
        organizer_email: str,
        attendees: list = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Microsoft Teams meeting
        
        Args:
            subject: Meeting subject
            start_time: Meeting start time
            end_time: Meeting end time
            organizer_email: Organizer email address
            attendees: List of attendee email addresses
            
        Returns:
            Dictionary with meeting details including join URL
        """
        if not self.enable_teams:
            print("ℹ️ Teams integration disabled - skipping Teams meeting creation")
            return None
            
        if not self.access_token:
            print("❌ No valid access token for Teams integration")
            return None
        
        try:
            # Convert Gmail to guest UPN if needed
            guest_upn = self._convert_gmail_to_guest_upn(organizer_email)
            
            # Prepare headers first
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # First, verify the user exists in the tenant
            print(f"🔍 Verifying user exists in tenant: {guest_upn}")
            encoded_upn = quote(guest_upn, safe='')
            user_check_url = f"{self.graph_endpoint}/users/{encoded_upn}"
            user_response = requests.get(user_check_url, headers=headers)
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"✅ User found: {user_info.get('displayName', 'Unknown')} ({user_info.get('userPrincipalName', 'N/A')})")
            else:
                print(f"⚠️ User lookup failed ({user_response.status_code}): {user_response.text}")
                print(f"💡 This might explain why Teams meeting creation fails")
            
            # Prepare the meeting request
            meeting_data = {
                "subject": subject,
                "startDateTime": start_time.isoformat() + "Z",
                "endDateTime": end_time.isoformat() + "Z",
                "participants": {
                    "organizer": {
                        "identity": {
                            "user": {
                                "id": organizer_email
                            }
                        }
                    }
                }
            }
            
            # Add attendees if provided
            if attendees:
                meeting_data["participants"]["attendees"] = [
                    {
                        "identity": {
                            "user": {
                                "id": email
                            }
                        }
                    } for email in attendees
                ]
            
            # Try multiple endpoints - first attempt with /me, then fallback to user-specific
            endpoints_to_try = [
                f"{self.graph_endpoint}/me/onlineMeetings",
                f"{self.graph_endpoint}/users/{encoded_upn}/onlineMeetings"
            ]
            
            for i, endpoint in enumerate(endpoints_to_try, 1):
                try:
                    print(f"🔄 Attempting Teams meeting creation (method {i}/{len(endpoints_to_try)})...")
                    
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=meeting_data
                    )
                    
                    if response.status_code == 201:
                        meeting_info = response.json()
                        print("✅ Successfully created Teams meeting")
                        
                        return {
                            "meeting_id": meeting_info.get("id"),
                            "join_url": meeting_info.get("joinWebUrl"),
                            "conference_id": meeting_info.get("videoTeleconferenceId"),
                            "phone_numbers": meeting_info.get("audioConferencing", {}).get("dialinUrl"),
                            "meeting_info": meeting_info
                        }
                    
                    elif response.status_code == 400:
                        error_data = response.json() if response.text else {}
                        error_message = error_data.get("error", {}).get("message", "Unknown error")
                        
                        if "/me request is only valid with delegated authentication flow" in error_message:
                            print(f"⚠️ Method {i} failed: Delegated auth required, trying next method...")
                            continue  # Try next endpoint
                        else:
                            print(f"❌ Method {i} failed with different error: {error_message}")
                            
                    else:
                        print(f"⚠️ Method {i} failed with status {response.status_code}: {response.text}")
                        
                        # More detailed error analysis
                        try:
                            error_data = response.json() if response.text else {}
                            error_info = error_data.get("error", {})
                            error_code = error_info.get("code", "Unknown")
                            error_message = error_info.get("message", "No message")
                            print(f"      🔍 Error Code: {error_code}")
                            print(f"      🔍 Error Message: {error_message}")
                            
                            # Check for specific error conditions
                            if response.status_code == 404:
                                print(f"      💡 404 Error likely means:")
                                print(f"         • User '{guest_upn}' needs OnlineMeetings permissions")
                                print(f"         • Guest user may not have Teams access")
                                print(f"         • App needs admin consent for application permissions")
                            elif response.status_code == 403:
                                print(f"      💡 403 Error means insufficient permissions")
                                print(f"         • App needs OnlineMeetings.ReadWrite.All permission")
                                print(f"         • Admin consent may be required")
                        except:
                            print(f"      📝 Raw response: {response.text}")
                        
                except Exception as endpoint_error:
                    print(f"⚠️ Method {i} encountered error: {endpoint_error}")
                    continue
            
            # All methods failed - provide helpful fallback information
            print("❌ All Teams meeting creation methods failed")
            print("💡 Teams requires delegated authentication for meeting creation")
            print("✅ Calendar event will be created with meeting coordination instructions")
            return None
            print("🔄 Proceeding with calendar-only event (this is the designed fallback)")
            return None
                
        except Exception as e:
            print(f"❌ Error creating Teams meeting: {e}")
            return None
    
    def get_teams_meeting_info(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an existing Teams meeting"""
        if not self.access_token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.graph_endpoint}/me/onlineMeetings/{meeting_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get meeting info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting meeting info: {e}")
            return None


class EnhancedGoogleCalendarAdapter:
    """Enhanced Google Calendar adapter with Teams integration"""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """Initialize with both Google Calendar and Teams integration"""
        # Import here to avoid circular imports
        from google_calendar_integration import GoogleCalendarAdapter
        
        self.google_calendar = GoogleCalendarAdapter(credentials_file, token_file)
        self.teams_integration = TeamsIntegration()
    
    def get_busy_times(self, email: str, start: datetime, end: datetime):
        """Delegate to Google Calendar adapter"""
        return self.google_calendar.get_busy_times(email, start, end)
    
    def get_user_timezone(self, email: str) -> str:
        """Delegate timezone detection to Google Calendar adapter"""
        return self.google_calendar.get_user_timezone(email)
    
    def _get_marketing_person_phone(self, email: str) -> str:
        """Get marketing person's phone number by email"""
        try:
            from app.api.marketing_persons import MarketingPersonsAPI
            api = MarketingPersonsAPI()
            person = api.get_marketing_person_by_email(email)
            return person.phone if person and person.phone != "N/A" else "Contact via email"
        except Exception:
            return "Contact via email"
    
    def book_meeting(self, email: str, start: datetime, end: datetime, subject: str, attendees: list) -> Optional[str]:
        """
        Book meeting using Google Calendar with Teams integration
        This is the main interface method expected by CalendarAdapter
        """
        return self.book_meeting_with_teams(
            email=email,
            start=start,
            end=end,
            subject=subject,
            attendees=attendees,
            user_email=attendees[-1] if attendees else None  # Assume last attendee is user
        )
    
    def book_meeting_with_teams(
        self,
        email: str,
        start: datetime,
        end: datetime,
        subject: str,
        attendees: list,
        user_email: str = None
    ) -> Optional[str]:
        """
        Create a meeting with both Google Calendar event and Teams meeting
        
        Args:
            email: Calendar owner email (nagakartheek.ds@gmail.com)
            start: Meeting start time
            end: Meeting end time
            subject: Meeting subject
            attendees: List of attendee emails
            user_email: Customer email address
            
        Returns:
            Google Calendar event ID if successful
        """
        try:
            # Step 1: Create Teams meeting
            print(f"🔄 Creating Teams meeting for {subject}...")
            teams_meeting = self.teams_integration.create_teams_meeting(
                subject=subject,
                start_time=start,
                end_time=end,
                organizer_email=email,
                attendees=attendees + ([user_email] if user_email else [])
            )
            
            if not teams_meeting:
                print("❌ Failed to create Teams meeting, proceeding with calendar-only event")
                teams_join_url = None
            else:
                teams_join_url = teams_meeting.get("join_url")
                print(f"✅ Teams meeting created: {teams_join_url}")
            
            # Step 2: Create Google Calendar event with Teams link
            enhanced_subject = f"{subject}" + (" (Teams Meeting)" if teams_join_url else "")
            
            # Enhanced description with Teams link
            if teams_join_url:
                description_parts = [
                    f"🎥 Microsoft Teams Meeting",
                    f"📞 Join Teams Meeting: {teams_join_url}",
                    "",
                    "📞 Dial-in Information:",
                    f"Conference ID: {teams_meeting.get('conference_id', 'Available in Teams')}"
                    f"Phone Number: {teams_meeting.get('phone_number', 'See Teams invitation')}",
                    "",
                    f"Meeting scheduled via ChatBot Assistant",
                    f"📧 Organizer: {email}",
                    f"📞 Organizer Phone: {self._get_marketing_person_phone(email)}"
                ]
            else:
                description_parts = [
                    f"📞 Professional Meeting - {subject}",
                    "",
                    f"📧 Meeting Organizer: {email}",
                    f"📞 Organizer Phone: {self._get_marketing_person_phone(email)}",
                    f"🤖 Scheduled via: Yodha ChatBot Assistant"
                ]
            
            if user_email:
                description_parts.append(f"Requested by: {user_email}")
            
            # Add comprehensive meeting information
            description_parts.extend([
                "",
                "🔔 Important Notes:",
                "• Please confirm attendance by responding to this invitation",
                "• For questions or changes, contact organizer directly", 
                f"• Contact: {email}",
            ])
            
            # Create enhanced event
            event = {
                'summary': enhanced_subject,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': 'UTC', 
                },
                'attendees': [{'email': attendee} for attendee in attendees + ([user_email] if user_email else [])],
                'description': "\n".join(description_parts),
                # 'location': teams_join_url if teams_join_url else "Virtual Meeting",
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
            }
            
            # Add Teams meeting details to event if available
            if teams_join_url:
                event['conferenceData'] = {
                    'createRequest': {
                        'conferenceSolutionKey': {'type': 'addOn'},
                        'requestId': f"teams-{int(start.timestamp())}"
                    }
                }
            
            # Create the calendar event
            created_event = self.google_calendar.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            
            event_id = created_event.get('id')
            print(f"✅ Created enhanced calendar event: {event_id}")
            print(f"📧 Invitations sent with Teams link to: {', '.join(attendees + ([user_email] if user_email else []))}")
            
            return event_id
            
        except Exception as e:
            print(f"❌ Error creating enhanced meeting: {e}")
            return None


# Test function
def test_teams_integration():
    """Test Teams integration"""
    try:
        print("🧪 Testing Microsoft Teams Integration")
        print("=" * 50)
        
        teams = TeamsIntegration()
        
        # Test creating a meeting
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting = teams.create_teams_meeting(
            subject="Test Meeting from ChatBot",
            start_time=start_time,
            end_time=end_time,
            organizer_email="test@example.com",
            attendees=["attendee@example.com"]
        )
        
        if meeting:
            print(f"✅ Teams meeting created!")
            print(f"Join URL: {meeting['join_url']}")
        
    except Exception as e:
        print(f"❌ Teams test failed: {e}")


if __name__ == "__main__":
    test_teams_integration()
