import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}
print(db_config)
# Sample query
query = "SELECT * FROM customer LIMIT 10;"

def connect_and_query(config, sql_query):
    try:
        # Establish connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # Execute query
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # Display results
        for row in rows:
            print(row)

        # Cleanup
        cursor.close()
        conn.close()
        print("Connection closed successfully.")

    except Exception as e:
        print("An error occurred:", e)

# Call the function
connect_and_query(db_config, query)