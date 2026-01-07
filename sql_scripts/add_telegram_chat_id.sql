-- Migration: Add Telegram Chat ID column to Customer table
-- Purpose: Store Telegram chat_id for meeting notifications
-- Date: December 2024

-- Add telegram_chat_id column (BIGINT to handle large Telegram chat IDs)
ALTER TABLE customer ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT;

-- Add comment for documentation
COMMENT ON COLUMN customer.telegram_chat_id IS 'Telegram chat ID for sending meeting notifications. Set when user registers via Telegram bot.';

-- Create index for faster lookups by telegram_chat_id (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_customer_telegram_chat_id ON customer(telegram_chat_id) WHERE telegram_chat_id IS NOT NULL;

-- Verify the column was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'customer' AND column_name = 'telegram_chat_id';
