"""
Chat API — REST endpoints + WebSocket for the customer-service chatbot.

REST workflow:
    POST /chat/start       → StartSessionResponse
    POST /chat/{sid}/message → MessageResponse
    POST /chat/{sid}/close  → CloseSessionResponse
    GET  /chat/{sid}        → SessionInfoDTO

WebSocket:
    WS /chat/ws/{sid}       → bidirectional JSON messages
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    StartSessionRequest, StartSessionResponse,
    MessageRequest, MessageResponse, MessageDTO,
    SessionInfoDTO, CloseSessionResponse,
)
from app.chatbot import CustomerServiceBot, ChatSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory session store (swap for Redis in prod)
_sessions: Dict[str, ChatSession] = {}
_bot = CustomerServiceBot()


def _session_dto(s: ChatSession) -> SessionInfoDTO:
    return SessionInfoDTO(
        session_id=s.session_id,
        customer_state=s.state.value,
        customer_id=s.customer_id,
        customer_info=s.customer_info,
        recent_purchases=s.recent_purchases,
        selected_product=s.selected_product,
        messages=[
            MessageDTO(role=m["role"], content=m["content"], timestamp=m.get("timestamp", ""))
            for m in s.messages
        ],
        debug_info=s.debug_info if s.debug_info else None,
    )


# ── REST ──────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartSessionResponse)
async def start_session(body: StartSessionRequest):
    session = _bot.start_session()
    _sessions[session.session_id] = session
    welcome = session.messages[-1]["content"] if session.messages else ""
    return StartSessionResponse(session_id=session.session_id, welcome_message=welcome)


@router.post("/{session_id}/message", response_model=MessageResponse)
async def send_message(
    session_id: str,
    body: MessageRequest,
    db: Session = Depends(get_db),
):
    session = _sessions.get(session_id)
    if not session:
        session = ChatSession(session_id=session_id)
        _sessions[session_id] = session

    reply, session = await _bot.process_message(body.message, session, db)
    _sessions[session_id] = session
    return MessageResponse(response=reply, session=_session_dto(session))


@router.get("/{session_id}", response_model=SessionInfoDTO)
async def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return SessionInfoDTO(session_id=session_id, customer_state="NOT_FOUND")
    return _session_dto(session)


@router.post("/{session_id}/close", response_model=CloseSessionResponse)
async def close_session(session_id: str, db: Session = Depends(get_db)):
    session = _sessions.get(session_id)
    if not session:
        return CloseSessionResponse(closing_message="Session not found.", stored=False)

    reply = await _bot._close_session(session, db)
    _sessions.pop(session_id, None)
    return CloseSessionResponse(closing_message=reply, stored=True)


# ── WebSocket ─────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def chat_ws(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    await websocket.accept()

    session = _sessions.get(session_id)
    if not session:
        session = _bot.start_session()
        session.session_id = session_id
        _sessions[session_id] = session
        # Send welcome
        await websocket.send_json({
            "type": "welcome",
            "message": session.messages[-1]["content"] if session.messages else "",
            "session": _session_dto(session).model_dump(),
        })

    try:
        while True:
            data = await websocket.receive_json()
            user_msg = data.get("message", "")
            if not user_msg:
                continue

            reply, session = await _bot.process_message(user_msg, session, db)
            _sessions[session_id] = session

            await websocket.send_json({
                "type": "message",
                "message": reply,
                "session": _session_dto(session).model_dump(),
            })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)
