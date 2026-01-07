import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import os
import markdown
from jinja2 import Template
from dotenv import load_dotenv
from typing import List
from app.models.pydantic_models import ChatSession

load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")

        if not self.email_username or not self.email_password:
            raise ValueError("Email credentials not found in environment variables")

    def format_chat_for_email(self, session: ChatSession) -> str:
        """Format chat session as HTML for email"""
        template = Template(
            """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chat-header { background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
                .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
                .user-message { background-color: #e3f2fd; text-align: right; }
                .assistant-message { background-color: #f5f5f5; }
                .timestamp { font-size: 0.8em; color: #666; }
            </style>
        </head>
        <body>
            <div class="chat-header">
                <h2>Chat Session Summary</h2>
                <p><strong>Session ID:</strong> {{ session.session_id }}</p>
                <p><strong>Customer:</strong> {{ session.customer_email }}</p>
                <p><strong>Date:</strong> {{ session.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                <p><strong>Messages:</strong> {{ session.messages|length }}</p>
            </div>
            
            <h3>Conversation:</h3>
            {% for message in session.messages %}
            <div class="message {{ 'user-message' if message.role == 'user' else 'assistant-message' }}">
                <strong>{{ message.role.title() }}:</strong> {{ message.content }}
                <div class="timestamp">{{ message.timestamp.strftime('%H:%M:%S') }}</div>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        )

        return template.render(session=session)

    def send_chat_summary(
        self, session: ChatSession, recipient_email: str, subject: str = None
    ):
        """Send chat summary via email"""
        if not subject:
            subject = f"Chat Session Summary - {session.session_id}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.email_username
        msg["To"] = recipient_email

        # Create HTML content
        html_content = self.format_chat_for_email(session)
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.email_username, self.email_password)
            server.sendmail(self.email_username, recipient_email, msg.as_string())


class SMSService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Twilio Sandbox default

        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Twilio credentials not found in environment variables")

        self.client = Client(self.account_sid, self.auth_token)
        self.is_whatsapp_configured = bool(self.account_sid and self.auth_token)

    def format_chat_for_sms(self, session: ChatSession, max_length: int = 1500) -> str:
        """Format chat session as text for SMS (with length limit)"""
        summary = f"Chat Summary - {session.session_id}\n"
        summary += f"Customer: {session.customer_email}\n"
        summary += f"Date: {session.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

        conversation = ""
        for message in session.messages:
            line = f"{message.role.title()}: {message.content}\n"
            if len(summary + conversation + line) > max_length:
                conversation += "... (truncated for SMS length limit)"
                break
            conversation += line

        return summary + conversation

    def send_chat_summary(self, session: ChatSession, recipient_phone: str):
        """Send chat summary via SMS"""
        message_body = self.format_chat_for_sms(session)

        message = self.client.messages.create(
            body=message_body, from_=self.phone_number, to=recipient_phone
        )

        return message.sid

    def send_whatsapp_notification(self, recipient_phone: str, message_text: str):
        """Send WhatsApp notification message"""
        if not self.is_whatsapp_configured:
            raise ValueError("WhatsApp service not configured")
        
        # Ensure recipient number has whatsapp: prefix
        if not recipient_phone.startswith("whatsapp:"):
            recipient_phone = f"whatsapp:{recipient_phone}"
        
        try:
            message = self.client.messages.create(
                body=message_text,
                from_=self.whatsapp_number,
                to=recipient_phone
            )
            return message.sid
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return None

    def send_email_notification_whatsapp(self, recipient_phone: str, customer_name: str = "Customer"):
        """Send WhatsApp notification that an email has been sent"""
        message_text = f"""🎯 *Contoso Customer Service*

Hi {customer_name}! 👋

✅ *Email Sent Successfully*

We've just sent you a detailed email with your complete conversation summary. Please check your inbox!

📧 *What's included:*
• Full conversation transcript
• Formatted chat history
• Professional summary

If you don't see the email, please check your spam folder.

Thank you for contacting Contoso! 🚀"""

        return self.send_whatsapp_notification(recipient_phone, message_text)

    def send_meeting_confirmation_whatsapp(
        self, 
        recipient_phone: str, 
        customer_name: str,
        marketing_person_name: str,
        marketing_person_email: str,
        meeting_date: str,
        meeting_time: str,
        meeting_end_time: str,
        timezone: str = "IST"
    ):
        """
        Send WhatsApp notification for meeting confirmation.
        
        Args:
            recipient_phone: Customer's phone number (with or without whatsapp: prefix)
            customer_name: Customer's name
            marketing_person_name: Name of the marketing person
            marketing_person_email: Email of the marketing person
            meeting_date: Meeting date (e.g., "Monday, December 16, 2024")
            meeting_time: Meeting start time (e.g., "10:00 AM")
            meeting_end_time: Meeting end time (e.g., "11:00 AM")
            timezone: Timezone string (e.g., "IST", "EST")
            
        Returns:
            Message SID if successful, None otherwise
        """
        message_text = f"""🎉 *Meeting Confirmed!*

Hi {customer_name}! 👋

Your meeting has been successfully scheduled. Here are the details:

📅 *Date:* {meeting_date}
🕐 *Time:* {meeting_time} - {meeting_end_time} {timezone}
👤 *With:* {marketing_person_name}
📧 *Contact:* {marketing_person_email}

📧 *What's Next:*
• A calendar invitation has been sent to your email
• Meeting connection details will be shared by {marketing_person_name}
• Please check your email 15 minutes before the meeting

❓ *Need to reschedule?*
Reply to the calendar invitation or contact {marketing_person_name} directly.

Thank you for choosing our service! 🙏"""

        return self.send_whatsapp_notification(recipient_phone, message_text)


class WhatsAppService:
    """Dedicated WhatsApp messaging service using Twilio"""
    
    def __init__(self):
        # Support both TWILIO_ACCOUNT_SID and TWILIO_SID (prefer non-placeholder)
        account_sid_1 = os.getenv("TWILIO_ACCOUNT_SID", "")
        account_sid_2 = os.getenv("TWILIO_SID", "")
        
        # Prefer TWILIO_SID if TWILIO_ACCOUNT_SID is a placeholder
        if account_sid_1 and 'your_' not in account_sid_1.lower():
            self.account_sid = account_sid_1
        elif account_sid_2:
            self.account_sid = account_sid_2
        else:
            self.account_sid = account_sid_1  # Will fail validation below
        
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        # Only require account_sid and auth_token for WhatsApp
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio credentials (TWILIO_ACCOUNT_SID/TWILIO_SID, TWILIO_AUTH_TOKEN) not found in environment variables")
        
        # Check for placeholder values
        if 'your_' in self.account_sid.lower() or self.account_sid == 'your_twilio_account_sid':
            raise ValueError("TWILIO_ACCOUNT_SID appears to be a placeholder. Please set real credentials.")
        
        self.client = Client(self.account_sid, self.auth_token)
        self.is_configured = True
        print(f"✅ WhatsApp service initialized with number: {self.whatsapp_number}")
    
    def send_message(self, recipient_phone: str, message_text: str) -> str:
        """
        Send a WhatsApp message.
        
        Args:
            recipient_phone: Phone number (with or without whatsapp: prefix)
            message_text: Message content
            
        Returns:
            Message SID if successful, None otherwise
        """
        # Ensure recipient number has whatsapp: prefix
        if not recipient_phone.startswith("whatsapp:"):
            recipient_phone = f"whatsapp:{recipient_phone}"
        
        # Ensure from number has whatsapp: prefix
        from_number = self.whatsapp_number
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        
        try:
            message = self.client.messages.create(
                body=message_text,
                from_=from_number,
                to=recipient_phone
            )
            print(f"✅ WhatsApp message sent! SID: {message.sid}")
            return message.sid
        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {e}")
            return None
    
    def send_meeting_confirmation(
        self, 
        recipient_phone: str, 
        customer_name: str,
        marketing_person_name: str,
        marketing_person_email: str,
        meeting_date: str,
        meeting_time: str,
        meeting_end_time: str,
        timezone: str = "IST"
    ) -> str:
        """
        Send WhatsApp meeting confirmation.
        
        Returns:
            Message SID if successful, None otherwise
        """
        message_text = f"""🎉 *Meeting Confirmed!*

Hi {customer_name}! 👋

Your meeting has been successfully scheduled. Here are the details:

📅 *Date:* {meeting_date}
🕐 *Time:* {meeting_time} - {meeting_end_time} {timezone}
👤 *With:* {marketing_person_name}
📧 *Contact:* {marketing_person_email}

📧 *What's Next:*
• A calendar invitation has been sent to your email
• Meeting connection details will be shared by {marketing_person_name}
• Please check your email 15 minutes before the meeting

❓ *Need to reschedule?*
Reply to the calendar invitation or contact {marketing_person_name} directly.

Thank you for choosing our service! 🙏"""

        return self.send_message(recipient_phone, message_text)
    
    def send_custom_notification(self, recipient_phone: str, title: str, body: str) -> str:
        """Send a custom WhatsApp notification"""
        message_text = f"""🔔 *{title}*

{body}"""
        return self.send_message(recipient_phone, message_text)

    def send_meeting_notification_to_marketing(
        self, 
        recipient_phone: str, 
        marketing_person_name: str,
        customer_name: str,
        customer_email: str,
        meeting_date: str,
        meeting_time: str,
        meeting_end_time: str,
        timezone: str = "IST"
    ) -> str:
        """
        Send WhatsApp notification to marketing person about a new meeting.
        
        Returns:
            Message SID if successful, None otherwise
        """
        message_text = f"""📅 *New Meeting Scheduled!*

Hi {marketing_person_name}! 👋

You have a new meeting request. Here are the details:

📅 *Date:* {meeting_date}
🕐 *Time:* {meeting_time} - {meeting_end_time} {timezone}
👤 *Customer:* {customer_name}
📧 *Email:* {customer_email}

📋 *Action Required:*
• Check your calendar for the meeting invitation
• Prepare for the meeting
• Contact the customer if needed: {customer_email}

Have a great meeting! 🚀"""

        return self.send_message(recipient_phone, message_text)


class TelegramService:
    """Service for sending Telegram notifications"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.is_configured = bool(self.bot_token)
        
        if self.is_configured:
            try:
                import telegram
                self.bot = telegram.Bot(token=self.bot_token)
            except ImportError:
                print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot==20.7")
                self.is_configured = False
            except Exception as e:
                print(f"⚠️ Telegram bot initialization failed: {e}")
                self.is_configured = False
        else:
            print("⚠️ Telegram service not configured - missing TELEGRAM_BOT_TOKEN")
    
    async def send_message(self, chat_id: str, message: str, parse_mode: str = "Markdown"):
        """Send a message to Telegram chat"""
        if not self.is_configured:
            raise ValueError("Telegram service not configured")
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    def send_message_sync(self, chat_id: str, message: str):
        """Synchronous wrapper for sending Telegram messages
        
        Creates a fresh bot instance for each call to avoid event loop issues
        when called multiple times from synchronous code.
        """
        if not self.is_configured:
            print("⚠️ Telegram service not configured")
            return False
        
        try:
            import asyncio
            from telegram import Bot
            
            async def _send():
                # Create fresh bot instance for each call to avoid closed loop issues
                bot = Bot(token=self.bot_token)
                async with bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
            
            # Use asyncio.run() which properly manages the event loop lifecycle
            asyncio.run(_send())
            return True
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    def send_email_notification_telegram(self, chat_id: str, customer_name: str = "Customer"):
        """Send Telegram notification that an email has been sent"""
        message_text = f"""🎯 *Contoso Customer Service*

Hi {customer_name}! 👋

✅ *Email Sent Successfully*

We've just sent you a detailed email with your complete conversation summary\\. Please check your inbox\\!

📧 *What's included:*
• Full conversation transcript
• Formatted chat history  
• Professional summary

If you don't see the email, please check your spam folder\\.

Thank you for contacting Contoso\\! 🚀"""

        return self.send_message_sync(chat_id, message_text)

    def send_meeting_confirmation(
        self,
        chat_id: int,
        customer_name: str,
        marketing_person_name: str,
        marketing_person_email: str,
        meeting_date: str,
        meeting_time: str,
        meeting_end_time: str,
        timezone: str = "IST"
    ) -> bool:
        """
        Send Telegram meeting confirmation to customer.
        
        Args:
            chat_id: Telegram chat ID (integer)
            customer_name: Customer's name
            marketing_person_name: Name of the professional
            marketing_person_email: Email of the professional
            meeting_date: Meeting date string
            meeting_time: Meeting start time
            meeting_end_time: Meeting end time
            timezone: Timezone string
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Escape special characters for Telegram MarkdownV2
        message_text = f"""🎉 *Meeting Confirmed\\!*

Hi {self._escape_markdown(customer_name)}\\! 👋

Your meeting has been successfully scheduled\\.

📅 *Date:* {self._escape_markdown(meeting_date)}
🕐 *Time:* {self._escape_markdown(meeting_time)} \\- {self._escape_markdown(meeting_end_time)} {self._escape_markdown(timezone)}
👤 *With:* {self._escape_markdown(marketing_person_name)}
📧 *Contact:* {self._escape_markdown(marketing_person_email)}

📧 *What's Next:*
• Calendar invitation sent to your email
• Meeting details shared by {self._escape_markdown(marketing_person_name)}
• Check email 15 minutes before meeting

❓ *Need to reschedule?*
Reply to calendar invitation or contact {self._escape_markdown(marketing_person_name)} directly\\.

Thank you for choosing our service\\! 🙏"""

        return self.send_message_sync(str(chat_id), message_text)

    def send_meeting_notification_to_professional(
        self,
        chat_id: int,
        professional_name: str,
        customer_name: str,
        customer_email: str,
        meeting_date: str,
        meeting_time: str,
        meeting_end_time: str,
        timezone: str = "IST"
    ) -> bool:
        """
        Send Telegram meeting notification to marketing/business professional.
        
        Args:
            chat_id: Telegram chat ID (integer)
            professional_name: Professional's name
            customer_name: Customer's name
            customer_email: Customer's email
            meeting_date: Meeting date string
            meeting_time: Meeting start time
            meeting_end_time: Meeting end time
            timezone: Timezone string
            
        Returns:
            True if sent successfully, False otherwise
        """
        message_text = f"""📅 *New Meeting Scheduled\\!*

Hi {self._escape_markdown(professional_name)}\\! 👋

You have a new meeting scheduled\\.

📅 *Date:* {self._escape_markdown(meeting_date)}
🕐 *Time:* {self._escape_markdown(meeting_time)} \\- {self._escape_markdown(meeting_end_time)} {self._escape_markdown(timezone)}
👤 *Customer:* {self._escape_markdown(customer_name)}
📧 *Email:* {self._escape_markdown(customer_email)}

📋 *Action Required:*
• Check your calendar for invitation
• Prepare for the meeting
• Contact customer if needed

Have a great meeting\\! 🚀"""

        return self.send_message_sync(str(chat_id), message_text)

    def _escape_markdown(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2"""
        if not text:
            return ""
        # Characters that need escaping in MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text


class MessageFormatter:
    """Utility class for formatting messages in different formats"""

    @staticmethod
    def to_markdown(session: ChatSession) -> str:
        """Convert chat session to Markdown format"""
        markdown_content = f"""# Chat Session Summary

**Session ID:** {session.session_id}  
**Customer:** {session.customer_email}  
**Date:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Messages:** {len(session.messages)}

## Conversation

"""

        for message in session.messages:
            markdown_content += f"### {message.role.title()}\n"
            markdown_content += f"*{message.timestamp.strftime('%H:%M:%S')}*\n\n"
            markdown_content += f"{message.content}\n\n"

        return markdown_content

    @staticmethod
    def to_plain_text(session: ChatSession) -> str:
        """Convert chat session to plain text format"""
        text_content = f"Chat Session Summary\n"
        text_content += f"{'='*50}\n\n"
        text_content += f"Session ID: {session.session_id}\n"
        text_content += f"Customer: {session.customer_email}\n"
        text_content += f"Date: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        text_content += f"Messages: {len(session.messages)}\n\n"
        text_content += f"Conversation:\n"
        text_content += f"{'-'*30}\n\n"

        for message in session.messages:
            text_content += f"[{message.timestamp.strftime('%H:%M:%S')}] {message.role.title()}: {message.content}\n\n"

        return text_content


# Initialize services with error handling
try:
    email_service = EmailService()
    print("Email service initialized successfully")
except Exception as e:
    email_service = None
    print(f"Email service initialization failed: {e}")

try:
    sms_service = SMSService()
    print("SMS service initialized successfully")
except Exception as e:
    sms_service = None
    print(f"SMS service initialization failed: {e}")

try:
    telegram_service = TelegramService()
    print("Telegram service initialized successfully" if telegram_service.is_configured else "Telegram service available but not configured")
except Exception as e:
    telegram_service = None
    print(f"Telegram service initialization failed: {e}")

try:
    whatsapp_service = WhatsAppService()
except Exception as e:
    whatsapp_service = None
    print(f"WhatsApp service initialization skipped: {e}")
