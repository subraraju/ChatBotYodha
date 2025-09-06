"""
Flexible customer products query script
Usage: python customer_products_flexible.py [customer_id]
Example: python customer_products_flexible.py 1001
"""
import sys
import os

# Simple inline query script
def query_customer_products():
    customer_id = 1008  # default
    
    # Get customer ID from command line
    if len(sys.argv) > 1:
        try:
            customer_id = int(sys.argv[1])
        except ValueError:
            print("Invalid customer ID, using default: 1008")
    
    print(f"Querying products for customer ID: {customer_id}")
    
    # SQL Query you can run directly in your database client:
    query = f"""
-- Products purchased by customer {customer_id}
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    p.product_name,
    p.category,
    p.type,
    p.price,
    s.quantity,
    s.total_amount,
    s.sale_date
FROM customer c
JOIN sales s ON c.customer_id = s.customer_id
JOIN product p ON s.product_id = p.product_id  
WHERE c.customer_id = {customer_id}
ORDER BY s.sale_date DESC
LIMIT 10;
"""
    
    print("\n" + "="*60)
    print("SQL Query to run in your database client:")
    print("="*60)
    print(query)
    print("="*60)
    
    # Alternative queries
    print(f"\nAlternative queries for customer {customer_id}:")
    print("-" * 50)
    
    print(f"\n1. Customer Info:")
    print(f"SELECT * FROM customer WHERE customer_id = {customer_id};")
    
    print(f"\n2. All purchases by customer:")
    print(f"SELECT * FROM sales WHERE customer_id = {customer_id};")
    
    print(f"\n3. Product details for customer's purchases:")
    print(f"""
SELECT p.* 
FROM product p 
JOIN sales s ON p.product_id = s.product_id 
WHERE s.customer_id = {customer_id};
""")
    
    print(f"\n4. Customer purchase summary:")
    print(f"""
SELECT 
    COUNT(*) as total_purchases,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as avg_order_value,
    MIN(sale_date) as first_purchase,
    MAX(sale_date) as last_purchase
FROM sales 
WHERE customer_id = {customer_id};
""")

if __name__ == "__main__":
    query_customer_products()
