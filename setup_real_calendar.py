#!/usr/bin/env python3
"""
Setup script for Real Gmail Calendar + Teams Integration
This script helps you configure the necessary credentials and test the integration
"""
import os
import sys
from pathlib import Path
import subprocess
import json


def check_and_install_packages():
    """Check and install required packages"""
    print("📦 Checking required packages...")
    
    required_packages = [
        "google-auth",
        "google-auth-oauthlib", 
        "google-api-python-client",
        "msal",
        "requests",
        "python-dateutil",
        "pytz",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\\n🔄 Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    
    return True


def setup_google_credentials():
    """Guide user through Google credentials setup"""
    print("\\n🔑 Google Calendar Credentials Setup")
    print("=" * 50)
    
    credentials_path = "credentials.json"
    
    if os.path.exists(credentials_path):
        print(f"✅ Found existing Google credentials: {credentials_path}")
        return True
    
    print("❌ Google credentials not found!")
    print("\\n📋 Follow these steps:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Calendar API")
    print("4. Go to 'Credentials' > 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("5. Choose 'Desktop application'")
    print("6. Download the JSON file")
    print(f"7. Save it as '{credentials_path}' in this directory")
    print("\\n⏳ Waiting for you to complete the setup...")
    
    input("Press Enter after you've placed the credentials.json file...")
    
    if os.path.exists(credentials_path):
        print("✅ Google credentials found!")
        return True
    else:
        print("❌ Credentials still not found. Please check the file path.")
        return False


def setup_azure_credentials():
    """Guide user through Azure credentials setup"""
    print("\\n🔑 Microsoft Azure Credentials Setup")
    print("=" * 50)
    
    env_path = ".env"
    
    if os.path.exists(env_path):
        print(f"✅ Found existing .env file: {env_path}")
        # Check if required variables are present
        with open(env_path, 'r') as f:
            content = f.read()
            if all(var in content for var in ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]):
                print("✅ Azure credentials appear to be configured")
                return True
    
    print("❌ Azure credentials not configured!")
    print("\\n📋 Follow these steps:")
    print("1. Go to Azure Portal: https://portal.azure.com/")
    print("2. Navigate to 'Azure Active Directory' > 'App registrations'")
    print("3. Click 'New registration'")
    print("4. Configure API permissions: Calendars.ReadWrite, OnlineMeetings.ReadWrite")
    print("5. Create a client secret")
    print("6. Note down: Client ID, Client Secret, Tenant ID")
    
    print("\\n📝 Please provide your Azure credentials:")
    client_id = input("Azure Client ID: ").strip()
    client_secret = input("Azure Client Secret: ").strip()
    tenant_id = input("Azure Tenant ID: ").strip()
    
    if not all([client_id, client_secret, tenant_id]):
        print("❌ All credentials are required!")
        return False
    
    # Create/update .env file
    env_content = f"""# Google Calendar API
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json

# Microsoft Teams/Graph API
AZURE_CLIENT_ID={client_id}
AZURE_CLIENT_SECRET={client_secret}
AZURE_TENANT_ID={tenant_id}
AZURE_REDIRECT_URI=http://localhost:8080/callback

# Default Settings
DEFAULT_MEETING_DURATION_MINUTES=60
DEFAULT_TIMEZONE=UTC
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file with Azure credentials")
    return True


def test_google_integration():
    """Test Google Calendar integration"""
    print("\\n🧪 Testing Google Calendar Integration")
    print("=" * 50)
    
    try:
        from google_calendar_integration import GoogleCalendarAdapter
        
        adapter = GoogleCalendarAdapter()
        calendars = adapter.get_calendar_info()
        
        if calendars:
            print("✅ Google Calendar integration working!")
            return True
        else:
            print("⚠️ Google Calendar accessible but no calendars found")
            return True
            
    except Exception as e:
        print(f"❌ Google Calendar test failed: {e}")
        return False


def test_teams_integration():
    """Test Teams integration"""
    print("\\n🧪 Testing Microsoft Teams Integration")
    print("=" * 50)
    
    try:
        from teams_integration import TeamsIntegration
        
        teams = TeamsIntegration()
        print("✅ Microsoft Teams integration initialized!")
        return True
        
    except Exception as e:
        print(f"❌ Teams integration test failed: {e}")
        return False


def update_marketing_scheduler():
    """Update the marketing scheduler to use real calendar integration"""
    print("\\n🔄 Updating Marketing Scheduler")
    print("=" * 50)
    
    scheduler_path = "app/chatbot/marketing_scheduler.py"
    
    if not os.path.exists(scheduler_path):
        print(f"❌ Marketing scheduler not found: {scheduler_path}")
        return False
    
    # Read current content
    with open(scheduler_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "GoogleCalendarAdapter" in content:
        print("✅ Marketing scheduler already configured for real calendar integration")
        return True
    
    # Add import and update initialization
    updated_content = content.replace(
        "class MarketingScheduler:",
        """# Import real calendar integration
try:
    from google_calendar_integration import GoogleCalendarAdapter
    from teams_integration import EnhancedGoogleCalendarAdapter
    REAL_CALENDAR_AVAILABLE = True
except ImportError:
    REAL_CALENDAR_AVAILABLE = False

class MarketingScheduler:"""
    )
    
    # Update the initialization
    updated_content = updated_content.replace(
        "self.calendar = calendar_adapter or MockCalendarAdapter()",
        """# Use real calendar if available, otherwise mock
        if calendar_adapter:
            self.calendar = calendar_adapter
        elif REAL_CALENDAR_AVAILABLE:
            try:
                self.calendar = EnhancedGoogleCalendarAdapter()
                print("✅ Using real Google Calendar + Teams integration")
            except Exception as e:
                print(f"⚠️ Failed to initialize real calendar, using mock: {e}")
                self.calendar = MockCalendarAdapter()
        else:
            self.calendar = MockCalendarAdapter()
            print("⚠️ Real calendar integration not available, using mock")"""
    )
    
    # Write updated content
    with open(scheduler_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Marketing scheduler updated for real calendar integration")
    return True


def create_test_script():
    """Create a comprehensive test script"""
    test_script = """#!/usr/bin/env python3
\"\"\"
Comprehensive test for Gmail Calendar + Teams Integration
\"\"\"
import sys
sys.path.append(".")

from app.chatbot.customer_service_bot import CustomerServiceBot, CustomerSession
from datetime import datetime


def test_real_calendar_integration():
    \"\"\"Test the complete real calendar integration\"\"\"
    print("🧪 Testing Real Calendar Integration with nagakartheek.ds@gmail.com")
    print("=" * 70)

    bot = CustomerServiceBot("TestCorp")
    session = CustomerSession("real_calendar_test")
    
    # Test marketing flow with real email
    print("\\n📞 Step 1: Request marketing meeting")
    response1, session = bot.process_message("I want to schedule a meeting with marketing", session)
    print(f"🤖 {response1}")
    
    print("\\n📧 Step 2: Provide nagakartheek.ds@gmail.com")
    response2, session = bot.process_message("nagakartheek.ds@gmail.com", session)
    print(f"🤖 {response2}")
    
    print("\\n✅ Step 3: Confirm email (should check REAL calendar)")
    response3, session = bot.process_message("yes", session)
    print(f"🤖 {response3}")
    
    if "Available" in response3 or "slots" in response3.lower():
        print("\\n⏰ Step 4: Select a slot")
        response4, session = bot.process_message("1", session)
        print(f"🤖 {response4}")
        
        if "booked" in response4.lower():
            print("\\n✅ SUCCESS: Real calendar integration working!")
            print("📅 A real calendar event should have been created")
            print("🎥 Teams meeting link should be included")
        else:
            print("\\n⚠️ Booking may have failed")
    else:
        print("\\n❌ Calendar slots not showing properly")


if __name__ == "__main__":
    try:
        test_real_calendar_integration()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
"""
    
    with open("test_real_calendar.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_real_calendar.py")


def main():
    """Main setup function"""
    print("🚀 Gmail Calendar + Teams Integration Setup")
    print("=" * 60)
    
    # Step 1: Check packages
    if not check_and_install_packages():
        print("❌ Package installation failed. Please install manually.")
        return
    
    # Step 2: Setup Google credentials
    if not setup_google_credentials():
        print("❌ Google credentials setup failed.")
        return
    
    # Step 3: Setup Azure credentials
    if not setup_azure_credentials():
        print("❌ Azure credentials setup failed.")
        return
    
    # Step 4: Test integrations
    google_ok = test_google_integration()
    teams_ok = test_teams_integration()
    
    if not (google_ok and teams_ok):
        print("⚠️ Some integrations failed. Check your credentials.")
        return
    
    # Step 5: Update marketing scheduler
    if not update_marketing_scheduler():
        print("❌ Failed to update marketing scheduler.")
        return
    
    # Step 6: Create test script
    create_test_script()
    
    print("\\n🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("✅ Google Calendar integration configured")
    print("✅ Microsoft Teams integration configured")
    print("✅ Marketing scheduler updated")
    print("✅ Test script created")
    print("\\n🧪 Next steps:")
    print("1. Run: python test_real_calendar.py")
    print("2. Test with nagakartheek.ds@gmail.com")
    print("3. Check that real calendar events are created")
    print("4. Verify Teams meeting links are included")


if __name__ == "__main__":
    main()
