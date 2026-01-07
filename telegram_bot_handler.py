#!/usr/bin/env python3
"""
Telegram Bot Handler for Meeting Notifications Registration

This bot allows users to register their Telegram account to receive meeting notifications.
Users send /register email@example.com and the bot stores their chat_id in the database.

Usage:
    python telegram_bot_handler.py

Commands:
    /start - Welcome message and instructions
    /register email@example.com - Register email to receive notifications
    /status - Check registration status
    /unregister - Remove Telegram notifications
"""

import os
import re
import logging
import asyncio
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import Telegram library
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot>=21.0")
    exit(1)

# Get bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)


def get_db_session():
    """Get database session"""
    from app.database import SessionLocal
    return SessionLocal()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_customer_by_email(email: str):
    """Get customer from database by email"""
    from app.models.database_models import Customer
    
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        return customer
    finally:
        db.close()


def update_telegram_chat_id(email: str, chat_id: int) -> tuple[bool, str]:
    """
    Update telegram_chat_id for a customer.
    
    Returns:
        (success: bool, message: str)
    """
    from app.models.database_models import Customer
    
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        
        if not customer:
            return False, f"Email '{email}' not found in our system. Please use the email you registered with."
        
        # Check if already registered with different chat_id
        old_chat_id = customer.telegram_chat_id
        if old_chat_id and old_chat_id != chat_id:
            logger.info(f"Overwriting telegram_chat_id for {email}: {old_chat_id} -> {chat_id}")
        
        # Update chat_id
        customer.telegram_chat_id = chat_id
        db.commit()
        
        customer_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or "User"
        
        if old_chat_id:
            return True, f"Updated! {customer_name}, your Telegram notifications have been re-registered."
        else:
            return True, f"Success! {customer_name}, you will now receive meeting notifications on Telegram."
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating telegram_chat_id: {e}")
        return False, "An error occurred. Please try again later."
    finally:
        db.close()


def get_registration_status(chat_id: int) -> Optional[str]:
    """Check if a chat_id is registered and return the email"""
    from app.models.database_models import Customer
    
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.telegram_chat_id == chat_id).first()
        if customer:
            return customer.email
        return None
    finally:
        db.close()


def remove_telegram_registration(chat_id: int) -> tuple[bool, str]:
    """Remove telegram_chat_id for a customer"""
    from app.models.database_models import Customer
    
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.telegram_chat_id == chat_id).first()
        
        if not customer:
            return False, "You are not registered for Telegram notifications."
        
        email = customer.email
        customer.telegram_chat_id = None
        db.commit()
        
        logger.info(f"Removed telegram registration for {email}")
        return True, f"Unregistered! You will no longer receive Telegram notifications for {email}."
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing telegram registration: {e}")
        return False, "An error occurred. Please try again later."
    finally:
        db.close()


# Command Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"/start from user {user.first_name} (chat_id: {chat_id})")
    
    welcome_message = f"""👋 Welcome to Yodha Meeting Notifications Bot!

Hi {user.first_name}! This bot sends you meeting notifications directly on Telegram.

📝 **How to Register:**
Send your email to link your account:
`/register your.email@example.com`

📌 **Example:**
`/register vishmatere1999@gmail.com`

Once registered, you'll receive:
• Meeting confirmations
• Appointment reminders
• Schedule updates

💡 Use /status to check your registration status.
"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /register command - Register email for notifications"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Check if email was provided
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide your email address.\n\n"
            "Usage: `/register your.email@example.com`",
            parse_mode='Markdown'
        )
        return
    
    email = context.args[0].lower().strip()
    
    # Validate email format
    if not validate_email(email):
        await update.message.reply_text(
            "❌ Invalid email format. Please use a valid email address.\n\n"
            "Example: `/register your.email@example.com`",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"/register from {user.first_name} (chat_id: {chat_id}) - email: {email}")
    
    # Update database
    success, message = update_telegram_chat_id(email, chat_id)
    
    if success:
        await update.message.reply_text(
            f"✅ {message}\n\n"
            "You will now receive meeting notifications on Telegram! 🎉",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ {message}",
            parse_mode='Markdown'
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - Check registration status"""
    chat_id = update.effective_chat.id
    
    registered_email = get_registration_status(chat_id)
    
    if registered_email:
        await update.message.reply_text(
            f"✅ **Registered**\n\n"
            f"Email: `{registered_email}`\n"
            f"Chat ID: `{chat_id}`\n\n"
            "You will receive meeting notifications here.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ **Not Registered**\n\n"
            "You are not registered for notifications.\n"
            "Use `/register your.email@example.com` to register.",
            parse_mode='Markdown'
        )


async def unregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unregister command - Remove registration"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    logger.info(f"/unregister from {user.first_name} (chat_id: {chat_id})")
    
    success, message = remove_telegram_registration(chat_id)
    
    if success:
        await update.message.reply_text(f"✅ {message}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ {message}", parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = """📚 **Available Commands:**

/start - Welcome message and instructions
/register email - Register for notifications
/status - Check registration status
/unregister - Stop receiving notifications
/help - Show this help message

💡 **Need help?** Contact support at support@yodha.com
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see available commands.",
        parse_mode='Markdown'
    )


def main() -> None:
    """Start the bot"""
    logger.info("Starting Telegram Bot Handler...")
    logger.info(f"Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("unregister", unregister_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Start polling
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
