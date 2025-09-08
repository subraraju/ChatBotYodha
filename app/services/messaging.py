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
        """Synchronous wrapper for sending Telegram messages"""
        if not self.is_configured:
            print("⚠️ Telegram service not configured")
            return False
        
        try:
            import asyncio
            import telegram
            
            async def _send():
                await self.send_message(chat_id, message)
            
            # Run in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_send())
            loop.close()
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
