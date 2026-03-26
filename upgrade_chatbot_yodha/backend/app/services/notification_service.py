"""
Unified notification service — Email (SMTP), WhatsApp (Twilio), Telegram.

Each channel is optional; if credentials are missing it logs and returns False.

Usage:
    from app.services.notification_service import notification_service
    await notification_service.send_email(to, subject, html_body)
    await notification_service.send_whatsapp(phone, message)
    await notification_service.send_telegram(chat_id, message)
"""

import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# Optional deps
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None  # type: ignore

try:
    from telegram import Bot as TelegramBot
except ImportError:
    TelegramBot = None  # type: ignore


# ── HTML helpers ──────────────────────────────────────────────────────

def _conversation_html(
    customer_name: str,
    session_id: str,
    messages: List[Dict[str, str]],
    product_name: Optional[str] = None,
) -> str:
    """Build a styled HTML email with the full conversation."""
    rows = ""
    for m in messages:
        role = m.get("role", "user")
        bg = "#d1ecf1" if role == "user" else "#d4edda"
        label = customer_name if role == "user" else settings.COMPANY_NAME
        rows += (
            f'<tr><td style="background:{bg};padding:8px;border-radius:6px;">'
            f"<b>{label}</b><br>{m.get('content','')}</td></tr>"
        )

    subject_line = f"Conversation summary — {product_name}" if product_name else "Conversation summary"
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:640px;margin:auto;">
    <h2>{subject_line}</h2>
    <p>Session: <code>{session_id}</code></p>
    <table style="width:100%;border-collapse:separate;border-spacing:0 6px;">
    {rows}
    </table>
    <hr><p style="color:#888;font-size:12px;">{settings.COMPANY_NAME} Chatbot</p>
    </body></html>
    """


def _format_meeting_datetime(start_iso: str, end_iso: str) -> Dict[str, str]:
    """Parse ISO datetime strings → human-readable date, time, and day name."""
    try:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
    except (ValueError, TypeError):
        return {"date": start_iso, "time": f"{start_iso} - {end_iso}", "day_name": ""}

    tz_abbr = settings.MEETING_TIMEZONE.split("/")[-1] if "/" in settings.MEETING_TIMEZONE else settings.MEETING_TIMEZONE
    day_name = start_dt.strftime("%A")
    date_str = start_dt.strftime(f"%A, %B {start_dt.day}, %Y")
    time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')} {tz_abbr}"
    return {"date": date_str, "time": time_str, "day_name": day_name}


def _build_whatsapp_meeting_msg(
    recipient_name: str,
    other_party_name: str,
    other_party_email: str,
    start_iso: str,
    end_iso: str,
    requester_email: str,
    is_for_requester: bool = True,
) -> str:
    """Build the emoji-rich WhatsApp meeting confirmation message."""
    dt = _format_meeting_datetime(start_iso, end_iso)

    if is_for_requester:
        return (
            f"\U0001f389 Meeting Confirmed!\n\n"
            f"Hi {recipient_name}!\n\n"
            f"Your meeting has been successfully scheduled. Here are the details:\n\n"
            f"\U0001f4c5 Date: {dt['date']}\n"
            f"\U0001f550 Time: {dt['time']}\n"
            f"\U0001f464 With: {other_party_name}\n"
            f"\U0001f4e7 Contact: {other_party_email}\n\n"
            f"\U0001f4e7 What's Next:\n"
            f"\u2022 A calendar invitation has been sent to your email\n"
            f"\u2022 Meeting connection details will be shared by {other_party_name}\n"
            f"\u2022 Please check your email 15 minutes before the meeting\n\n"
            f"\u2753 Need to reschedule?\n"
            f"Reply to the calendar invitation or contact {other_party_name} directly.\n\n"
            f"Thank you for choosing our service!"
        )
    else:
        return (
            f"\U0001f389 New Meeting Scheduled!\n\n"
            f"Hi {recipient_name}!\n\n"
            f"A new meeting has been scheduled for you. Here are the details:\n\n"
            f"\U0001f4c5 Date: {dt['date']}\n"
            f"\U0001f550 Time: {dt['time']}\n"
            f"\U0001f464 With: {other_party_name}\n"
            f"\U0001f4e7 Contact: {requester_email}\n\n"
            f"\U0001f4e7 What's Next:\n"
            f"\u2022 A calendar invitation has been sent to all attendees\n"
            f"\u2022 Please share meeting connection details with {other_party_name}\n"
            f"\u2022 Check your email for the calendar invite\n\n"
            f"\u2753 Need to reschedule?\n"
            f"Update the calendar invitation or contact {other_party_name} directly.\n\n"
            f"— {settings.COMPANY_NAME}"
        )


def _meeting_email_html(
    recipient_name: str,
    customer_first: str,
    customer_last: str,
    customer_email: str,
    marketer_first: str,
    marketer_last: str,
    marketer_email: str,
    start_iso: str,
    end_iso: str,
    organizer_name: str,
    organizer_email: str,
    organizer_phone: str,
) -> str:
    """Build a professional HTML email for meeting confirmation."""
    dt = _format_meeting_datetime(start_iso, end_iso)
    customer_full = f"{customer_first} {customer_last}".strip()
    marketer_full = f"{marketer_first} {marketer_last}".strip()

    return f"""
    <html>
    <body style="font-family: Arial, Helvetica, sans-serif; max-width: 640px; margin: auto; color: #333;">
      <div style="background: #0078d4; color: #fff; padding: 20px 24px; border-radius: 8px 8px 0 0;">
        <h2 style="margin: 0; font-size: 22px;">&quot;Customer Meeting - {settings.COMPANY_NAME}&quot; Confirmation</h2>
      </div>

      <div style="border: 1px solid #ddd; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <tr>
            <td style="padding: 10px 0; font-weight: bold; width: 100px; vertical-align: top; color: #555;">When</td>
            <td style="padding: 10px 0;">
              <strong>{dt['date']}</strong><br>
              {dt['time']}<br>
              <span style="color: #888;">({settings.MEETING_TIMEZONE})</span>
            </td>
          </tr>
          <tr>
            <td style="padding: 10px 0; font-weight: bold; vertical-align: top; color: #555;">Notes</td>
            <td style="padding: 10px 0; line-height: 1.6;">
              Professional Meeting - Customer Meeting - {settings.COMPANY_NAME} Meeting<br>
              Organizer: {organizer_email}<br>
              Organizer Phone: {organizer_phone}<br>
              Scheduled via: {settings.COMPANY_NAME} ChatBot Assistant<br>
              Requested by: {customer_email}<br><br>
              Important Notes:<br>
              &bull; Please confirm attendance by responding to this invitation<br>
              &bull; For questions or changes, contact organizer directly<br>
              &bull; Contact: {organizer_email}<br><br>
              Guests:<br>
              Mktg Professional: {marketer_full}; {marketer_email}<br>
              Requester: {customer_full}; {customer_email}
            </td>
          </tr>
          <tr>
            <td style="padding: 10px 0; font-weight: bold; vertical-align: top; color: #555;">From</td>
            <td style="padding: 10px 0;">{organizer_name} &nbsp;&nbsp; Calendar</td>
          </tr>
        </table>

        <div style="background: #f0f7ff; border-left: 4px solid #0078d4; padding: 14px 18px; margin: 16px 0; border-radius: 4px;">
          <strong>Regards,</strong><br>
          {organizer_name}<br>
          {organizer_email}
        </div>
      </div>

      <p style="color: #999; font-size: 11px; text-align: center; margin-top: 16px;">
        {settings.COMPANY_NAME} &mdash; Automated Meeting Notification
      </p>
    </body>
    </html>
    """


# ── Service ───────────────────────────────────────────────────────────

class NotificationService:
    """Thin wrappers around email / WhatsApp / Telegram."""

    def __init__(self) -> None:
        self._twilio: Optional[Any] = None
        self._telegram: Optional[Any] = None

        if settings.twilio_configured and TwilioClient:
            self._twilio = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )
            logger.info("Twilio client initialised")

        if settings.telegram_configured and TelegramBot:
            self._telegram_token = settings.TELEGRAM_BOT_TOKEN

    # ── Email ─────────────────────────────────────────────────────────

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        if not settings.smtp_configured:
            logger.warning("SMTP not configured — email not sent")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL or settings.EMAIL_USERNAME
        msg["To"] = to_email
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Email send failed: %s", exc)
            return False

    async def send_conversation_email(
        self,
        customer_email: str,
        customer_name: str,
        session_id: str,
        messages: List[Dict[str, str]],
        product_name: Optional[str] = None,
    ) -> bool:
        """Send a styled conversation summary email."""
        html = _conversation_html(customer_name, session_id, messages, product_name)
        subject = f"{settings.COMPANY_NAME} — Chat Summary"
        return await self.send_email(customer_email, subject, html)

    # ── WhatsApp ──────────────────────────────────────────────────────

    async def send_whatsapp(self, to_phone: str, body: str) -> bool:
        if not self._twilio:
            logger.warning("Twilio not configured — WhatsApp not sent")
            return False
        try:
            # Ensure from/to have exactly one 'whatsapp:' prefix
            wa_from = settings.TWILIO_WHATSAPP_NUMBER
            if not wa_from.startswith("whatsapp:"):
                wa_from = f"whatsapp:{wa_from}"
            wa_to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
            self._twilio.messages.create(
                body=body,
                from_=wa_from,
                to=wa_to,
            )
            logger.info("WhatsApp sent to %s", to_phone)
            return True
        except Exception as exc:
            logger.error("WhatsApp send failed: %s", exc)
            return False

    async def send_meeting_whatsapp(
        self,
        to_phone: str,
        recipient_name: str,
        other_party_name: str,
        other_party_email: str,
        start_iso: str,
        end_iso: str,
        requester_email: str,
        is_for_requester: bool = True,
    ) -> bool:
        """Send emoji-rich WhatsApp meeting confirmation."""
        body = _build_whatsapp_meeting_msg(
            recipient_name=recipient_name,
            other_party_name=other_party_name,
            other_party_email=other_party_email,
            start_iso=start_iso,
            end_iso=end_iso,
            requester_email=requester_email,
            is_for_requester=is_for_requester,
        )
        return await self.send_whatsapp(to_phone, body)

    async def send_meeting_email(
        self,
        to_email: str,
        customer_first: str,
        customer_last: str,
        customer_email: str,
        marketer_first: str,
        marketer_last: str,
        marketer_email: str,
        start_iso: str,
        end_iso: str,
    ) -> bool:
        """Send a professional HTML meeting confirmation email."""
        dt = _format_meeting_datetime(start_iso, end_iso)
        subject = f"Customer Meeting - {settings.COMPANY_NAME}, {dt['date']}"
        html = _meeting_email_html(
            recipient_name=to_email,  # used for personalisation if needed
            customer_first=customer_first,
            customer_last=customer_last,
            customer_email=customer_email,
            marketer_first=marketer_first,
            marketer_last=marketer_last,
            marketer_email=marketer_email,
            start_iso=start_iso,
            end_iso=end_iso,
            organizer_name=settings.ORGANIZER_NAME,
            organizer_email=settings.ORGANIZER_EMAIL,
            organizer_phone=settings.ORGANIZER_PHONE,
        )
        return await self.send_email(to_email, subject, html)

    async def send_meeting_notifications(
        self,
        customer_info: Dict[str, Any],
        marketer_info: Dict[str, Any],
        start_iso: str,
        end_iso: str,
    ) -> Dict[str, bool]:
        """
        Send meeting confirmations to all parties via WhatsApp + Email.

        Recipients: customer (requester), marketing professional, organizer.
        Returns a dict of channel/recipient → success.
        """
        results: Dict[str, bool] = {}

        customer_first = customer_info.get("first_name", "Customer")
        customer_last = customer_info.get("last_name", "")
        customer_full = f"{customer_first} {customer_last}".strip()
        customer_email = customer_info.get("email", "")
        customer_phone = customer_info.get("phone", "")

        marketer_first = marketer_info.get("first_name", "")
        marketer_last = marketer_info.get("last_name", "")
        marketer_full = f"{marketer_first} {marketer_last}".strip()
        marketer_email = marketer_info.get("email", "")
        marketer_phone = marketer_info.get("phone", "")

        organizer_phone = settings.ORGANIZER_PHONE
        organizer_name = settings.ORGANIZER_NAME

        # ── WhatsApp notifications ────────────────────────────────────

        # 1. Customer (requester)
        if customer_phone:
            results["whatsapp_customer"] = await self.send_meeting_whatsapp(
                to_phone=customer_phone,
                recipient_name=customer_full,
                other_party_name=marketer_full,
                other_party_email=marketer_email,
                start_iso=start_iso,
                end_iso=end_iso,
                requester_email=customer_email,
                is_for_requester=True,
            )
        else:
            logger.warning("No phone for customer — WhatsApp skipped")
            results["whatsapp_customer"] = False

        # 2. Marketing professional
        if marketer_phone:
            results["whatsapp_marketer"] = await self.send_meeting_whatsapp(
                to_phone=marketer_phone,
                recipient_name=marketer_full,
                other_party_name=customer_full,
                other_party_email=customer_email,
                start_iso=start_iso,
                end_iso=end_iso,
                requester_email=customer_email,
                is_for_requester=False,
            )
        else:
            logger.warning("No phone for marketer — WhatsApp skipped")
            results["whatsapp_marketer"] = False

        # 3. Organizer
        if organizer_phone:
            results["whatsapp_organizer"] = await self.send_meeting_whatsapp(
                to_phone=organizer_phone,
                recipient_name=organizer_name,
                other_party_name=customer_full,
                other_party_email=customer_email,
                start_iso=start_iso,
                end_iso=end_iso,
                requester_email=customer_email,
                is_for_requester=False,
            )
        else:
            logger.warning("No phone for organizer — WhatsApp skipped")
            results["whatsapp_organizer"] = False

        # ── Email notifications ───────────────────────────────────────

        email_recipients = []
        if customer_email:
            email_recipients.append(("email_customer", customer_email))
        if marketer_email:
            email_recipients.append(("email_marketer", marketer_email))
        if settings.ORGANIZER_EMAIL:
            email_recipients.append(("email_organizer", settings.ORGANIZER_EMAIL))

        for key, email in email_recipients:
            results[key] = await self.send_meeting_email(
                to_email=email,
                customer_first=customer_first,
                customer_last=customer_last,
                customer_email=customer_email,
                marketer_first=marketer_first,
                marketer_last=marketer_last,
                marketer_email=marketer_email,
                start_iso=start_iso,
                end_iso=end_iso,
            )

        logger.info("Meeting notification results: %s", results)
        return results

    # ── Telegram ──────────────────────────────────────────────────────

    async def send_telegram(self, chat_id: int, text: str) -> bool:
        if not TelegramBot or not settings.telegram_configured:
            logger.warning("Telegram not configured — message not sent")
            return False
        try:
            bot = TelegramBot(token=self._telegram_token)
            await bot.send_message(chat_id=chat_id, text=text)
            logger.info("Telegram sent to chat_id=%s", chat_id)
            return True
        except Exception as exc:
            logger.error("Telegram send failed: %s", exc)
            return False

    async def send_meeting_telegram(
        self,
        chat_id: int,
        customer_name: str,
        marketer_name: str,
        meeting_time: str,
    ) -> bool:
        text = (
            f"Meeting confirmed\\!\n\n"
            f"*Customer:* {customer_name}\n"
            f"*With:* {marketer_name}\n"
            f"*Time:* {meeting_time}\n\n"
            f"— {settings.COMPANY_NAME}"
        )
        return await self.send_telegram(chat_id, text)


# ── Singleton ─────────────────────────────────────────────────────────

notification_service = NotificationService()
