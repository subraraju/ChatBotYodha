-- Create Customer Table
CREATE TABLE IF NOT EXISTS customer (
    customer_id SERIAL PRIMARY KEY,
    party_type VARCHAR(20),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    middle_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    addr1 VARCHAR(50),
    addr2 VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    zipcode VARCHAR(20),
    country VARCHAR(20),
    comments VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Product Table
CREATE TABLE IF NOT EXISTS product (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    type VARCHAR(50),
    version VARCHAR(20),
    price DECIMAL(10, 2),
    stock_quantity INT,
    start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_dt TIMESTAMP,
    comments VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Sales Table
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customer(customer_id),
    product_id INT REFERENCES product(product_id),
    quantity INT,
    sale_date DATE,
    comments VARCHAR(200),
    total_amount DECIMAL(10, 2)
);

-- Create Activity Table
CREATE TABLE IF NOT EXISTS activity (
    activity_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customer(customer_id),
    product_id INT REFERENCES product(product_id),
    activity_type VARCHAR(50),
    description TEXT,
    comments VARCHAR(200),
    activity_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customer_email ON customer(email);
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_activity_customer_id ON activity(customer_id);
CREATE INDEX IF NOT EXISTS idx_activity_product_id ON activity(product_id);
