-- ======================================================
-- Seed data — sample customers, products, sales, activities
-- ======================================================

-- Customers (Individual / Business)
INSERT INTO customer (party_type, first_name, last_name, email, phone, city, state, country)
VALUES
    ('Individual', 'John', 'Smith', 'john.smith@example.com', '555-0101', 'New York', 'NY', 'USA'),
    ('Business',   'Jane', 'Doe',   'jane.doe@example.com',   '555-0102', 'San Francisco', 'CA', 'USA'),
    ('Individual', 'Bob',  'Wilson','bob.wilson@example.com',  '555-0103', 'Chicago', 'IL', 'USA')
ON CONFLICT (email) DO NOTHING;

-- Marketing persons
INSERT INTO customer (party_type, first_name, last_name, email, phone, city, state, country)
VALUES
    ('MKTG', 'Kartheek', 'M',    'kartheek@example.com',  '555-0201', 'Hyderabad', 'TS', 'India'),
    ('MKTG', 'Raju',     'T',    'raju.t@example.com',    '555-0202', 'Bangalore', 'KA', 'India'),
    ('MKTG', 'Malee',    'K',    'malee.k@example.com',   '555-0203', 'Chennai',   'TN', 'India')
ON CONFLICT (email) DO NOTHING;

-- Products
INSERT INTO product (product_name, category, type, version, description, price, stock_quantity, warranty_period)
VALUES
    ('CloudSync Pro',      'Software', 'SaaS',       '2.1', 'Enterprise cloud synchronisation platform',  299.99, 100, '1 year'),
    ('DataGuard Shield',   'Software', 'Security',   '3.0', 'Advanced data protection and encryption',    499.99,  50, '2 years'),
    ('SmartAnalytics Hub', 'Software', 'Analytics',  '1.5', 'AI-powered business intelligence dashboard', 199.99, 200, '1 year'),
    ('DevOps Toolkit',     'Software', 'DevOps',     '4.2', 'CI/CD pipeline management suite',            399.99,  75, '1 year')
ON CONFLICT DO NOTHING;

-- Sales
INSERT INTO sales (customer_id, product_id, quantity, sale_date, total_amount, comments)
VALUES
    (1, 1, 1, '2024-01-15', 299.99, 'Annual subscription'),
    (1, 3, 2, '2024-02-20', 399.98, 'Team license x2'),
    (2, 2, 1, '2024-03-10', 499.99, 'Enterprise license'),
    (3, 4, 1, '2024-01-05', 399.99, 'Startup plan');

-- Activities
INSERT INTO activity (customer_id, product_id, activity_type, description)
VALUES
    (1, 1, 'PURCHASE', 'Purchased CloudSync Pro annual subscription'),
    (1, 3, 'PURCHASE', 'Purchased SmartAnalytics Hub team license'),
    (2, 2, 'PURCHASE', 'Purchased DataGuard Shield enterprise'),
    (3, 4, 'INQUIRY',  'Asked about DevOps Toolkit features');
