"""
Customer-service chatbot — state-machine-driven conversation engine.

Two flows:
  1. Customer Support  — identify → show purchases → product Q&A (FAISS)
  2. Marketing Meeting — pick person → get slots → book via Google Calendar

Every public method is async so it can call the LLM and calendar services.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service
from app.services.calendar_service import calendar_service
from app.services import customer_lookup
from app.services import activity_service
from app.services.notification_service import notification_service
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


# ── Enums & data classes ──────────────────────────────────────────────

class State(str, Enum):
    UNKNOWN = "UNKNOWN"
    COLLECTING_INFO = "COLLECTING_INFO"
    IDENTIFIED = "IDENTIFIED"
    PRODUCT_SUPPORT = "PRODUCT_SUPPORT"
    MARKETING_SCHEDULER = "MARKETING_SCHEDULER"


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: State = State.UNKNOWN
    customer_id: Optional[int] = None
    customer_info: Dict[str, Any] = field(default_factory=dict)
    recent_purchases: List[Dict[str, Any]] = field(default_factory=list)
    all_purchases: List[Dict[str, Any]] = field(default_factory=list)
    displayed_purchases: int = 0
    has_more_purchases: bool = False
    selected_product: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    marketing_flow: Dict[str, Any] = field(default_factory=dict)
    debug_info: Dict[str, Any] = field(default_factory=dict)


# ── Chatbot ───────────────────────────────────────────────────────────

class CustomerServiceBot:
    """Stateless service — all mutable state is in ChatSession."""

    def start_session(self) -> ChatSession:
        session = ChatSession()
        welcome = (
            f"Welcome to {settings.COMPANY_NAME} support! "
            "I can help with product questions or schedule a meeting with our team.\n\n"
            "Could you please share your **email** or **phone number** so I can look up your account?"
        )
        session.messages.append({"role": "assistant", "content": welcome})
        session.state = State.COLLECTING_INFO
        return session

    # ── Main entry point ──────────────────────────────────────────────

    async def process_message(
        self, message: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        """Process one user message, return (response_text, updated_session)."""
        session.messages.append({"role": "user", "content": message})

        # ── Universal overrides ───────────────────────────────────────
        if self._is_closing(message):
            reply = await self._close_session(session, db)
            return reply, session

        if self._is_marketing_request(message) and session.state != State.MARKETING_SCHEDULER:
            session.state = State.MARKETING_SCHEDULER
            session.marketing_flow = {"step": "selecting_person"}
            return await self._handle_marketing(message, session, db)

        # ── State dispatch ────────────────────────────────────────────
        handlers = {
            State.UNKNOWN: self._handle_unknown,
            State.COLLECTING_INFO: self._handle_collecting,
            State.IDENTIFIED: self._handle_identified,
            State.PRODUCT_SUPPORT: self._handle_product_support,
            State.MARKETING_SCHEDULER: self._handle_marketing,
        }
        handler = handlers.get(session.state, self._handle_unknown)
        reply, session = await handler(message, session, db)
        session.messages.append({"role": "assistant", "content": reply})
        return reply, session

    # ── State handlers ────────────────────────────────────────────────

    async def _handle_unknown(
        self, msg: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        session.state = State.COLLECTING_INFO
        return (
            "Could you share your **email** or **phone** so I can look up your account?",
            session,
        )

    async def _handle_collecting(
        self, msg: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        info = _extract_contact(msg)
        if not info:
            return (
                "I couldn't find an email or phone in your message. "
                "Please provide your **email address** or **phone number**.",
                session,
            )

        cust = customer_lookup.find_customer(db, **info)
        if not cust:
            return (
                "I couldn't find an account with that information. "
                "Please double-check or provide an alternative email/phone.",
                session,
            )

        session.customer_id = cust["customer_id"]
        session.customer_info = cust
        session.state = State.IDENTIFIED

        # Preload purchases
        purchases, has_more = customer_lookup.get_purchases(
            db, cust["customer_id"], 0, PAGE_SIZE
        )
        session.all_purchases = purchases
        session.recent_purchases = purchases
        session.displayed_purchases = len(purchases)
        session.has_more_purchases = has_more

        name = cust.get("first_name", "there")
        if not purchases:
            return (
                f"Hi **{name}**! I found your account but you don't have any recent purchases. "
                "Would you like to schedule a meeting with our team?",
                session,
            )

        lines = [f"Hi **{name}**! Here are your recent purchases:\n"]
        for i, p in enumerate(purchases, 1):
            lines.append(
                f"{i}. **{p['product_name']}** (v{p['version']}) — "
                f"${p['total_amount']:.2f} on {p['sale_date']}"
            )
        if has_more:
            lines.append("\nType **more** to see additional purchases.")
        lines.append(
            "\nPlease select a product **number** for support, "
            "or type **meeting** to schedule a call."
        )
        return "\n".join(lines), session

    async def _handle_identified(
        self, msg: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        # "more" pagination
        if msg.strip().lower() == "more" and session.has_more_purchases:
            purchases, has_more = customer_lookup.get_purchases(
                db, session.customer_id, session.displayed_purchases, PAGE_SIZE
            )
            session.all_purchases.extend(purchases)
            session.recent_purchases = session.all_purchases
            session.displayed_purchases += len(purchases)
            session.has_more_purchases = has_more

            lines = ["Here are more purchases:\n"]
            start = session.displayed_purchases - len(purchases)
            for i, p in enumerate(purchases, start + 1):
                lines.append(
                    f"{i}. **{p['product_name']}** (v{p['version']}) — "
                    f"${p['total_amount']:.2f} on {p['sale_date']}"
                )
            if has_more:
                lines.append("\nType **more** for even more.")
            lines.append("\nSelect a product **number** for support.")
            return "\n".join(lines), session

        # Product selection by number
        match = re.match(r"^\s*(\d+)\s*$", msg)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(session.all_purchases):
                prod = session.all_purchases[idx]
                session.selected_product = prod
                session.state = State.PRODUCT_SUPPORT
                return (
                    f"Great — you selected **{prod['product_name']}** (v{prod['version']}).\n"
                    "What would you like to know? I can help with warranty, features, "
                    "troubleshooting, or anything else about this product.",
                    session,
                )
            return "That number isn't in the list. Please pick a valid product number.", session

        # Partial name match
        lower = msg.strip().lower()
        for p in session.all_purchases:
            if lower in p["product_name"].lower():
                session.selected_product = p
                session.state = State.PRODUCT_SUPPORT
                return (
                    f"I found **{p['product_name']}**! What can I help you with?",
                    session,
                )

        return (
            "Please select a product by **number** or **name**, "
            "or type **meeting** to schedule a call.",
            session,
        )

    async def _handle_product_support(
        self, msg: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        # Product switch
        if self._is_product_switch(msg):
            session.selected_product = None
            session.state = State.IDENTIFIED
            lines = ["Sure! Here are your purchases again:\n"]
            for i, p in enumerate(session.all_purchases, 1):
                lines.append(f"{i}. **{p['product_name']}** (v{p['version']})")
            lines.append("\nSelect a product **number**.")
            return "\n".join(lines), session

        product_name = session.selected_product["product_name"]

        # FAISS search
        docs = embedding_service.search(
            f"{product_name}: {msg}", top_k=3
        )

        if docs:
            context = "\n\n".join(d["text"] for d in docs)
            prompt = (
                f"Product: {product_name}\n"
                f"Documentation:\n{context}\n\n"
                f"Customer question: {msg}\n\n"
                "Answer the question using the documentation above. "
                "Be concise and helpful. If the documentation doesn't cover this, say so."
            )
        else:
            prompt = (
                f"The customer is asking about their product '{product_name}'.\n"
                f"Question: {msg}\n\n"
                "Provide a helpful, concise reply. If you don't have specific details, "
                "suggest they contact support or schedule a meeting."
            )

        history = [m for m in session.messages[-10:] if m["role"] in ("user", "assistant")]
        try:
            reply = await llm_service.chat(prompt, conversation_history=history)
        except RuntimeError as exc:
            reply = str(exc)
        return reply, session

    # ── Marketing flow ────────────────────────────────────────────────

    async def _handle_marketing(
        self, msg: str, session: ChatSession, db: Session
    ) -> Tuple[str, ChatSession]:
        flow = session.marketing_flow
        step = flow.get("step", "selecting_person")

        if step == "selecting_person":
            persons = customer_lookup.get_marketing_persons(db)
            if not persons:
                return "No marketing representatives are available right now. Please try later.", session
            flow["persons"] = persons
            lines = ["Here are our available representatives:\n"]
            for i, p in enumerate(persons, 1):
                lines.append(f"{i}. **{p['first_name']} {p['last_name']}**")
            lines.append("\nPlease select a **number**.")
            flow["step"] = "awaiting_person_choice"
            session.messages.append({"role": "assistant", "content": "\n".join(lines)})
            return "\n".join(lines), session

        if step == "awaiting_person_choice":
            match = re.match(r"^\s*(\d+)\s*$", msg)
            if not match:
                return "Please enter the **number** of the representative.", session
            idx = int(match.group(1)) - 1
            persons = flow.get("persons", [])
            if idx < 0 or idx >= len(persons):
                return "Invalid selection. Pick a number from the list.", session
            person = persons[idx]
            flow["person"] = person
            flow["step"] = "collecting_email"
            return (
                f"You selected **{person['first_name']} {person['last_name']}**.\n"
                "Please provide your **email** for the calendar invite:",
                session,
            )

        if step == "collecting_email":
            email = _extract_email(msg)
            if not email:
                return "Please provide a valid **email address**.", session
            flow["user_email"] = email
            flow["step"] = "showing_slots"

            person = flow["person"]
            try:
                slots = await calendar_service.suggest_slots(person["email"])
            except Exception as exc:
                logger.error("Calendar slot suggestion failed: %s", exc)
                slots = []
            if not slots:
                return "No available slots this week. Would you like to try next week?", session
            flow["slots"] = slots
            lines = [f"Available slots with **{person['first_name']}**:\n"]
            for i, s in enumerate(slots, 1):
                lines.append(f"{i}. {s['display']}")
            lines.append("\nSelect a **number** to book.")
            return "\n".join(lines), session

        if step == "showing_slots":
            match = re.match(r"^\s*(\d+)\s*$", msg)
            if not match:
                return "Please enter the **number** of the time slot.", session
            idx = int(match.group(1)) - 1
            slots = flow.get("slots", [])
            if idx < 0 or idx >= len(slots):
                return "Invalid slot. Pick a number from the list.", session
            slot = slots[idx]
            person = flow["person"]
            user_email = flow["user_email"]

            event_id = await calendar_service.book_meeting(
                start_iso=slot["start"],
                end_iso=slot["end"],
                subject=f"{settings.COMPANY_NAME} — Meeting",
                attendees=[user_email, person["email"]],
                description=f"Scheduled via {settings.COMPANY_NAME} chatbot",
            )

            if event_id:
                # If customer_info is empty, look up from DB using the email
                if not session.customer_info.get("phone"):
                    cust = customer_lookup.find_customer(db, email=user_email)
                    if cust:
                        session.customer_info = cust
                        session.customer_id = cust["customer_id"]

                # Build full marketer info dict for notifications
                marketer_info = {
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "email": person.get("email", ""),
                    "phone": person.get("phone", ""),
                }

                # Send WhatsApp + Email to customer, marketer, and organizer
                await notification_service.send_meeting_notifications(
                    customer_info=session.customer_info,
                    marketer_info=marketer_info,
                    start_iso=slot["start"],
                    end_iso=slot["end"],
                )

                customer_name = session.customer_info.get("first_name", "Customer")
                marketer_name = f"{person['first_name']} {person['last_name']}"

                flow["step"] = "done"
                session.state = State.IDENTIFIED
                return (
                    f"Your meeting is booked for **{slot['display']}** "
                    f"with **{marketer_name}**! A calendar invite has been sent to {user_email}.\n\n"
                    "Is there anything else I can help with?",
                    session,
                )
            return "Sorry, I couldn't book that slot. Please try another.", session

        return "Something went wrong with the scheduling flow. Type **meeting** to restart.", session

    # ── Session close ─────────────────────────────────────────────────

    async def _close_session(self, session: ChatSession, db: Session) -> str:
        """Store conversation, create activity, send email."""
        reply = (
            f"Thank you for contacting {settings.COMPANY_NAME}! "
            "Have a great day. Goodbye!"
        )
        session.messages.append({"role": "assistant", "content": reply})

        # Persist conversation
        data = {
            "session_id": session.session_id,
            "customer_id": session.customer_id,
            "customer_info": session.customer_info,
            "messages": session.messages,
        }
        url = await storage_service.save_session(session.session_id, data)

        # Activity record
        if session.customer_id:
            product_id = (
                session.selected_product.get("product_id")
                if session.selected_product else None
            )
            activity_service.create_chatbot_activity(
                db,
                customer_id=session.customer_id,
                session_id=session.session_id,
                url_data=url,
                product_id=product_id,
                description=f"Chat session — {len(session.messages)} messages",
            )

        # Send email summary
        if session.customer_info.get("email"):
            await notification_service.send_conversation_email(
                session.customer_info["email"],
                session.customer_info.get("first_name", "Customer"),
                session.session_id,
                session.messages,
                session.selected_product.get("product_name") if session.selected_product else None,
            )

        return reply

    # ── Detection helpers ─────────────────────────────────────────────

    @staticmethod
    def _is_closing(msg: str) -> bool:
        lower = msg.strip().lower()
        patterns = [
            r"\b(bye|goodbye|exit|quit|close|end\s*chat|that'?s?\s*all)\b",
            r"^(thanks|thank\s*you)\s*[.!]*$",
        ]
        return any(re.search(p, lower) for p in patterns)

    @staticmethod
    def _is_marketing_request(msg: str) -> bool:
        lower = msg.strip().lower()
        patterns = [
            r"\b(meeting|schedule|appointment|book\s*a?\s*call|marketing)\b",
        ]
        return any(re.search(p, lower) for p in patterns)

    @staticmethod
    def _is_product_switch(msg: str) -> bool:
        lower = msg.strip().lower()
        patterns = [
            r"\b(switch|change|different|another|other)\s*(product|item)\b",
            r"\bgo\s*back\b",
        ]
        return any(re.search(p, lower) for p in patterns)


# ── Helpers ───────────────────────────────────────────────────────────

def _extract_contact(msg: str) -> Dict[str, str]:
    """Pull email or phone from a message."""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", msg)
    if email_match:
        return {"email": email_match.group()}

    phone_match = re.search(r"[\+]?[\d\s\-()]{7,15}", msg)
    if phone_match:
        return {"phone": phone_match.group().strip()}

    return {}


def _extract_email(msg: str) -> Optional[str]:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", msg)
    return match.group() if match else None
