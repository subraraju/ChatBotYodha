#!/usr/bin/env python3
"""
User-specific timezone configuration for marketing scheduling
"""
import os
from typing import Dict, Optional

# User-specific timezone overrides
USER_TIMEZONE_CONFIG = {
    # Marketing team members - customize as needed
    'nagakartheek.ds@gmail.com': 'Asia/Kolkata',  # IST timezone
    'sarah.marketing@company.co.uk': 'Europe/London',  # GMT/BST
    'john.sales@company.com': 'America/New_York',  # EST/EDT
    'maria.support@company.com': 'Europe/Madrid',  # CET/CEST
    'david.manager@company.com': 'America/Los_Angeles',  # PST/PDT
    
    # Add more marketing team members here as needed
    # 'email@domain.com': 'Timezone/String',
}

# Default business hours configuration (can be overridden per timezone)
BUSINESS_HOURS_CONFIG = {
    'default': {'start': 9, 'end': 17},  # 9 AM - 5 PM
    'Asia/Kolkata': {'start': 9, 'end': 17},  # 9 AM - 5 PM IST
    'Europe/London': {'start': 9, 'end': 17},  # 9 AM - 5 PM GMT/BST
    'America/New_York': {'start': 9, 'end': 17},  # 9 AM - 5 PM EST/EDT
    'America/Los_Angeles': {'start': 9, 'end': 17},  # 9 AM - 5 PM PST/PDT
}

def get_user_timezone_override(email: str) -> Optional[str]:
    """
    Get timezone override for a specific user email
    
    Args:
        email: User's email address
        
    Returns:
        Timezone string if configured, None otherwise
    """
    return USER_TIMEZONE_CONFIG.get(email.lower())

def get_business_hours_for_timezone(timezone_str: str) -> Dict[str, int]:
    """
    Get business hours configuration for a specific timezone
    
    Args:
        timezone_str: Timezone string (e.g., 'Asia/Kolkata')
        
    Returns:
        Dictionary with 'start' and 'end' hours
    """
    return BUSINESS_HOURS_CONFIG.get(timezone_str, BUSINESS_HOURS_CONFIG['default'])

def add_user_timezone(email: str, timezone_str: str) -> None:
    """
    Add or update timezone for a user (for runtime configuration)
    
    Args:
        email: User's email address
        timezone_str: Timezone string
    """
    USER_TIMEZONE_CONFIG[email.lower()] = timezone_str
    print(f"✅ Added timezone override: {email} → {timezone_str}")

def list_configured_users() -> None:
    """Print all configured user timezones"""
    print("🌍 Configured User Timezones:")
    print("-" * 50)
    for email, timezone in USER_TIMEZONE_CONFIG.items():
        print(f"📧 {email:30s} → 🌍 {timezone}")

if __name__ == "__main__":
    list_configured_users()
    
    # Test specific user lookup
    test_email = "nagakartheek.ds@gmail.com"
    override_tz = get_user_timezone_override(test_email)
    print(f"\n🔍 Timezone for {test_email}: {override_tz}")
    
    business_hours = get_business_hours_for_timezone(override_tz or 'default')
    print(f"🕘 Business hours: {business_hours['start']:02d}:00 - {business_hours['end']:02d}:00")
