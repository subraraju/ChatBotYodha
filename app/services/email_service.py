"""Email service for sending notifications to customers."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmailService:
    """Service for sending email notifications to customers."""
    
    def __init__(self):
        """Initialize email service with configuration from environment variables."""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.company_name = os.getenv("COMPANY_NAME", "Contoso")
        
        # Check if email service is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        # Initialize WhatsApp service if available
        self._whatsapp_service = None
        try:
            from .messaging import SMSService
            self._whatsapp_service = SMSService()
        except Exception as e:
            print(f"WhatsApp service not available: {e}")
        
        # Initialize Telegram service if available
        self._telegram_service = None
        try:
            from .messaging import TelegramService
            self._telegram_service = TelegramService()
        except Exception as e:
            print(f"Telegram service not available: {e}")
        
        if not self.is_configured:
            print("⚠️ Email service not configured - missing SMTP credentials")
    
    def send_conversation_summary_email(
        self, 
        customer_email: str, 
        customer_name: str,
        session_id: str,
        conversation_url: str,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> bool:
        """
        Send a conversation summary email to the customer.
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            session_id: Session ID
            conversation_url: URL to the stored conversation
            product_name: Name of the product discussed (optional)
            activity_id: Activity record ID (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            print("❌ Cannot send email - SMTP not configured")
            return False
        
        try:
            # Create email content
            subject = f"Your {self.company_name} Customer Service Conversation Summary"
            
            # Generate email body
            html_body = self._generate_conversation_summary_html(
                customer_name=customer_name,
                session_id=session_id,
                conversation_url=conversation_url,
                product_name=product_name,
                activity_id=activity_id
            )
            
            text_body = self._generate_conversation_summary_text(
                customer_name=customer_name,
                session_id=session_id,
                conversation_url=conversation_url,
                product_name=product_name,
                activity_id=activity_id
            )
            
            # Send email
            success = self._send_email(
                to_email=customer_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body
            )
            
            if success:
                print(f"✅ Conversation summary email sent to {customer_email}")
                return True
            else:
                print(f"❌ Failed to send email to {customer_email}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending conversation summary email: {e}")
            return False
    
    def _generate_conversation_summary_html(
        self, 
        customer_name: str,
        session_id: str,
        conversation_url: str,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> str:
        """Generate HTML email body for conversation summary."""
        
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        product_section = ""
        if product_name:
            product_section = f"""
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                    <strong>Product Discussed:</strong> {product_name}
                </td>
            </tr>
            """
        
        activity_section = ""
        if activity_id:
            activity_section = f"""
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                    <strong>Reference ID:</strong> {activity_id}
                </td>
            </tr>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Conversation Summary - {self.company_name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h1 style="color: #2c3e50; margin: 0;">Thank you for contacting {self.company_name}!</h1>
            </div>
            
            <div style="background-color: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <p>Dear {customer_name},</p>
                
                <p>Thank you for using our customer service chat. Your conversation has been successfully saved and is available for your reference.</p>
                
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <strong>Date:</strong> {current_date}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <strong>Session ID:</strong> {session_id}
                        </td>
                    </tr>
                    {product_section}
                    {activity_section}
                </table>
                
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #2980b9;">📁 Your Conversation Record</h3>
                    <p style="margin: 0;">A complete record of your conversation is available at:</p>
                    <p style="margin: 10px 0 0 0;">
                        <a href="{conversation_url}" style="color: #2980b9; text-decoration: none; font-weight: bold;">
                            Download Conversation Record
                        </a>
                    </p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #27ae60;">What's Next?</h3>
                    <ul>
                        <li>You can reference this conversation using the session ID above</li>
                        <li>If you need further assistance, please don't hesitate to contact us again</li>
                        <li>Our team may follow up if additional action is required</li>
                    </ul>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; text-align: center; color: #666;">
                        <strong>Need more help?</strong><br>
                        Contact us anytime through our customer service chat or call our support line.
                    </p>
                </div>
                
                <p>Best regards,<br>
                <strong>The {self.company_name} Customer Service Team</strong></p>
                
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
            
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_conversation_summary_text(
        self, 
        customer_name: str,
        session_id: str,
        conversation_url: str,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> str:
        """Generate plain text email body for conversation summary."""
        
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        product_line = f"\nProduct Discussed: {product_name}" if product_name else ""
        activity_line = f"\nReference ID: {activity_id}" if activity_id else ""
        
        text_template = f"""
Dear {customer_name},

Thank you for using {self.company_name} customer service chat. Your conversation has been successfully saved and is available for your reference.

CONVERSATION DETAILS:
===================
Date: {current_date}
Session ID: {session_id}{product_line}{activity_line}

YOUR CONVERSATION RECORD:
========================
A complete record of your conversation is available at:
{conversation_url}

WHAT'S NEXT:
===========
- You can reference this conversation using the session ID above
- If you need further assistance, please don't hesitate to contact us again
- Our team may follow up if additional action is required

Need more help?
Contact us anytime through our customer service chat or call our support line.

Best regards,
The {self.company_name} Customer Service Team

---
This is an automated message. Please do not reply to this email.
        """
        
        return text_template.strip()
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        text_body: str, 
        html_body: str
    ) -> bool:
        """
        Send an email with both text and HTML content.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            text_body: Plain text email body
            html_body: HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ SMTP error sending email: {e}")
            return False
    
    def send_conversation_with_content_email(
        self, 
        customer_email: str, 
        customer_name: str,
        session_id: str,
        conversation_messages: list,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> bool:
        """
        Send a conversation summary email with the actual conversation content included.
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            session_id: Session ID
            conversation_messages: List of conversation messages
            product_name: Name of the product discussed (optional)
            activity_id: Activity record ID (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            print("❌ Cannot send email - SMTP not configured")
            return False
        
        try:
            # Create email content
            subject = f"Your {self.company_name} Customer Service Conversation"
            
            # Generate email body with conversation content
            html_body = self._generate_conversation_with_content_html(
                customer_name=customer_name,
                session_id=session_id,
                conversation_messages=conversation_messages,
                product_name=product_name,
                activity_id=activity_id
            )
            
            text_body = self._generate_conversation_with_content_text(
                customer_name=customer_name,
                session_id=session_id,
                conversation_messages=conversation_messages,
                product_name=product_name,
                activity_id=activity_id
            )
            
            # Send email
            success = self._send_email(
                to_email=customer_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body
            )
            
            if success:
                print(f"✅ Conversation email sent to {customer_email}")
            else:
                print(f"❌ Failed to send conversation email to {customer_email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending conversation email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_conversation_with_content_html(
        self, 
        customer_name: str,
        session_id: str,
        conversation_messages: list,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> str:
        """Generate HTML email body with full conversation content."""
        
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        product_section = ""
        if product_name:
            product_section = f"""
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                    <strong>Product Discussed:</strong> {product_name}
                </td>
            </tr>
            """
        
        activity_section = ""
        if activity_id:
            activity_section = f"""
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                    <strong>Reference ID:</strong> {activity_id}
                </td>
            </tr>
            """
        
        # Generate conversation content
        conversation_html = ""
        for message in conversation_messages:
            role = message.role if hasattr(message, 'role') else getattr(message, 'role', 'user')
            content = message.content if hasattr(message, 'content') else str(message)
            timestamp = message.timestamp if hasattr(message, 'timestamp') else None
            
            if role == "user":
                icon = "👤"
                sender = "You"
                style = "background-color: #f8f9fa; border-left: 4px solid #007bff;"
            else:
                icon = "🤖"
                sender = f"Yodha ({self.company_name} Assistant)"
                style = "background-color: #f1f3f4; border-left: 4px solid #28a745;"
            
            time_str = ""
            if timestamp:
                time_str = f"<div style='font-size: 12px; color: #666; margin-top: 5px;'>{timestamp.strftime('%I:%M %p')}</div>"
            
            conversation_html += f"""
            <div style="margin: 15px 0; padding: 15px; {style} border-radius: 8px;">
                <div style="font-weight: bold; color: #333; margin-bottom: 8px;">
                    {icon} {sender}
                </div>
                <div style="color: #444; line-height: 1.5;">
                    {content}
                </div>
                {time_str}
            </div>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your {self.company_name} Conversation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <div style="background-color: #007bff; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">Your {self.company_name} Conversation</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Customer Service Summary</p>
            </div>
            
            <div style="background-color: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
                <p style="margin-top: 0; font-size: 16px;">Dear {customer_name},</p>
                
                <p>Thank you for contacting {self.company_name} customer service. Below is the complete record of your conversation with our assistant Yodha.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <strong>Session ID:</strong> {session_id}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <strong>Date:</strong> {current_date}
                        </td>
                    </tr>
                    {product_section}
                    {activity_section}
                </table>
                
                <h3 style="color: #007bff; margin-top: 30px; margin-bottom: 20px;">Conversation Details</h3>
                
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background-color: #fafbfc;">
                    {conversation_html}
                </div>
                
                <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                    <h4 style="margin-top: 0; color: #155724;">Need Additional Help?</h4>
                    <p style="margin-bottom: 0;">If you have any follow-up questions or need further assistance, please don't hesitate to contact us again. We're here to help!</p>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                    <p>Thank you for choosing {self.company_name}!</p>
                    <p style="margin-bottom: 0;">This email was sent from an automated system. Please do not reply to this email.</p>
                </div>
            </div>
            
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_conversation_with_content_text(
        self, 
        customer_name: str,
        session_id: str,
        conversation_messages: list,
        product_name: Optional[str] = None,
        activity_id: Optional[int] = None
    ) -> str:
        """Generate plain text email body with full conversation content."""
        
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        product_line = f"Product Discussed: {product_name}" if product_name else ""
        activity_line = f"Reference ID: {activity_id}" if activity_id else ""
        
        # Generate conversation content
        conversation_text = ""
        for message in conversation_messages:
            role = message.role if hasattr(message, 'role') else getattr(message, 'role', 'user')
            content = message.content if hasattr(message, 'content') else str(message)
            timestamp = message.timestamp if hasattr(message, 'timestamp') else None
            
            if role == "user":
                sender = "You"
            else:
                sender = f"Yodha ({self.company_name} Assistant)"
            
            time_str = ""
            if timestamp:
                time_str = f" [{timestamp.strftime('%I:%M %p')}]"
            
            conversation_text += f"{sender}; {time_str}; {content}\n"
        
        text_template = f"""
Your {self.company_name} Conversation Summary

Dear {customer_name},

Thank you for contacting {self.company_name} customer service. Below is the complete record of your conversation with our assistant Yodha.

CONVERSATION DETAILS:
Session ID: {session_id}; Date: {current_date}; {product_line}; {activity_line}

CONVERSATION TRANSCRIPT:
{"=" * 60}
{conversation_text}

NEED ADDITIONAL HELP?
If you have any follow-up questions or need further assistance, please don't hesitate to contact us again. We're here to help!

Thank you for choosing {self.company_name}!

---
This email was sent from an automated system. Please do not reply to this email.
        """.strip()
        
        return text_template

    def test_email_configuration(self) -> bool:
        """
        Test email configuration by sending a test email to the configured sender.
        
        Returns:
            True if test email sent successfully, False otherwise
        """
        if not self.is_configured:
            print("❌ Email service not configured")
            return False
        
        try:
            test_subject = f"{self.company_name} Email Service Test"
            test_body = f"""
This is a test email from the {self.company_name} customer service system.

Email service is configured and working correctly.

Test performed on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
            """.strip()
            
            success = self._send_email(
                to_email=self.from_email,
                subject=test_subject,
                text_body=test_body,
                html_body=f"<html><body><pre>{test_body}</pre></body></html>"
            )
            
            if success:
                print(f"✅ Test email sent successfully to {self.from_email}")
            else:
                print(f"❌ Failed to send test email")
            
            return success
            
        except Exception as e:
            print(f"❌ Error testing email configuration: {e}")
            return False
        
    def send_whatsapp_notification(
        self, 
        phone_number: str, 
        customer_name: str = "Customer"
    ) -> bool:
        """
        Send WhatsApp notification that an email has been sent.
        
        Args:
            phone_number: Customer's WhatsApp number (with country code)
            customer_name: Customer's name for personalization
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self._whatsapp_service or not self._whatsapp_service.is_whatsapp_configured:
            print("⚠️ WhatsApp service not configured")
            return False
        
        try:
            message_sid = self._whatsapp_service.send_email_notification_whatsapp(
                recipient_phone=phone_number,
                customer_name=customer_name
            )
            
            if message_sid:
                print(f"✅ WhatsApp notification sent successfully: {message_sid}")
                return True
            else:
                print("❌ Failed to send WhatsApp notification")
                return False
        except Exception as e:
            print(f"❌ Error sending WhatsApp notification: {str(e)}")
            return False
    
    def send_telegram_notification(
        self, 
        chat_id: str, 
        customer_name: str = "Customer"
    ) -> bool:
        """
        Send Telegram notification that an email has been sent.
        
        Args:
            chat_id: Customer's Telegram chat ID
            customer_name: Customer's name for personalization
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self._telegram_service or not self._telegram_service.is_configured:
            print("⚠️ Telegram service not configured")
            return False
        
        try:
            success = self._telegram_service.send_email_notification_telegram(
                chat_id=chat_id,
                customer_name=customer_name
            )
            
            if success:
                print(f"✅ Telegram notification sent successfully to chat: {chat_id}")
                return True
            else:
                print("❌ Failed to send Telegram notification")
                return False
        except Exception as e:
            print(f"❌ Error sending Telegram notification: {str(e)}")
            return False


def test_email_service():
    """Test the email service functionality."""
    print("🧪 Testing Email Service")
    
    email_service = EmailService()
    
    if not email_service.is_configured:
        print("⚠️ Email service not configured - set SMTP_USERNAME and SMTP_PASSWORD environment variables")
        return False
    
    # Test configuration
    config_test = email_service.test_email_configuration()
    
    # Test conversation summary email
    summary_test = email_service.send_conversation_summary_email(
        customer_email=email_service.from_email,
        customer_name="Test User",
        session_id="test-session-123",
        conversation_url="https://example.com/conversation.json",
        product_name="Test Product",
        activity_id=12345
    )
    
    print(f"✅ Email configuration test: {'PASS' if config_test else 'FAIL'}")
    print(f"✅ Conversation summary test: {'PASS' if summary_test else 'FAIL'}")
    
    return config_test and summary_test


if __name__ == "__main__":
    test_email_service()
