-- Migration script to add session closure functionality columns to Activity table

-- Add the missing columns to the activity table
ALTER TABLE activity 
ADD COLUMN IF NOT EXISTS sales_id INT REFERENCES sales(sale_id),
ADD COLUMN IF NOT EXISTS session_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS url_data VARCHAR(1000);

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_activity_sales_id ON activity(sales_id);
CREATE INDEX IF NOT EXISTS idx_activity_session_id ON activity(session_id);
