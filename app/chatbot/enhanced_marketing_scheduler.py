#!/usr/bin/env python3
"""
Enhanced Marketing Meeting Scheduler with Person Selection
Integrates marketing person selection into the chatbot flow
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Import the modules
try:
    from app.api.marketing_persons import MarketingPersonsAPI, get_marketing_persons_list, get_marketing_person_info_by_selection, get_customer_name_by_email, get_customer_phone_by_email
    from app.chatbot.marketing_scheduler import MarketingScheduler
    from app.services.messaging import WhatsAppService
except ImportError:
    # Fallback imports for direct execution
    sys.path.insert(0, os.path.join(parent_dir, 'app', 'api'))
    sys.path.insert(0, os.path.join(parent_dir, 'app', 'chatbot'))
    sys.path.insert(0, os.path.join(parent_dir, 'app', 'services'))
    from marketing_persons import MarketingPersonsAPI, get_marketing_persons_list, get_marketing_person_info_by_selection, get_customer_name_by_email, get_customer_phone_by_email
    from marketing_scheduler import MarketingScheduler
    from messaging import WhatsAppService

class EnhancedMarketingScheduler:
    """Enhanced scheduler with marketing person selection"""
    
    def __init__(self):
        self.marketing_api = MarketingPersonsAPI()
        self.scheduler = MarketingScheduler()
        self.current_session = {}  # Store session state
        
        # Initialize WhatsApp service
        try:
            self.whatsapp_service = WhatsAppService()
            self.whatsapp_enabled = True
        except Exception as e:
            self.whatsapp_service = None
            self.whatsapp_enabled = False
            print(f"⚠️ WhatsApp service not available: {e}")
    
    def start_meeting_request(self, user_email: str) -> Dict:
        """
        Start the meeting scheduling process by showing marketing person selection
        
        Args:
            user_email: Email of the user requesting the meeting
            
        Returns:
            Dictionary with response and next step info
        """
        try:
            # Get available marketing persons
            selection_text = self.marketing_api.format_selection_list()
            
            # Store user info in session
            self.current_session = {
                'user_email': user_email,
                'step': 'selecting_person',
                'timestamp': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'message': selection_text,
                'step': 'selecting_person',
                'instructions': 'Please reply with the number of your preferred marketing team member (e.g., "1" or "2").'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Sorry, I encountered an error while fetching our marketing team. Please try again later.",
                'error': str(e)
            }
    
    def handle_person_selection(self, selection_input: str, user_email: str = None) -> Dict:
        """
        Handle the marketing person selection
        
        Args:
            selection_input: User's selection (should be a number)
            user_email: User's email (optional, can use from session)
            
        Returns:
            Dictionary with response and next step info
        """
        try:
            # Use email from session if not provided
            if not user_email and 'user_email' in self.current_session:
                user_email = self.current_session['user_email']
            
            # Parse selection
            try:
                selection_num = int(selection_input.strip())
            except ValueError:
                return {
                    'success': False,
                    'message': "❌ Please enter a valid number (e.g., 1, 2, or 3) to select a marketing team member.",
                    'step': 'selecting_person'
                }
            
            # Get selected marketing person
            person_info = get_marketing_person_info_by_selection(selection_num)
            
            if not person_info:
                active_persons = self.marketing_api.get_active_marketing_persons()
                max_selection = len(active_persons)
                return {
                    'success': False,
                    'message': f"❌ Invalid selection. Please choose a number between 1 and {max_selection}.",
                    'step': 'selecting_person'
                }
            
            # Get available slots for the selected marketing person
            marketing_email = person_info['email']
            marketing_name = person_info['name']
            
            print(f"📅 Finding available slots for {marketing_name} ({marketing_email})...")
            
            slots = self.scheduler.suggest_slots(marketing_email)
            
            if not slots:
                return {
                    'success': False,
                    'message': f"😔 Unfortunately, **{marketing_name}** doesn't have any available slots this week. Please try again next week or contact us directly at {marketing_email}.",
                    'step': 'no_slots_available'
                }
            
            # Format available slots
            slots_text = f"✅ Great choice! **{marketing_name}** is available for the following time slots:\n\n"
            
            for i, (start, end) in enumerate(slots, 1):
                day_name = start.strftime('%A')
                date_str = start.strftime('%B %d')
                time_str = start.strftime('%I:%M %p')
                end_time_str = end.strftime('%I:%M %p')
                timezone_str = start.strftime('%Z') or 'IST'
                
                slots_text += f"**{i}. {day_name}, {date_str}**\n"
                slots_text += f"   🕐 {time_str} - {end_time_str} {timezone_str}\n\n"
            
            slots_text += f"Please reply with the slot number you prefer (1-{len(slots)}) to book your meeting with **{marketing_name}**."
            
            if person_info.get('specialization'):
                slots_text += f"\n\n💡 *{marketing_name} specializes in: {person_info['specialization']}*"
            
            # Update session
            self.current_session.update({
                'step': 'selecting_slot',
                'marketing_person': person_info,
                'available_slots': [(start.isoformat(), end.isoformat()) for start, end in slots],
                'user_email': user_email
            })
            
            return {
                'success': True,
                'message': slots_text,
                'step': 'selecting_slot',
                'marketing_person': person_info,
                'available_slots': len(slots)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': "❌ Sorry, I encountered an error while processing your selection. Please try again.",
                'error': str(e)
            }
    
    def handle_slot_selection(self, slot_input: str, user_email: str = None) -> Dict:
        """
        Handle the time slot selection and book the meeting
        
        Args:
            slot_input: User's slot selection (should be a number)
            user_email: User's email (optional, can use from session)
            
        Returns:
            Dictionary with booking result
        """
        try:
            # Check session state
            if self.current_session.get('step') != 'selecting_slot':
                return {
                    'success': False,
                    'message': "❌ Please start by selecting a marketing team member first.",
                    'step': 'restart_needed'
                }
            
            # Use email from session if not provided
            if not user_email and 'user_email' in self.current_session:
                user_email = self.current_session['user_email']
            
            # Parse slot selection
            try:
                slot_num = int(slot_input.strip())
            except ValueError:
                available_slots_count = len(self.current_session.get('available_slots', []))
                return {
                    'success': False,
                    'message': f"❌ Please enter a valid slot number (1-{available_slots_count}).",
                    'step': 'selecting_slot'
                }
            
            # Validate slot number
            available_slots = self.current_session.get('available_slots', [])
            if not (1 <= slot_num <= len(available_slots)):
                return {
                    'success': False,
                    'message': f"❌ Invalid slot number. Please choose between 1 and {len(available_slots)}.",
                    'step': 'selecting_slot'
                }
            
            # Get marketing person and slot info
            marketing_person = self.current_session['marketing_person']
            marketing_email = marketing_person['email']
            marketing_name = marketing_person['name']
            
            # Convert slot back to datetime objects
            selected_slot_data = available_slots[slot_num - 1]
            start_time = datetime.fromisoformat(selected_slot_data[0])
            end_time = datetime.fromisoformat(selected_slot_data[1])
            
            # Look up customer name from database
            customer_name = get_customer_name_by_email(user_email)
            if not customer_name:
                # Extract name from email as fallback (e.g., "john.doe@email.com" -> "John Doe")
                email_prefix = user_email.split('@')[0] if user_email else "Customer"
                customer_name = email_prefix.replace('.', ' ').replace('_', ' ').title()
                print(f"⚠️ Using derived name from email: {customer_name}")
            
            # Book the meeting with customer name
            print(f"📅 Booking meeting with {marketing_name} for {customer_name} ({user_email})...")
            
            event_id = self.scheduler.calendar.book_meeting(
                email=marketing_email,
                start=start_time,
                end=end_time,
                subject=f"Meeting with {customer_name}",
                attendees=[user_email, marketing_email],
                user_name=customer_name,
                user_email=user_email,
                marketing_person_email=marketing_email,
                marketing_person_name=marketing_name
            )
            
            if event_id:
                # Format confirmation message
                day_name = start_time.strftime('%A')
                date_str = start_time.strftime('%B %d, %Y')
                time_str = start_time.strftime('%I:%M %p')
                end_time_str = end_time.strftime('%I:%M %p')
                timezone_str = start_time.strftime('%Z') or 'IST'
                
                confirmation_msg = f"🎉 **Meeting Confirmed!**\n\n"
                confirmation_msg += f"📅 **When:** {day_name}, {date_str}\n"
                confirmation_msg += f"🕐 **Time:** {time_str} - {end_time_str} {timezone_str}\n"
                confirmation_msg += f"👤 **With:** {marketing_name}\n"
                confirmation_msg += f"📧 **Email:** {marketing_email}\n\n"
                
                confirmation_msg += f"📧 **Next Steps:**\n"
                confirmation_msg += f"• You'll receive a calendar invitation shortly\n"
                confirmation_msg += f"• {marketing_name} will send meeting connection details\n"
                confirmation_msg += f"• Check your email 15 minutes before the meeting\n\n"
                
                # Send WhatsApp confirmation
                whatsapp_sent = False
                whatsapp_error = None
                if self.whatsapp_enabled and self.whatsapp_service:
                    try:
                        # Get customer phone from database
                        customer_phone = get_customer_phone_by_email(user_email)
                        
                        if customer_phone:
                            print(f"📱 Sending WhatsApp confirmation to {customer_phone}...")
                            whatsapp_sid = self.whatsapp_service.send_meeting_confirmation(
                                recipient_phone=customer_phone,
                                customer_name=customer_name,
                                marketing_person_name=marketing_name,
                                marketing_person_email=marketing_email,
                                meeting_date=f"{day_name}, {date_str}",
                                meeting_time=time_str,
                                meeting_end_time=end_time_str,
                                timezone=timezone_str
                            )
                            
                            if whatsapp_sid:
                                whatsapp_sent = True
                                print(f"✅ WhatsApp confirmation sent! SID: {whatsapp_sid}")
                                confirmation_msg += f"📱 **WhatsApp notification sent to your phone!**\n\n"
                            else:
                                print("⚠️ WhatsApp message could not be sent")
                        else:
                            print(f"⚠️ No phone number found for {user_email}, skipping WhatsApp notification")
                    except Exception as e:
                        whatsapp_error = str(e)
                        print(f"❌ Error sending WhatsApp notification: {e}")
                
                confirmation_msg += f"❓ **Questions?** Reply to the calendar invitation or contact {marketing_name} directly.\n\n"
                confirmation_msg += f"Thank you for choosing our service! 🙏"
                
                # Clear session
                self.current_session = {}
                
                return {
                    'success': True,
                    'message': confirmation_msg,
                    'step': 'booking_confirmed',
                    'event_id': event_id,
                    'whatsapp_sent': whatsapp_sent,
                    'whatsapp_error': whatsapp_error,
                    'meeting_details': {
                        'marketing_person': marketing_name,
                        'email': marketing_email,
                        'datetime': start_time.isoformat(),
                        'duration_hours': (end_time - start_time).seconds // 3600
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f"❌ Sorry, there was an issue booking your meeting with {marketing_name}. Please try again or contact us directly.",
                    'step': 'booking_failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': "❌ Sorry, I encountered an error while booking your meeting. Please try again.",
                'error': str(e)
            }
    
    def get_session_state(self) -> Dict:
        """Get current session state for debugging"""
        return self.current_session.copy()
    
    def reset_session(self):
        """Reset the current session"""
        self.current_session = {}

# Convenience functions for easy integration
def start_marketing_meeting_flow(user_email: str) -> Dict:
    """Start the marketing meeting scheduling flow"""
    scheduler = EnhancedMarketingScheduler()
    return scheduler.start_meeting_request(user_email)

def handle_marketing_person_selection(selection: str, user_email: str) -> Dict:
    """Handle marketing person selection"""
    scheduler = EnhancedMarketingScheduler()
    return scheduler.handle_person_selection(selection, user_email)

def handle_time_slot_selection(selection: str, user_email: str) -> Dict:
    """Handle time slot selection and booking"""
    scheduler = EnhancedMarketingScheduler()
    return scheduler.handle_slot_selection(selection, user_email)

# Test the enhanced scheduler
if __name__ == "__main__":
    print("🧪 TESTING ENHANCED MARKETING SCHEDULER")
    print("=" * 50)
    
    scheduler = EnhancedMarketingScheduler()
    test_user_email = "testcustomer@example.com"
    
    # Test 1: Start meeting request
    print("\n1️⃣ Starting meeting request...")
    result1 = scheduler.start_meeting_request(test_user_email)
    print("Response:", result1['message'][:200] + "..." if len(result1['message']) > 200 else result1['message'])
    
    # Test 2: Select marketing person (simulate user choosing "1")
    print(f"\n2️⃣ Selecting marketing person (choosing 1)...")
    result2 = scheduler.handle_person_selection("1", test_user_email)
    if result2['success']:
        print("✅ Person selection successful")
        print("Available slots:", result2.get('available_slots', 0))
    else:
        print("❌ Person selection failed:", result2['message'])
    
    print(f"\n✅ Enhanced Marketing Scheduler test completed!")
    print(f"Session state: {scheduler.get_session_state()}")
