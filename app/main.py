from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import List

# Import routers
from app.api.customers import router as customers_router
from app.api.products import router as products_router
from app.api.sales import router as sales_router
from app.api.activities import router as activities_router
from app.api.tavily import router as tavily_router

# Import services and models
from app.database import get_database, create_tables
from app.models.pydantic_models import ChatSession, ChatMessage, SimpleChatRequest, SimpleChatResponse
from app.services.storage import chat_storage
from app.services.messaging import email_service, sms_service, MessageFormatter
from app.chatbot.agent import chatbot_agent
from app.chatbot.customer_service_bot import CustomerServiceBot

# Initialize the Customer Service Bot (Yodha)
customer_service_bot = None

def get_customer_service_bot():
    """Get or initialize the customer service bot"""
    global customer_service_bot
    if customer_service_bot is None:
        customer_service_bot = CustomerServiceBot()
    return customer_service_bot

app = FastAPI(
    title="Agentic Chatbot API",
    description="A comprehensive chatbot with database integration, external search, and messaging capabilities",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(customers_router)
app.include_router(products_router)
app.include_router(sales_router)
app.include_router(activities_router)
app.include_router(tavily_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()


@app.get("/")
async def root():
    return {"message": "Agentic Chatbot API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


# Simple Chat API - stateless endpoint for external integration
@app.post("/api/chat/simple", response_model=SimpleChatResponse)
async def simple_chat(request: SimpleChatRequest):
    """
    Simple stateless chat endpoint for external integration.
    
    Send a message and get a response - no session management required.
    Uses the CustomerServiceBot (Yodha) which powers the Streamlit interface.
    
    - **message**: The user's message/question
    - **customer_email**: Optional customer email for personalized responses
    """
    try:
        bot = get_customer_service_bot()
        
        # Create a new session for this request
        session = bot.start_new_session()
        
        # If customer email is provided, add it to the session context
        if request.customer_email:
            session.customer_info['email'] = request.customer_email
        
        # Process the message
        response, _ = bot.process_message(request.message, session)
        
        return SimpleChatResponse(response=response, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Session-based Chat endpoints
@app.post("/api/chat/start")
async def start_chat_session(customer_email: str):
    """Start a new chat session"""
    try:
        session = chatbot_agent.create_chat_session(customer_email)
        chat_storage.save_chat_session(session)
        return {"session_id": session.session_id, "message": "Chat session started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{session_id}/message")
async def send_message(session_id: str, message: str, use_external_search: bool = True):
    """Send a message in a chat session"""
    try:
        # Load existing session
        session = chat_storage.load_chat_session(session_id)

        # Process message
        response, updated_session = chatbot_agent.chat(
            message, session, use_external_search
        )

        # Save updated session
        chat_storage.save_chat_session(updated_session)

        return {"response": response, "message_count": len(updated_session.messages)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{session_id}")
async def get_chat_session(session_id: str):
    """Get a chat session"""
    try:
        session = chat_storage.load_chat_session(session_id)
        return session
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/user/{customer_email}")
async def get_user_sessions(customer_email: str):
    """Get all sessions for a user"""
    try:
        session_ids = chat_storage.list_user_sessions(customer_email)
        return {"customer_email": customer_email, "sessions": session_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{session_id}/email")
async def email_chat_summary(
    session_id: str, recipient_email: str, subject: str = None
):
    """Email chat session summary"""
    try:
        if not email_service:
            raise HTTPException(status_code=503, detail="Email service not configured")

        session = chat_storage.load_chat_session(session_id)
        email_service.send_chat_summary(session, recipient_email, subject)
        return {"message": "Chat summary sent via email"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{session_id}/sms")
async def sms_chat_summary(session_id: str, recipient_phone: str):
    """Send chat session summary via SMS"""
    try:
        if not sms_service:
            raise HTTPException(status_code=503, detail="SMS service not configured")

        session = chat_storage.load_chat_session(session_id)
        message_sid = sms_service.send_chat_summary(session, recipient_phone)
        return {"message": "Chat summary sent via SMS", "message_sid": message_sid}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{session_id}/export/{format}")
async def export_chat_session(session_id: str, format: str):
    """Export chat session in different formats"""
    try:
        session = chat_storage.load_chat_session(session_id)

        if format.lower() == "markdown":
            content = MessageFormatter.to_markdown(session)
            media_type = "text/markdown"
        elif format.lower() == "text":
            content = MessageFormatter.to_plain_text(session)
            media_type = "text/plain"
        elif format.lower() == "json":
            content = session.model_dump_json(indent=2)
            media_type = "application/json"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use: markdown, text, or json",
            )

        return {"content": content, "format": format, "session_id": session_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        chat_storage.delete_chat_session(session_id)
        return {"message": "Chat session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
