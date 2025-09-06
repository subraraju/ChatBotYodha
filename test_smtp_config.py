#!/usr/bin/env python3
"""
Simple SMTP configuration test to help diagnose email issues.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    
    print("🔧 SMTP Configuration Test")
    print("=" * 50)
    
    # Get SMTP settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", username)
    
    print(f"SMTP Server: {smtp_server}:{smtp_port}")
    print(f"Username: {username}")
    print(f"From Email: {from_email}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not username or not password:
        print("\n❌ Missing credentials!")
        print("Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
        print("\nFor Gmail:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an App Password")
        print("3. Use: SMTP_USERNAME=youremail@gmail.com")
        print("4. Use: SMTP_PASSWORD=your_16_char_app_password")
        return False
    
    # Test connection
    print(f"\n🔌 Testing connection to {smtp_server}:{smtp_port}...")
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        print("✅ SMTP connection established")
        
        # Start TLS
        server.starttls()
        server.ehlo()
        print("✅ TLS encryption enabled")
        
        # Test authentication
        print("🔐 Testing authentication...")
        server.login(username, password)
        print("✅ Authentication successful!")
        
        server.quit()
        print("✅ Connection closed properly")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Common fixes:")
        print("- Make sure you're using an App Password (not your regular Gmail password)")
        print("- Enable 2-factor authentication first")
        print("- Check that username/password are correct")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Common fixes:")
        print("- Check internet connection")
        print("- Verify SMTP server and port")
        print("- Check firewall settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def send_test_email():
    """Send a test email if connection works"""
    
    print("\n📧 Sending Test Email")
    print("=" * 30)
    
    # Get settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", username)
    
    test_recipient = "nagakartheek.ds@gmail.com"
    
    # Create email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"SMTP Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    msg['From'] = from_email
    msg['To'] = test_recipient
    
    # Email content
    text_content = f"""
SMTP Test Email

This is a test email to verify SMTP configuration is working.

Test Details:
- Sent from: {from_email}
- SMTP Server: {smtp_server}:{smtp_port}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you receive this email, SMTP is configured correctly!
    """
    
    html_content = f"""
    <html>
    <body>
        <h2>SMTP Test Email</h2>
        <p>This is a test email to verify SMTP configuration is working.</p>
        <h3>Test Details:</h3>
        <ul>
            <li><strong>Sent from:</strong> {from_email}</li>
            <li><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</li>
            <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        <p><strong>If you receive this email, SMTP is configured correctly!</strong></p>
    </body>
    </html>
    """
    
    # Attach content
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)
        
        print(f"✅ Test email sent successfully to {test_recipient}")
        print("📧 Please check the inbox for the test email")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

if __name__ == "__main__":
    print("SMTP Configuration and Test Tool")
    print("=================================")
    
    # Test connection first
    connection_ok = test_smtp_connection()
    
    if connection_ok:
        print("\n🎉 SMTP configuration is working!")
        
        # Ask if user wants to send test email
        send_test = input("\nSend test email to nagakartheek.ds@gmail.com? (y/n): ").lower().strip()
        if send_test == 'y':
            send_test_email()
    else:
        print("\n❌ SMTP configuration needs to be fixed")
        print("\nTo fix:")
        print("1. Update your .env file with valid Gmail credentials")
        print("2. Use an App Password (not regular password)")
        print("3. Run this test again")
