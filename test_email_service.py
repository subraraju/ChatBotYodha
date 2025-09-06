#!/usr/bin/env python3
"""
Test script to send an email to nagakartheek.ds@gmail.com for verification.
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.email_service import EmailService

def test_email_send():
    """Test sending email to the specified address"""
    
    print("📧 Testing Email Service")
    print("=" * 50)
    
    # Initialize email service
    email_service = EmailService()
    
    if not email_service.is_configured:
        print("❌ Email service is not configured!")
        print("Please update your .env file with actual SMTP settings:")
        print("- SMTP_USERNAME=your_gmail@gmail.com")
        print("- SMTP_PASSWORD=your_gmail_app_password") 
        print("- SMTP_SERVER=smtp.gmail.com")
        print("- SMTP_PORT=587")
        print("- FROM_EMAIL=your_gmail@gmail.com")
        print("\nFor Gmail, you need to:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an App Password")
        print("3. Use the App Password (not your regular password)")
        
        # Let's try to configure it manually for testing
        print("\n🔧 Attempting manual configuration for testing...")
        
        # You can manually set these for testing
        test_email = input("Enter your Gmail address (or press Enter to skip): ").strip()
        if test_email:
            test_password = input("Enter your Gmail App Password (or press Enter to skip): ").strip()
            if test_password:
                email_service.smtp_username = test_email
                email_service.smtp_password = test_password
                email_service.from_email = test_email
                email_service.is_configured = True
                print("✅ Manual configuration applied")
            else:
                print("⏭️ Skipping email test - no credentials provided")
                return False
        else:
            print("⏭️ Skipping email test - no credentials provided")
            return False
    
    print("✅ Email service is configured")
    print(f"SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
    print(f"From Email: {email_service.from_email}")
    
    # Test email details
    test_email = "nagakartheek.ds@gmail.com"
    test_name = "Test Recipient"
    session_id = f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    conversation_url = "https://example.com/test-conversation"
    
    print(f"\n📤 Sending test email to: {test_email}")
    print(f"Session ID: {session_id}")
    
    try:
        # Send the email
        success = email_service.send_conversation_summary_email(
            customer_email=test_email,
            customer_name=test_name,
            session_id=session_id,
            conversation_url=conversation_url,
            product_name="Test Product XYZ",
            activity_id=12345
        )
        
        if success:
            print("✅ Email sent successfully!")
            print(f"📧 Please check {test_email} for the test email")
            return True
        else:
            print("❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_email_send():
    """Test direct email sending with simple content"""
    
    print("\n📧 Testing Direct Email Send")
    print("=" * 50)
    
    # Initialize email service
    email_service = EmailService()
    
    if not email_service.is_configured:
        print("❌ Email service is not configured!")
        return False
    
    # Simple test email content
    test_email = "nagakartheek.ds@gmail.com"
    subject = f"Test Email from {email_service.company_name} Chatbot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Test Email from {email_service.company_name} Chatbot</h2>
        <p>Dear Test Recipient,</p>
        <p>This is a test email to verify that the email service is working correctly.</p>
        <p><strong>Test Details:</strong></p>
        <ul>
            <li>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li>From: {email_service.from_email}</li>
            <li>Company: {email_service.company_name}</li>
        </ul>
        <p>If you receive this email, please confirm that the email service is working.</p>
        <br>
        <p>Best regards,<br>
        The {email_service.company_name} Team</p>
    </body>
    </html>
    """
    
    text_content = f"""
    Test Email from {email_service.company_name} Chatbot
    
    Dear Test Recipient,
    
    This is a test email to verify that the email service is working correctly.
    
    Test Details:
    - Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    - From: {email_service.from_email}
    - Company: {email_service.company_name}
    
    If you receive this email, please confirm that the email service is working.
    
    Best regards,
    The {email_service.company_name} Team
    """
    
    try:
        # Send simple test email
        success = email_service._send_email(
            to_email=test_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            print("✅ Direct email sent successfully!")
            print(f"📧 Please check {test_email} for the test email")
            return True
        else:
            print("❌ Failed to send direct email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending direct email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Email Service Test")
    print("==================")
    
    try:
        # Test the conversation summary email
        success1 = test_email_send()
        
        # Test direct email sending
        success2 = test_direct_email_send()
        
        if success1 or success2:
            print("\n✅ At least one email test succeeded!")
            print("📧 Please check nagakartheek.ds@gmail.com for received emails")
        else:
            print("\n❌ All email tests failed")
            print("Please check SMTP configuration in .env file")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
