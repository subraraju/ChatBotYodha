#!/usr/bin/env python3
"""
Local Database Setup Helper
Sets up a local PostgreSQL database for development when the remote database is not accessible
"""

import os
from dotenv import load_dotenv

def generate_local_env():
    """Generate a local .env configuration"""
    print("🔧 Generating Local Development Configuration")
    print("="*50)
    
    local_config = """# Local Development Environment Configuration
# Replace the remote database with local PostgreSQL

# Local Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mycrm_local
DB_USER=postgres
DB_PASSWORD=your_local_postgres_password

DATABASE_URL=postgresql://postgres:your_local_postgres_password@localhost:5432/mycrm_local

# Keep other configurations the same
AZURE_STORAGE_CONNECTION_STRING=your_azure_blob_storage_connection_string
AZURE_STORAGE_CONTAINER_NAME=chatbot-sessions

# Tavily API
TAVILY_API_KEY=your_tavily_api_key

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
OLLAMA_BASE_URL=http://localhost:11434

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Application Settings
APP_HOST=127.0.0.1
APP_PORT=8000
"""
    
    # Write to .env.local file
    with open('.env.local', 'w') as f:
        f.write(local_config)
    
    print("✅ Created .env.local file with local database configuration")
    print("\n📋 Next Steps:")
    print("1. Install PostgreSQL locally")
    print("2. Create a database named 'mycrm_local'")
    print("3. Update the password in .env.local")
    print("4. Copy .env.local to .env to use local configuration")
    print("5. Run the SQL scripts to create tables")

def generate_docker_compose():
    """Generate a Docker Compose file for local PostgreSQL"""
    print("\n🐳 Generating Docker Compose for Local PostgreSQL")
    print("="*50)
    
    docker_compose = """version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: chatbot_postgres
    environment:
      POSTGRES_DB: mycrm_local
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: chatbot123
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql_scripts:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d mycrm_local"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: chatbot_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@chatbot.local
      PGADMIN_DEFAULT_PASSWORD: admin123
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "8080:80"
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  default:
    name: chatbot_network
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✅ Created docker-compose.yml for local PostgreSQL")
    print("\n📋 Docker Setup Steps:")
    print("1. Install Docker Desktop")
    print("2. Run: docker-compose up -d")
    print("3. Database will be available at localhost:5432")
    print("4. PgAdmin will be available at http://localhost:8080")
    print("   - Email: admin@chatbot.local")
    print("   - Password: admin123")
    print("5. Update .env with local database credentials")

def generate_local_env_with_docker():
    """Generate .env file for Docker setup"""
    docker_env = """# Docker Local Development Environment
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mycrm_local
DB_USER=postgres
DB_PASSWORD=chatbot123

DATABASE_URL=postgresql://postgres:chatbot123@localhost:5432/mycrm_local

# Azure Storage (Optional - will use local storage if not configured)
AZURE_STORAGE_CONNECTION_STRING=your_azure_blob_storage_connection_string
AZURE_STORAGE_CONTAINER_NAME=chatbot-sessions

# External APIs
TAVILY_API_KEY=your_tavily_api_key
GROQ_API_KEY=your_groq_api_key

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
APP_HOST=127.0.0.1
APP_PORT=8000
"""
    
    with open('.env.docker', 'w') as f:
        f.write(docker_env)
    
    print("✅ Created .env.docker with Docker PostgreSQL configuration")

def main():
    print("🗄️  Local Database Setup Helper")
    print("The remote database at 4.155.102.23 is not accessible.")
    print("This script will help you set up a local development environment.\n")
    
    generate_local_env()
    generate_docker_compose()
    generate_local_env_with_docker()
    
    print("\n" + "="*50)
    print("📋 Summary - Choose Your Approach:")
    print("="*50)
    
    print("\n🐳 **Option 1: Docker (Recommended)**")
    print("   1. Install Docker Desktop")
    print("   2. Run: docker-compose up -d")
    print("   3. Copy .env.docker to .env")
    print("   4. Run: python test_db_connection.py")
    
    print("\n💻 **Option 2: Native PostgreSQL Installation**")
    print("   1. Install PostgreSQL locally")
    print("   2. Create database and user")
    print("   3. Copy .env.local to .env and update password")
    print("   4. Run the SQL scripts manually")
    print("   5. Run: python test_db_connection.py")
    
    print("\n🔄 **Option 3: Fix Remote Connection**")
    print("   1. Contact your database administrator")
    print("   2. Check if IP address has changed")
    print("   3. Verify server status and firewall rules")
    print("   4. Test connection from different network")

if __name__ == "__main__":
    main()
