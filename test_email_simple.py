#!/usr/bin/env python3
"""
Simple email test script to verify email functionality.
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.email_service import EmailService

def test_email_basic():
    """Basic email test"""
    
    print("📧 Basic Email Service Test")
    print("=" * 50)
    
    # Initialize email service
    email_service = EmailService()
    
    print(f"SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
    print(f"Username: {email_service.smtp_username}")
    print(f"From Email: {email_service.from_email}")
    print(f"Is Configured: {email_service.is_configured}")
    
    if not email_service.is_configured:
        print("\n❌ Email service is not configured!")
        print("To configure email, update your .env file:")
        print("SMTP_USERNAME=your_email@gmail.com")
        print("SMTP_PASSWORD=your_app_password")
        return False
    
    # Test sending email
    test_email = "nagakartheek.ds@gmail.com"
    test_name = "Test User"
    session_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    conversation_url = "https://example.com/test-conversation"
    
    print(f"\n📤 Attempting to send email to: {test_email}")
    
    try:
        success = email_service.send_conversation_summary_email(
            customer_email=test_email,
            customer_name=test_name,
            session_id=session_id,
            conversation_url=conversation_url,
            product_name="Test Product",
            activity_id=123
        )
        
        if success:
            print("✅ Email sent successfully!")
            print(f"📧 Please check {test_email} for the email")
            return True
        else:
            print("❌ Email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_email():
    """Test direct email sending"""
    
    print("\n📧 Direct Email Test")
    print("=" * 40)
    
    email_service = EmailService()
    
    if not email_service.is_configured:
        print("❌ Email service not configured")
        return False
    
    # Simple email content
    test_email = "nagakartheek.ds@gmail.com"
    subject = f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    text_body = f"""
Test Email from {email_service.company_name} Chatbot

This is a test email to verify email functionality.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
From: {email_service.from_email}

If you receive this, the email service is working!

Best regards,
The {email_service.company_name} Team
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>Test Email from {email_service.company_name} Chatbot</h2>
        <p>This is a test email to verify email functionality.</p>
        <p><strong>Details:</strong></p>
        <ul>
            <li>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li>From: {email_service.from_email}</li>
        </ul>
        <p>If you receive this, the email service is working!</p>
        <br>
        <p>Best regards,<br>The {email_service.company_name} Team</p>
    </body>
    </html>
    """
    
    try:
        success = email_service._send_email(
            to_email=test_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
        
        if success:
            print("✅ Direct email sent successfully!")
            return True
        else:
            print("❌ Direct email failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Email Service Test")
    print("==================")
    
    # Test basic email functionality
    success1 = test_email_basic()
    
    # Test direct email
    success2 = test_direct_email()
    
    if success1 or success2:
        print("\n✅ Email test(s) successful!")
        print("📧 Please check nagakartheek.ds@gmail.com")
    else:
        print("\n❌ All email tests failed")
        print("Please configure SMTP settings in .env file")
