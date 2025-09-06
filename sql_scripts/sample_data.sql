-- Insert sample customers
INSERT INTO customer (party_type, first_name, last_name, email, phone, addr1, city, state, zipcode, country) VALUES
('Individual', 'John', 'Doe', 'john.doe@email.com', '555-0101', '123 Main St', 'Seattle', 'WA', '98101', 'USA'),
('Individual', 'Jane', 'Smith', 'jane.smith@email.com', '555-0102', '456 Oak Ave', 'Portland', 'OR', '97201', 'USA'),
('Business', 'Mike', 'Johnson', 'mike.johnson@company.com', '555-0103', '789 Pine St', 'San Francisco', 'CA', '94102', 'USA');

-- Insert sample products
INSERT INTO product (product_name, category, type, version, price, stock_quantity) VALUES
('CRM Software', 'Software', 'Enterprise', '2.1', 999.99, 100),
('Project Management Tool', 'Software', 'Business', '1.5', 299.99, 50),
('Analytics Dashboard', 'Software', 'Professional', '3.0', 599.99, 75),
('Mobile App License', 'Software', 'Standard', '1.0', 99.99, 200);

-- Insert sample sales
INSERT INTO sales (customer_id, product_id, quantity, sale_date, total_amount) VALUES
(1, 1, 1, '2024-01-15', 999.99),
(2, 2, 2, '2024-01-20', 599.98),
(3, 3, 1, '2024-01-25', 599.99),
(1, 4, 3, '2024-02-01', 299.97);

-- Insert sample activities
INSERT INTO activity (customer_id, product_id, activity_type, description) VALUES
(1, 1, 'Support', 'Customer requested help with initial setup'),
(2, 2, 'Training', 'Provided training session for project management features'),
(3, 3, 'Demo', 'Conducted product demonstration'),
(1, 4, 'Follow-up', 'Post-sale follow-up call');
