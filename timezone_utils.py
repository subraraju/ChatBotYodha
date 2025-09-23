#!/usr/bin/env python3
"""
Timezone-aware scheduling utilities for marketing meetings
"""
import os
import pytz
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from googleapiclient.discovery import build
import requests

try:
    from user_timezone_config import get_user_timezone_override, get_business_hours_for_timezone
except ImportError:
    # Fallback if config not available
    def get_user_timezone_override(email):
        return None
    def get_business_hours_for_timezone(timezone_str):
        return {'start': 9, 'end': 17}


class TimezoneManager:
    """Manages timezone detection and conversion for marketing scheduling"""
    
    # Common timezone mappings for major cities
    COMMON_TIMEZONES = {
        # US Timezones
        'eastern': 'America/New_York',
        'central': 'America/Chicago', 
        'mountain': 'America/Denver',
        'pacific': 'America/Los_Angeles',
        
        # European Timezones
        'london': 'Europe/London',
        'paris': 'Europe/Paris',
        'berlin': 'Europe/Berlin',
        'rome': 'Europe/Rome',
        'madrid': 'Europe/Madrid',
        
        # Asian Timezones
        'tokyo': 'Asia/Tokyo',
        'hong_kong': 'Asia/Hong_Kong',
        'singapore': 'Asia/Singapore',
        'mumbai': 'Asia/Kolkata',
        'dubai': 'Asia/Dubai',
        
        # Others
        'sydney': 'Australia/Sydney',
        'toronto': 'America/Toronto',
    }
    
    @staticmethod
    def detect_timezone_from_email(email: str) -> Optional[str]:
        """
        Attempt to detect timezone from email domain or patterns
        This is a heuristic approach - in production you might want to ask users
        """
        email_lower = email.lower()
        
        # Specific pattern matching (more granular)
        if 'india' in email_lower or '.in' in email_lower:
            return 'Asia/Kolkata'  # India Standard Time
        elif any(domain in email_lower for domain in ['.uk', '.co.uk', 'london', 'britain']):
            return 'Europe/London'  # GMT/BST
        elif any(domain in email_lower for domain in ['.de', 'berlin', 'germany']):
            return 'Europe/Berlin'  # CET/CEST
        elif any(domain in email_lower for domain in ['.fr', 'paris', 'france']):
            return 'Europe/Paris'   # CET/CEST
        elif '.au' in email_lower or 'australia' in email_lower:
            return 'Australia/Sydney'  # AEST/AEDT
        elif '.jp' in email_lower or 'japan' in email_lower:
            return 'Asia/Tokyo'  # JST
        elif '.ca' in email_lower or 'canada' in email_lower:
            return 'America/Toronto'  # Eastern Canada
        
        # For common Gmail and other domains, try to infer from username patterns
        if 'gmail.com' in email_lower:
            username = email_lower.split('@')[0]
            
            # Look for geographic indicators in username
            if any(indicator in username for indicator in ['india', 'mumbai', 'delhi', 'bangalore']):
                return 'Asia/Kolkata'
            elif any(indicator in username for indicator in ['london', 'uk', 'britain']):
                return 'Europe/London'
            elif any(indicator in username for indicator in ['tokyo', 'japan']):
                return 'Asia/Tokyo'
            # Add more patterns as needed
        
        # For generic domains, default to US Eastern (most common for business)
        if any(domain in email_lower for domain in ['.com', '.org', '.net']) and not any(x in email_lower for x in ['.co.', '.com.au', '.com.in']):
            return 'America/New_York'  # Assume US Eastern for generic domains
        
        # Default to None if no match (will be handled upstream)
        return None
    
    @staticmethod
    def get_timezone_from_calendar_settings(service, email: str) -> Optional[str]:
        """
        Try to get timezone from Google Calendar settings
        """
        try:
            # Try to get the user's calendar settings
            settings = service.settings().list().execute()
            
            for setting in settings.get('items', []):
                if setting.get('id') == 'timezone':
                    timezone = setting.get('value')
                    print(f"🌍 Detected timezone from calendar settings: {timezone}")
                    return timezone
                    
        except Exception as e:
            print(f"⚠️ Could not get calendar timezone: {e}")
        
        return None
    
    @staticmethod 
    def get_user_timezone(service, email: str) -> str:
        """
        Get the best guess for user's timezone
        
        Args:
            service: Google Calendar service object
            email: User's email address
            
        Returns:
            Timezone string (defaults to detected or UTC)
        """
        # Method 0: Check user-specific timezone override first
        override_tz = get_user_timezone_override(email)
        if override_tz:
            print(f"🌍 Using configured timezone override for {email}: {override_tz}")
            return override_tz
        
        # Method 1: Try to get from calendar settings
        calendar_tz = TimezoneManager.get_timezone_from_calendar_settings(service, email)
        if calendar_tz:
            return calendar_tz
        
        # Method 2: Try email-based detection
        email_tz = TimezoneManager.detect_timezone_from_email(email)
        if email_tz:
            print(f"🌍 Estimated timezone from email pattern: {email_tz}")
            return email_tz
        
        # Method 3: Default to UTC
        print(f"⚠️ Could not detect timezone for {email}, using UTC")
        return 'UTC'
    
    @staticmethod
    def convert_business_hours_to_timezone(
        business_start_hour: int,
        business_end_hour: int, 
        user_timezone_str: str,
        target_date: datetime
    ) -> tuple:
        """
        Convert business hours from local time to user's timezone
        
        Args:
            business_start_hour: Start hour (e.g., 9 for 9 AM)
            business_end_hour: End hour (e.g., 17 for 5 PM) 
            user_timezone_str: User's timezone string
            target_date: Date to calculate for
            
        Returns:
            (adjusted_start_hour, adjusted_end_hour) in user's timezone
        """
        try:
            user_tz = pytz.timezone(user_timezone_str)
            
            # Create datetime objects for business hours in user's timezone
            business_start = user_tz.localize(
                target_date.replace(hour=business_start_hour, minute=0, second=0, microsecond=0)
            )
            business_end = user_tz.localize(
                target_date.replace(hour=business_end_hour, minute=0, second=0, microsecond=0)
            )
            
            print(f"🕘 Business hours in {user_timezone_str}: {business_start.strftime('%H:%M')} - {business_end.strftime('%H:%M')}")
            
            return business_start_hour, business_end_hour
            
        except Exception as e:
            print(f"⚠️ Timezone conversion error: {e}")
            return business_start_hour, business_end_hour
    
    @staticmethod
    def create_timezone_aware_datetime(
        date: datetime,
        hour: int,
        timezone_str: str
    ) -> datetime:
        """
        Create a timezone-aware datetime object
        
        Args:
            date: Base date
            hour: Hour in the timezone
            timezone_str: Timezone string
            
        Returns:
            Timezone-aware datetime object
        """
        try:
            tz = pytz.timezone(timezone_str)
            local_dt = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            return tz.localize(local_dt)
        except Exception as e:
            print(f"⚠️ Error creating timezone-aware datetime: {e}")
            # Fallback to UTC
            utc_dt = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            return pytz.UTC.localize(utc_dt)


def test_timezone_detection():
    """Test timezone detection functionality"""
    print("🌍 Testing Timezone Detection")
    print("=" * 50)
    
    test_emails = [
        "nagakartheek.ds@gmail.com",  # Should detect India
        "john.doe@company.co.uk",     # Should detect UK
        "marie@company.fr",           # Should detect France
        "hans@company.de",            # Should detect Germany
        "user@example.com",           # Should detect US Eastern
        "test@company.com.au",        # Should detect Australia
    ]
    
    tm = TimezoneManager()
    
    for email in test_emails:
        detected_tz = tm.detect_timezone_from_email(email)
        print(f"📧 {email:25s} → 🌍 {detected_tz}")
        
        if detected_tz:
            tz = pytz.timezone(detected_tz)
            current_time = datetime.now(tz)
            print(f"   Current time in {detected_tz}: {current_time.strftime('%H:%M %Z')}")
        print()


def test_business_hours_conversion():
    """Test business hours conversion to different timezones"""
    print("\n🕘 Testing Business Hours Timezone Conversion")
    print("=" * 50)
    
    business_start = 9   # 9 AM
    business_end = 17    # 5 PM
    test_date = datetime.now()
    
    timezones_to_test = [
        'America/New_York',  # US Eastern
        'Europe/London',     # UK
        'Asia/Kolkata',      # India
        'Asia/Tokyo',        # Japan
        'Australia/Sydney',  # Australia
    ]
    
    tm = TimezoneManager()
    
    print(f"Base business hours: {business_start}:00 - {business_end}:00")
    print()
    
    for tz_str in timezones_to_test:
        start, end = tm.convert_business_hours_to_timezone(
            business_start, business_end, tz_str, test_date
        )
        
        # Show what time it would be in that timezone
        tz = pytz.timezone(tz_str)
        now_in_tz = datetime.now(tz)
        
        print(f"🌍 {tz_str:20s}: {start:2d}:00 - {end:2d}:00 (Current: {now_in_tz.strftime('%H:%M %Z')})")


if __name__ == "__main__":
    test_timezone_detection()
    test_business_hours_conversion()
