# ChatBotYodha
AI-powered customer service chatbot built with LangChain &amp; Azure for any Product based industry.

## ✨ Features

### 🎯 **Core Functionality**
- **Intelligent Conversational AI** with context awareness
- **Multi-step Function Calling** for complex query handling
- **Enhanced Response Formatting** with automatic bold highlighting
- **Session Management** with conversation tracking
- **Real-time Database Integration** for customer, product, and sales data

### 💬 **Communication Channels**
- **📧 Email Notifications** with full conversation content (HTML & text)
- **🌐 Web Interface** with Streamlit for seamless interaction

### 🗄️ **Data Management**
- **PostgreSQL Database** with comprehensive business schema
- **Azure Blob Storage** for conversation persistence

### 🔧 **AI & LLM Support**
- **OpenAI GPT-4** for production-grade responses
- **Ollama Local Models** for privacy-focused deployments
- **Automatic Fallback** between LLM providers

## 🏗️ Project Structure

```
genai_chatbot/
├── app/
│   ├── chatbot/
│   │   └── customer_service_bot.py  # Customer service logic
│   ├── models/
│   │   ├── database_models.py  # SQLAlchemy models
│   │   └── pydantic_models.py  # API validation models
│   ├── services/
│   │   ├── email_service.py   # Email with conversation content
│   │   └── storage.py         # Azure Blob & local storage
│   ├── database.py            # Database configuration
├── sql_scripts/
│   ├── create_tables.sql      # Database schema
│   └── sample_data.sql        # Sample data
├── venv312/                   # Python 3.12 virtual environment
├── streamlit_customer_service.py  # Enhanced UI with formatting
├── test_*.py                 # Test suites
├── requirements.txt          # Dependencies
├── .env                     # Environment configuration
└── README.md               # This file
```

## 🚀 Quick Start

### 📋 **Prerequisites**

- **Python 3.12+**
- **PostgreSQL Database** (Azure PostgreSQL recommended)
- **Azure Blob Storage** (optional, local fallback available)
- **OpenAI API Key** or **Ollama** for local LLM

### 1️⃣ **Clone & Environment Setup**

```powershell
# Clone the repository
git clone https://github.com/rajuts/ChatBotYodha.git
cd ChatBotYodha

# Create virtual environment with Python 3.12
python -m venv venv312

# Activate virtual environment
.\venv312\Scripts\Activate.ps1  # Windows PowerShell
# source venv312/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ **Database Setup**

```

### 3️⃣ **Environment Configuration**

Create/edit `.env` file:

```env
# 🗄️ Database Configuration
DB_HOST=your-postgres-server.postgres.database.azure.com
DB_PORT=5432
DB_NAME=mycrm
DB_USER=your_username
DB_PASSWORD=your_password
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# 🤖 LLM Configuration
# Option 1: OpenAI (Recommended)
OPENAI_API_KEY=sk-your-openai-api-key
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o

# Option 2: Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama

# Option 3: Groq (Fast inference)
GROQ_API_KEY=your_groq_api_key

# ☁️ Azure Storage (Optional - local fallback available)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=chatbot-sessions

# 📧 Email Configuration (Gmail recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password  # No spaces!
FROM_EMAIL=your_email@gmail.com

# 📱 WhatsApp/SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Sandbox

# 🔍 External Search
TAVILY_API_KEY=your_tavily_api_key

# 🏢 Application Settings
COMPANY_NAME=Contoso
APP_HOST=127.0.0.1
APP_PORT=8000
```

### 4️⃣ **Launch Application**

```powershell
# Activate virtual environment
.\venv312\Scripts\Activate.ps1

# Start the application (runs both FastAPI and Streamlit)
streamlit run streamlit_customer_service.py
```

## 🔧 Detailed Setup Instructions

### 🤖 **LLM Provider Setup**

#### **Option 1: OpenAI (Recommended)**
1. Get API key from https://platform.openai.com/
2. Add to `.env`: `OPENAI_API_KEY=sk-your-key`
3. Set: `LLM_PROVIDER=openai`

#### **Option 2: Ollama (Local/Privacy)**
```powershell
# Install Ollama
# Download from: https://ollama.ai/
ollama serve

# Pull models
ollama pull llama2
ollama pull codellama

# Configure in .env
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
```

### 📧 **Email Setup (Gmail)**

#### **Step 1: Enable 2-Factor Authentication**
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification"

#### **Step 2: Generate App Password**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password (remove spaces!)

#### **Step 3: Configure Environment**
```env
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # 16-char app password, no spaces!
FROM_EMAIL=your_gmail@gmail.com
```

## 🔧 Configuration Options

### **LLM Provider Switching**
```env
# Switch between providers easily
LLM_PROVIDER=openai    # Production
LLM_PROVIDER=ollama    # Privacy/Local
```

### **Code Standards**
- Follow PEP 8 Python style guide
- Add docstrings to all functions
- Include tests for new features
- Update README for new configurations
