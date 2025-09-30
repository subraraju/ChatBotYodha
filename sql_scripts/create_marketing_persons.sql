-- Marketing Persons Table
-- This table stores information about marketing team members available for meetings

CREATE TABLE IF NOT EXISTS marketing_persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    is_active BOOLEAN DEFAULT TRUE,
    specialization VARCHAR(200),
    availability_note VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial marketing persons
INSERT OR REPLACE INTO marketing_persons (id, name, email, timezone, specialization, availability_note) VALUES
(1, 'Kartheek', 'nagakartheek.ds@gmail.com', 'Asia/Kolkata', 'Product Demos & Technical Consultations', 'Available Monday-Friday, 9 AM - 5 PM IST'),
(2, 'Raju T', 'rajuts@yahoo.com', 'Asia/Kolkata', 'Business Development & Partnerships', 'Available Monday-Saturday, flexible hours'),
(3, 'Malee', 'malee@uslocumservices.com', 'US/Pacific', 'International Sales & Support', 'Available Monday-Friday, 8 AM - 4 PM PST');

-- Create index for faster email lookups
CREATE INDEX IF NOT EXISTS idx_marketing_persons_email ON marketing_persons(email);
CREATE INDEX IF NOT EXISTS idx_marketing_persons_active ON marketing_persons(is_active);
