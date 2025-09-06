"""
Customer Service Chatbot with proper customer journey workflow
"""
import os
import json
import uuid
import requests
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI package directly (more reliable than LangChain)
try:
    if os.getenv("LLM_PROVIDER", "openai").lower() == "openai":
        import openai
        OPENAI_AVAILABLE = True
        print("✅ Using OpenAI package directly")
    else:
        OPENAI_AVAILABLE = False
        print("📝 Using Ollama provider - OpenAI not needed")
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI package not available - using Ollama only")

# Import Azure and Activity services
try:
    from app.services.azure_storage import AzureBlobStorageService
    from app.services.activity_service import ActivityService
    from app.services.email_service import EmailService
    from app.database import get_database
    AZURE_SERVICES_AVAILABLE = True
    EMAIL_SERVICE_AVAILABLE = True
    print("✅ Azure, Activity, and Email services available")
except ImportError as e:
    AZURE_SERVICES_AVAILABLE = False
    EMAIL_SERVICE_AVAILABLE = False
    print(f"⚠️ Azure/Activity/Email services not available: {e}")

# ===== CONFIGURATION =====
# Company Configuration
COMPANY_NAME = os.getenv("COMPANY_NAME", "Contoso")

# LLM Configuration  
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Embedding Model Configuration
# Using BAAI/bge-large-en-v1.5 as default for high-quality embeddings
EMBEDDING_MODEL_DEFAULT = 'BAAI/bge-large-en-v1.5'  # High quality, 1024 dimensions
EMBEDDING_MODEL_FAST = 'all-MiniLM-L6-v2'  # Fast fallback option, 384 dimensions
EMBEDDING_MODEL_FALLBACK = 'all-MiniLM-L6-v2'  # Fallback if main model fails


class CustomerState(Enum):
    UNKNOWN = "unknown"
    COLLECTING_INFO = "collecting_info"
    IDENTIFIED = "identified"
    HELPING_WITH_PURCHASE = "helping_with_purchase"
    PRODUCT_SEARCH = "product_search"
    PRODUCT_SUPPORT = "product_support"


class ChatMessage:
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()


class CustomerSession:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: List[ChatMessage] = []
        self.customer_state = CustomerState.UNKNOWN
        self.customer_info = {}
        self.customer_id = None
        self.recent_purchases = []
        self.selected_product = None
        self.debug_info = None  # Store debugging information
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        # Purchase pagination tracking
        self.purchase_offset = 0  # Track how many purchases we've already shown
        self.has_more_purchases = False  # Track if there are more purchases available
        self.all_purchases = []  # Store all retrieved purchases (up to 10)
        self.displayed_purchases = []  # Track which purchases are currently shown to user


class CustomerServiceBot:
    """Customer-facing chatbot with intelligent customer journey"""
    
    def __init__(self, embedding_model: str = None, debug_mode: bool = False):
        # LLM Configuration
        self.llm_provider = LLM_PROVIDER
        self.company_name = COMPANY_NAME
        
        # Initialize LLM based on provider
        if self.llm_provider == "openai" and OPENAI_AVAILABLE:
            self.openai_model = OPENAI_MODEL
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                print("⚠️ OpenAI API key not found, falling back to Ollama")
                self.llm_provider = "ollama"
            else:
                # Initialize OpenAI client directly
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                print(f"✅ Using OpenAI {self.openai_model}")
        
        # Ollama configuration (fallback or primary)
        if self.llm_provider == "ollama" or not OPENAI_AVAILABLE:
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")
            self.sql_model = os.getenv("OLLAMA_SQL_MODEL", "sqlcoder:7b")
            self.llm_provider = "ollama"  # Ensure it's set correctly
            print(f"✅ Using Ollama {self.chat_model}")
        
        # Set embedding model with smart defaults
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            # Use BGE large model by default for high-quality embeddings
            self.embedding_model = EMBEDDING_MODEL_DEFAULT
        
        self.debug_mode = debug_mode
        
        # Connection checks and preloading
        if self.llm_provider == "ollama":
            # Check Ollama connection on initialization
            self._check_ollama_connection()
            
            # Preload Ollama models during initialization
            if self.debug_mode:
                print("🚀 Preloading Ollama models...")
                self._preload_ollama_models()
        
        # Initialize vector store lazily (only when needed)
        self.vector_store = None
        
        # Database schema for customer service queries
        self.database_schema = """
        Database Schema (PostgreSQL):
        
        Table: customer
        - customer_id SERIAL PRIMARY KEY
        - first_name VARCHAR(50), last_name VARCHAR(50)
        - email VARCHAR(100) UNIQUE
        - phone VARCHAR(20)
        - city VARCHAR(50), state VARCHAR(50)
        
        Table: product  
        - product_id SERIAL PRIMARY KEY
        - product_name VARCHAR(100)
        - category VARCHAR(50)
        - type VARCHAR(50)
        - price DECIMAL(10, 2)
        - stock_quantity INT
        
        Table: sales
        - sale_id SERIAL PRIMARY KEY
        - customer_id INT REFERENCES customer(customer_id)
        - product_id INT REFERENCES product(product_id)
        - quantity INT
        - sale_date DATE
        - total_amount DECIMAL(10, 2)
        """
        
        if self.debug_mode:
            print(f"✅ Customer Service Bot initialized for {self.company_name}")
            print(f"✅ LLM Provider: {self.llm_provider}")
            print(f"✅ Embedding Model: {self.embedding_model}")
        else:
            print("✅ Customer Service Bot initialized")
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and models are available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model.get('name', '') for model in models]
                
                print("✅ Ollama connection successful")
                print(f"📋 Available models: {model_names}")
                
                # Check if required models are available
                if self.chat_model not in model_names:
                    print(f"⚠️ Warning: Chat model '{self.chat_model}' not found")
                if self.sql_model not in model_names:
                    print(f"⚠️ Warning: SQL model '{self.sql_model}' not found")
                    
                return True
            else:
                print(f"⚠️ Ollama server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            print("💡 Please ensure Ollama is running: 'ollama serve'")
            return False
    
    def _preload_ollama_models(self):
        """Preload Ollama models by sending a small test prompt"""
        try:
            print(f"🔄 Preloading chat model: {self.chat_model}")
            # Send a small test prompt to warm up the model
            self._call_ollama(self.chat_model, "Hi", max_tokens=1)
            print(f"✅ Chat model {self.chat_model} ready")
            
            print(f"🔄 Preloading SQL model: {self.sql_model}")
            # Send a small test prompt to warm up the SQL model
            self._call_ollama(self.sql_model, "SELECT 1", max_tokens=1)
            print(f"✅ SQL model {self.sql_model} ready")
            
        except Exception as e:
            print(f"⚠️ Model preload warning: {e}")
    
    def _call_llm(self, prompt: str, max_tokens: int = 300, conversation_history: List = None) -> str:
        """Unified method to call either OpenAI or Ollama based on provider"""
        if self.llm_provider == "openai" and hasattr(self, 'openai_client'):
            return self._call_openai(prompt, max_tokens, conversation_history)
        else:
            return self._call_ollama(self.chat_model, prompt, max_tokens)
    
    def _call_openai(self, prompt: str, max_tokens: int = 300, conversation_history: List = None) -> str:
        """Call OpenAI API using the openai package directly with conversation history"""
        try:
            system_prompt = f"""You are Yodha, a professional customer service representative for {self.company_name}.

CRITICAL BEHAVIORAL INSTRUCTIONS:
- You are ONLY Yodha speaking directly to the customer - NEVER write emails, letters, or formal documents
- NEVER start responses with "Dear [Customer]" or end with "Best Regards" or any email signature
- NEVER use phrases like "This can be an answer for", "Here is a response", or any meta-commentary
- You are having a direct conversation - speak naturally as yourself, not writing to someone
- **MANDATORY FORMATTING**: ALWAYS use **bold formatting** for:
  * Your main answer or direct response to the customer's question
  * Key product names, prices, and important specifications
  * Status information (available, in stock, warranty details, delivery times)
  * Action items and next steps
  * Any critical information the customer needs to know immediately
- Be direct, professional, and conversational - you are Yodha talking to a customer right now
- If you don't know something, say "I don't have that information" - don't elaborate on limitations"""

            # Build messages array starting with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        # Convert our ChatMessage objects to OpenAI format
                        role = "assistant" if msg.role == "assistant" else "user"
                        messages.append({"role": role, "content": msg.content})
            
            # Add the current user message
            messages.append({"role": "user", "content": prompt})

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content if response.choices[0].message.content else "I apologize, but I cannot generate a response right now."
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            return "I'm experiencing some technical difficulties. Please try again."

    def _call_ollama(self, model: str, prompt: str, max_tokens: int = 300) -> str:
        """Call Ollama API directly with improved error handling"""
        
        # Enhanced system instructions for Ollama models
        enhanced_prompt = f"""You are Yodha, a professional customer service representative for {self.company_name}.

CRITICAL INSTRUCTIONS FOR YOUR RESPONSE:
- You are ONLY Yodha speaking directly to a customer in a live conversation
- NEVER write emails, letters, or formal documents - you are talking to someone right now
- NEVER start with "Dear [Customer]" or end with "Best Regards" or signatures
- NEVER say "This can be an answer", "Here is a response", or similar meta-commentary
- Always highlight your main answer using **bold formatting** for key information
- Speak naturally and directly as Yodha - you are having a conversation, not writing a document
- Be professional but conversational - like talking to someone in person
- If you don't know something, simply say "I don't have that information"

Customer's message/question: {prompt}

Your direct response as Yodha (no email format, no meta-commentary, use **bold** for key points):"""

        try:
            # First, check if Ollama is accessible with a quick ping
            try:
                ping_response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if ping_response.status_code != 200:
                    return "Ollama server is not responding. Please ensure it's running."
            except requests.exceptions.RequestException:
                return "Cannot connect to Ollama server. Please ensure it's running on port 11434."
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": enhanced_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=60  # Increased from 30 to 60 seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'I apologize, but I cannot generate a response right now.')
            else:
                print(f"Ollama HTTP error: {response.status_code} - {response.text}")
                return "I'm experiencing some technical difficulties. Please try again."
                
        except requests.exceptions.Timeout:
            print("Ollama request timed out after 60 seconds")
            return "My response is taking longer than expected. Please try a simpler question or try again."
        except requests.exceptions.ConnectionError as e:
            print(f"Ollama connection error: {e}")
            return "I'm having trouble connecting to my systems. Please ensure Ollama is running and try again."
        except Exception as e:
            print(f"Ollama error: {e}")
            return "I'm having trouble connecting to my systems. Please try again in a moment."
    
    def _generate_welcome_message(self) -> str:
        """Generate a friendly welcome message"""
        welcome_prompt = f"""Generate a warm, welcoming greeting message as Yodha for {self.company_name} that:
- Says hello and introduces yourself as Yodha from {self.company_name}
- Asks how you can help them today
- Sounds natural and professional
- Is brief (1-2 sentences max)
- Uses **bold formatting** to highlight your name and company

CRITICAL: 
- You are speaking directly to a customer right now - NOT writing an email or letter
- NEVER use "Dear [Customer]" or "Best Regards" or any email format
- Just speak naturally as Yodha introducing yourself
- Use **bold** for your name and key information

Generate only the greeting message:"""
        
        return self._call_llm(welcome_prompt, 100)
    
    def _extract_customer_info(self, message: str) -> Dict[str, str]:
        """Extract customer information from message using regex"""
        info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            info['email'] = email_match.group()
        
        # Phone pattern (various formats)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, message)
        if phone_match:
            info['phone'] = phone_match.group()
        
        # Name patterns (simple extraction)
        name_patterns = [
            r"my name is ([A-Za-z]+(?:\s+[A-Za-z]+)*)",
            r"i'm ([A-Za-z]+(?:\s+[A-Za-z]+)*)",
            r"i am ([A-Za-z]+(?:\s+[A-Za-z]+)*)"
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, message.lower())
            if name_match:
                full_name = name_match.group(1)
                name_parts = full_name.split()
                if len(name_parts) >= 1:
                    info['first_name'] = name_parts[0].title()
                if len(name_parts) >= 2:
                    info['last_name'] = name_parts[-1].title()
                break
        
        return info
    
    def _detect_user_sentiment(self, message: str, conversation_history: List) -> str:
        """Detect if user seems happy, unhappy, or neutral"""
        sentiment_prompt = f"""Based on the conversation history and the user's final message, determine their sentiment.

User's final message: "{message}"

Analyze the sentiment and respond with ONLY one word:
- "unhappy" if they seem frustrated, dissatisfied, or negative
- "happy" if they seem satisfied, positive, or grateful  
- "neutral" if their sentiment is unclear or neutral

Response (one word only):"""
        
        # Use conversation history for better sentiment analysis
        recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        sentiment = self._call_llm(sentiment_prompt, 50, conversation_history=recent_history).strip().lower()
        return sentiment if sentiment in ['happy', 'unhappy', 'neutral'] else 'neutral'
    
    def _generate_closing_message(self, sentiment: str, product_name: str = None) -> str:
        """Generate appropriate closing message based on sentiment"""
        if sentiment == 'unhappy':
            # Apologetic closing with manufacturer contact
            contact_info = ""
            if product_name:
                contact_info = self._get_manufacturer_contact(product_name)
            
            closing_prompt = f"""Generate a professional closing message as Yodha for {self.company_name} where you:
- Gently apologize that you couldn't help them fully
- Provide manufacturer contact information if available: {contact_info}
- Wish them well and close the session professionally
- Use **bold formatting** for key information
- Keep it brief and sincere

CRITICAL: Speak directly as Yodha - NOT an email format, no "Dear" or "Best Regards"

Generate the closing message:"""
        else:
            # Happy or neutral closing
            closing_prompt = f"""Generate a friendly closing message as Yodha for {self.company_name} where you:
- Thank them for contacting {self.company_name}
- Wish them a good day
- Let them know they can return anytime
- Use **bold formatting** for key points
- Keep it brief and positive

CRITICAL: Speak directly as Yodha - NOT an email format, no "Dear" or "Best Regards"

Generate the closing message:"""
        
        return self._call_llm(closing_prompt, 150)
    
    def _database_lookup(self, info: Dict[str, str], offset: int = 0, limit: int = 5) -> Tuple[Optional[int], List[Dict], bool]:
        """Actual database lookup for customer ID and recent purchases with pagination"""
        import psycopg2
        
        try:
            # Get database connection
            DATABASE_URL = os.getenv("DATABASE_URL")
            if not DATABASE_URL:
                print("❌ DATABASE_URL not configured, using mock data")
                return self._mock_database_lookup_fallback(info, offset, limit)
            
            # Connect to database with short timeout
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=8)
            cursor = conn.cursor()
            
            # Build search query based on available info
            search_conditions = []
            search_params = []
            
            if info.get('email'):
                search_conditions.append("LOWER(email) = LOWER(%s)")
                search_params.append(info['email'])
            
            if info.get('phone'):
                # Clean phone number for matching
                clean_phone = re.sub(r'[^\d]', '', info['phone'])
                search_conditions.append("REGEXP_REPLACE(phone, '[^0-9]', '', 'g') = %s")
                search_params.append(clean_phone)
            
            if info.get('first_name') and info.get('last_name'):
                search_conditions.append("LOWER(first_name) = LOWER(%s) AND LOWER(last_name) = LOWER(%s)")
                search_params.extend([info['first_name'], info['last_name']])
            
            if not search_conditions:
                return None, [], False
            
            # Query to find customer
            customer_query = f"""
            SELECT customer_id, first_name, last_name, email, phone 
            FROM customer 
            WHERE {' OR '.join(search_conditions)}
            LIMIT 1;
            """
            
            cursor.execute(customer_query, search_params)
            customer_result = cursor.fetchone()
            
            if not customer_result:
                return None, [], False
            
            customer_id, first_name, last_name, email, phone = customer_result
            print(f"✅ Found customer: {first_name} {last_name} (ID: {customer_id})")
            
            # Query to get recent purchases with pagination
            purchases_query = """
            SELECT 
                p.product_id,
                p.product_name,
                p.category,
                p.type,
                p.price,
                s.quantity,
                s.total_amount,
                s.sale_date,
                s.sales_id
            FROM sales s
            JOIN product p ON s.product_id = p.product_id
            WHERE s.customer_id = %s
            ORDER BY s.sale_date DESC
            LIMIT %s OFFSET %s;
            """
            
            cursor.execute(purchases_query, (customer_id, limit, offset))
            purchase_results = cursor.fetchall()
            
            # Check if there are more purchases beyond current batch
            check_more_query = """
            SELECT COUNT(*)
            FROM sales s
            WHERE s.customer_id = %s
            """
            cursor.execute(check_more_query, (customer_id,))
            total_purchases = cursor.fetchone()[0]
            has_more = total_purchases > (offset + limit)
            
            # Format purchases - now including product_id
            recent_purchases = []
            for purchase in purchase_results:
                recent_purchases.append({
                    'product_id': purchase[0],      # Added product_id
                    'product_name': purchase[1],
                    'category': purchase[2],
                    'type': purchase[3],
                    'price': float(purchase[4]) if purchase[4] else 0.0,
                    'quantity': purchase[5],
                    'total_amount': float(purchase[6]) if purchase[6] else 0.0,
                    'sale_date': str(purchase[7]),
                    'sales_id': purchase[8]
                })
            
            print(f"✅ Found {len(recent_purchases)} recent purchases (offset: {offset}, has_more: {has_more})")
            
            # Update customer info with database data
            info.update({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone
            })
            
            cursor.close()
            conn.close()
            
            return customer_id, recent_purchases, has_more
            
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            # Fallback to mock data if database is unavailable
            return self._mock_database_lookup_fallback(info, offset, limit)
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
            return self._mock_database_lookup_fallback(info, offset, limit)
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def _mock_database_lookup_fallback(self, info: Dict[str, str], offset: int = 0, limit: int = 5) -> Tuple[Optional[int], List[Dict], bool]:
        """Fallback mock data when database is unavailable"""
        if info.get('email') or info.get('phone'):
            print(f"⚠️ Using mock data (database unavailable) - offset: {offset}, limit: {limit}")
            # Mock customer found
            customer_id = 12345
            
            # Extended mock purchase list for pagination testing
            all_mock_purchases = [
                {
                    'product_name': 'Wireless Headphones Pro',
                    'category': 'Electronics',
                    'type': 'Audio',
                    'price': 159.99,
                    'quantity': 1,
                    'total_amount': 159.99,
                    'sale_date': '2025-08-20',
                    'sales_id': 'MOCK-001'
                },
                {
                    'product_name': 'Smart Phone Case',
                    'category': 'Accessories',
                    'type': 'Protection',
                    'price': 29.99,
                    'quantity': 1,
                    'total_amount': 29.99,
                    'sale_date': '2025-08-15',
                    'sales_id': 'MOCK-002'
                },
                {
                    'product_name': 'USB-C Cable',
                    'category': 'Accessories',
                    'type': 'Cable',
                    'price': 19.99,
                    'quantity': 2,
                    'total_amount': 39.98,
                    'sale_date': '2025-08-10',
                    'sales_id': 'MOCK-003'
                },
                {
                    'product_name': 'Portable Charger',
                    'category': 'Electronics',
                    'type': 'Power',
                    'price': 49.99,
                    'quantity': 1,
                    'total_amount': 49.99,
                    'sale_date': '2025-08-05',
                    'sales_id': 'MOCK-004'
                },
                {
                    'product_name': 'Bluetooth Speaker',
                    'category': 'Electronics',
                    'type': 'Audio',
                    'price': 89.99,
                    'quantity': 1,
                    'total_amount': 89.99,
                    'sale_date': '2025-07-30',
                    'sales_id': 'MOCK-005'
                },
                {
                    'product_name': 'Screen Protector',
                    'category': 'Accessories',
                    'type': 'Protection',
                    'price': 12.99,
                    'quantity': 1,
                    'total_amount': 12.99,
                    'sale_date': '2025-07-25',
                    'sales_id': 'MOCK-006'
                },
                {
                    'product_name': 'Wireless Mouse',
                    'category': 'Electronics',
                    'type': 'Input',
                    'price': 35.99,
                    'quantity': 1,
                    'total_amount': 35.99,
                    'sale_date': '2025-07-20',
                    'sales_id': 'MOCK-007'
                },
                {
                    'product_name': 'Laptop Stand',
                    'category': 'Accessories',
                    'type': 'Support',
                    'price': 59.99,
                    'quantity': 1,
                    'total_amount': 59.99,
                    'sale_date': '2025-07-15',
                    'sales_id': 'MOCK-008'
                },
                {
                    'product_name': 'Webcam HD',
                    'category': 'Electronics',
                    'type': 'Video',
                    'price': 79.99,
                    'quantity': 1,
                    'total_amount': 79.99,
                    'sale_date': '2025-07-10',
                    'sales_id': 'MOCK-009'
                },
                {
                    'product_name': 'Gaming Keyboard',
                    'category': 'Electronics',
                    'type': 'Input',
                    'price': 129.99,
                    'quantity': 1,
                    'total_amount': 129.99,
                    'sale_date': '2025-07-05',
                    'sales_id': 'MOCK-010'
                }
            ]
            
            # Apply pagination
            recent_purchases = all_mock_purchases[offset:offset + limit]
            has_more = len(all_mock_purchases) > (offset + limit)
            
            return customer_id, recent_purchases, has_more
        
        return None, [], False
    
    def _search_products(self, query: str) -> List[Dict]:
        """Mock product search - would normally query database"""
        # This would generate SQL and query the product table
        mock_products = [
            {
                'product_name': 'Wireless Headphones Pro',
                'category': 'Electronics',
                'price': 159.99,
                'stock_quantity': 25
            },
            {
                'product_name': 'Smart Phone Case',
                'category': 'Accessories',
                'price': 29.99,
                'stock_quantity': 50
            },
            {
                'product_name': 'Bluetooth Speaker',
                'category': 'Electronics',
                'price': 89.99,
                'stock_quantity': 15
            }
        ]
        
        # Simple keyword matching (would use SQL LIKE/regex in real implementation)
        query_lower = query.lower()
        matching_products = [
            product for product in mock_products
            if any(keyword in product['product_name'].lower() or keyword in product['category'].lower()
                   for keyword in query_lower.split())
        ]
        
        return matching_products[:5]  # Limit to 5 results
    
    def _extract_product_from_input(self, message: str, purchases: List[Dict], session=None) -> Optional[str]:
        """Extract product name from user input (number or partial name) and store product_id in session"""
        message_lower = message.lower().strip()
        
        # Check if user provided a number (direct or with words like "product 7", "number 3")
        import re
        number_patterns = [
            r'^\d+$',  # Just a number: "7"
            r'product\s+(\d+)',  # "product 7"
            r'number\s+(\d+)',   # "number 7"
            r'item\s+(\d+)',     # "item 7"
            r'(\d+)(?:st|nd|rd|th)',  # "7th", "1st", "2nd", "3rd"
        ]
        
        user_number = None
        for pattern in number_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if pattern == r'^\d+$':
                    user_number = int(match.group(0))
                else:
                    user_number = int(match.group(1))
                break
        
        if user_number:
            # If we have session context, handle broader numbering (1-10)
            if session and hasattr(session, 'all_purchases') and hasattr(session, 'displayed_purchases'):
                # Check if user number is in the range 1-10 (all purchases)
                if 1 <= user_number <= len(session.all_purchases):
                    selected_purchase = session.all_purchases[user_number - 1]
                    # Store both product name and product_id in selected_product
                    if hasattr(session, 'selected_product'):
                        session.selected_product = {
                            'product_name': selected_purchase['product_name'],
                            'product_id': selected_purchase.get('product_id'),
                            'selected_method': 'number_selection',
                            'purchase_data': selected_purchase
                        }
                    return selected_purchase['product_name']
            
            # Fallback to direct index in displayed purchases (1-based)
            index = user_number - 1
            if 0 <= index < len(purchases):
                selected_purchase = purchases[index]
                # Store product info in session if available
                if session and hasattr(session, 'selected_product'):
                    session.selected_product = {
                        'product_name': selected_purchase['product_name'],
                        'product_id': selected_purchase.get('product_id'),
                        'selected_method': 'displayed_selection',
                        'purchase_data': selected_purchase
                    }
                return selected_purchase['product_name']
        
        # Check for partial product name matching
        search_list = purchases
        if session and hasattr(session, 'all_purchases'):
            # Search in all purchases for better matching
            search_list = session.all_purchases
            
        for purchase in search_list:
            product_name = purchase['product_name'].lower()
            # Check if any significant word from the message matches the product name
            message_words = [word for word in message_lower.split() if len(word) > 2]
            for word in message_words:
                if word in product_name:
                    # Store product info when found by name matching
                    if session and hasattr(session, 'selected_product'):
                        session.selected_product = {
                            'product_name': purchase['product_name'],
                            'product_id': purchase.get('product_id'),
                            'selected_method': 'name_matching',
                            'purchase_data': purchase
                        }
                    return purchase['product_name']
        
        return None
    
    def _search_product_documentation(self, product_name: str, question: str, return_debug_info: bool = False) -> Optional[str]:
        """Search for product information in uploaded PDFs with optional debugging info"""
        debug_info = {
            'chunks_searched': 0,
            'relevant_chunks_found': 0,
            'top_chunks': [],
            'search_scores': [],
            'model_used': '',
            'filter_keywords': []
        }
        
        try:
            from pathlib import Path
            import pickle
            import faiss
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            # Check if FAISS index exists
            index_dir = Path("data/index")
            faiss_index_path = index_dir / "faiss_vector_store.index"
            faiss_meta_path = index_dir / "faiss_vector_store.pkl"
            
            if not (faiss_index_path.exists() and faiss_meta_path.exists()):
                if return_debug_info:
                    debug_info['error'] = 'FAISS index not found'
                    return "NO_INDEX_AVAILABLE", debug_info
                return "NO_INDEX_AVAILABLE"
            
            # Load metadata and determine which model was used for embeddings
            with open(faiss_meta_path, 'rb') as f:
                metadata = pickle.load(f)
            
            chunks = metadata['chunks']
            stored_model_name = metadata.get('model_name', EMBEDDING_MODEL_FALLBACK)
            debug_info['chunks_searched'] = len(chunks)
            debug_info['model_used'] = stored_model_name
            
            # Filter chunks that might relate to the product
            relevant_chunks = []
            product_words = product_name.lower().split()
            debug_info['filter_keywords'] = product_words
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                # If any product word appears in the chunk, consider it relevant
                if any(word in chunk_lower for word in product_words if len(word) > 2):
                    relevant_chunks.append(chunk)
            
            debug_info['relevant_chunks_found'] = len(relevant_chunks)
            
            if not relevant_chunks:
                if return_debug_info:
                    debug_info['error'] = f'No relevant chunks found for product: {product_name}'
                    return "PRODUCT_NOT_IN_INDEX", debug_info
                return "PRODUCT_NOT_IN_INDEX"
            
            # Use the instance's configured embedding model instead of stored model
            # This allows for runtime model switching and avoids timeout issues
            model_to_use = self.embedding_model
            
            # Only use stored model if it matches our current configuration
            if stored_model_name == self.embedding_model:
                try:
                    if self.debug_mode:
                        print(f"Loading embedding model: {stored_model_name}")
                    model = SentenceTransformer(stored_model_name)
                    debug_info['model_used'] = stored_model_name
                except Exception as e:
                    if self.debug_mode:
                        print(f"Failed to load {stored_model_name}, falling back to {EMBEDDING_MODEL_FALLBACK}")
                    model = SentenceTransformer(EMBEDDING_MODEL_FALLBACK)
                    debug_info['model_used'] = f"{EMBEDDING_MODEL_FALLBACK} (fallback)"
            else:
                # Use configured model (different from stored model)
                try:
                    if self.debug_mode:
                        print(f"Using configured embedding model: {self.embedding_model}")
                    model = SentenceTransformer(self.embedding_model)
                    debug_info['model_used'] = self.embedding_model
                    debug_info['model_switch'] = f"Switched from {stored_model_name} to {self.embedding_model}"
                except Exception as e:
                    if self.debug_mode:
                        print(f"Failed to load {self.embedding_model}, falling back to {EMBEDDING_MODEL_FALLBACK}")
                    model = SentenceTransformer(EMBEDDING_MODEL_FALLBACK)
                    debug_info['model_used'] = f"{EMBEDDING_MODEL_FALLBACK} (fallback)"
                
            question_embedding = model.encode([question])
            
            # Get embeddings for relevant chunks
            relevant_embeddings = model.encode(relevant_chunks)
            
            # Create temporary index for relevant chunks
            temp_index = faiss.IndexFlatL2(relevant_embeddings.shape[1])
            temp_index.add(relevant_embeddings.astype('float32'))
            
            # Search for most similar chunks (increased from 3 to 5 for better context)
            k = min(5, len(relevant_chunks))  # Get top 5 relevant chunks
            distances, indices = temp_index.search(question_embedding.astype('float32'), k)
            
            # Store debug info about search results
            debug_info['search_scores'] = [float(dist) for dist in distances[0]]
            
            # Combine top chunks for context with better organization
            context_chunks = [relevant_chunks[i] for i in indices[0]]
            debug_info['top_chunks'] = [
                {
                    'chunk_text': chunk[:200] + "..." if len(chunk) > 200 else chunk,
                    'full_chunk': chunk,
                    'score': float(distances[0][idx]),
                    'chunk_index': int(indices[0][idx])
                }
                for idx, chunk in enumerate(context_chunks)
            ]
            
            # Filter out very similar chunks to avoid redundancy
            filtered_chunks = []
            for chunk in context_chunks:
                # Only add if it's not too similar to already added chunks
                is_unique = True
                for existing in filtered_chunks:
                    if len(set(chunk.split()) & set(existing.split())) / len(set(chunk.split()) | set(existing.split())) > 0.8:
                        is_unique = False
                        break
                if is_unique:
                    filtered_chunks.append(chunk)
            
            context = "\n\n---\n\n".join(filtered_chunks)
            debug_info['final_context_length'] = len(context)
            debug_info['filtered_chunks_count'] = len(filtered_chunks)
            
            # Generate answer using the enhanced context
            prompt = f"""Based on the following product documentation for {product_name}, answer the customer's question as Yodha from {self.company_name}.

Product Documentation:
{context}

Customer Question: {question}

Instructions:
- Speak directly as Yodha helping a customer (NOT writing an email or formal document)
- Use **bold formatting** to highlight your main answer and key information
- Provide helpful and accurate answer based ONLY on the information provided above
- If specific information is not available in the documentation, clearly state that
- Be concise but thorough
- NEVER use "Dear Customer" or "Best Regards" or email formatting
- Sound natural and conversational

Your response as Yodha:"""

            debug_info['prompt_length'] = len(prompt)
            answer = self._call_llm(prompt, 500)  # Increased token limit
            
            if return_debug_info:
                return answer, debug_info
            return answer
            
        except Exception as e:
            print(f"Error searching product documentation: {e}")
            if return_debug_info:
                debug_info['error'] = str(e)
                return "SEARCH_ERROR", debug_info
            return "SEARCH_ERROR"
    
    def _get_manufacturer_contact(self, product_name: str) -> Optional[str]:
        """Extract manufacturer contact info from PDFs"""
        try:
            from pathlib import Path
            import pickle
            
            # Check if FAISS index exists
            index_dir = Path("data/index")
            faiss_meta_path = index_dir / "faiss_vector_store.pkl"
            
            if not faiss_meta_path.exists():
                return None
            
            # Load metadata
            with open(faiss_meta_path, 'rb') as f:
                metadata = pickle.load(f)
            
            chunks = metadata['chunks']
            
            # Look for contact information in chunks related to the product
            product_words = product_name.lower().split()
            contact_keywords = ['contact', 'support', 'phone', 'email', 'customer service', 'manufacturer']
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                # Check if chunk relates to product and contains contact info
                has_product = any(word in chunk_lower for word in product_words if len(word) > 2)
                has_contact = any(keyword in chunk_lower for keyword in contact_keywords)
                
                if has_product and has_contact:
                    # Extract contact information
                    lines = chunk.split('\n')
                    contact_lines = []
                    for line in lines:
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in contact_keywords):
                            contact_lines.append(line.strip())
                    
                    if contact_lines:
                        return "For further assistance, please contact the manufacturer:\n" + "\n".join(contact_lines[:3])
            
            # If no specific contact info found, provide general guidance
            return f"For further assistance with {product_name}, please contact the manufacturer directly. You can usually find contact information on:\n- The product packaging or manual\n- The manufacturer's official website\n- Customer support section of their website"
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
            return "Please contact the manufacturer for further assistance."
    
    def _generate_contextual_response(self, message: str, session: CustomerSession) -> str:
        """Generate appropriate response based on customer state and message with full conversation history"""
        
        # Create a context-aware prompt that includes customer state information
        context_prompt = f"""You are having a live conversation with a customer of {self.company_name}. 

Current conversation context:
- Customer State: {session.customer_state.value}
- Customer Info: {session.customer_info}
- Customer ID: {session.customer_id if session.customer_id else 'Not identified'}

Please respond naturally to their message while keeping this context in mind. Use **bold formatting** for key information."""
        
        # Use the conversation history for context (last 10 messages to avoid token limits)
        recent_history = session.messages[-10:] if len(session.messages) > 10 else session.messages
        
        return self._call_llm(context_prompt, 200, conversation_history=recent_history)
    
    def _detect_session_closing(self, message: str) -> bool:
        """Detect if the user wants to close the session using contextual analysis."""
        message_lower = message.lower().strip()
        
        # Add debug logging
        print(f"🔍 Checking session closing for message: '{message}'")
        
        # Strong closure indicators (definitive)
        strong_closers = [
            'goodbye', 'bye', 'see you', 'farewell', 'talk later',
            'end chat', 'close', 'exit', 'quit', 'stop',
            'that\'s all', 'all set', 'i\'m done', 'finished',
            'solved everything', 'that solved it', 'close session',
            'end session', 'close chat'
        ]
        
        # Check for strong closure indicators first
        for closer in strong_closers:
            if closer in message_lower:
                print(f"✅ Strong closure detected: '{closer}'")
                return True
        
        # Simple "I'm good" patterns that should trigger closure (with context checks)
        simple_good_patterns = [
            'i\'m good', 'im good', 'i am good', 'all good',
            'i\'m all set', 'im all set', 'i am all set',
            'i\'m okay', 'im okay', 'i am okay'
        ]
        
        for pattern in simple_good_patterns:
            if pattern in message_lower:
                # Check if it's NOT followed by "at", "with", "for" etc. (skill/ability contexts)
                pattern_index = message_lower.find(pattern)
                after_pattern = message_lower[pattern_index + len(pattern):].strip()
                
                # Skip if followed by ability/skill indicators
                ability_indicators = ['at', 'with', 'for', 'about', 'regarding', 'on', 'in']
                if any(after_pattern.startswith(indicator) for indicator in ability_indicators):
                    continue
                
                # Check for continuation words that suggest they want more help
                continuation_words = ['but', 'however', 'can you', 'what about', 'could you', 'would you', 'help me', 'question', 'also', 'and']
                has_continuation = any(word in message_lower for word in continuation_words)
                
                if not has_continuation:
                    print(f"✅ Simple 'good' pattern detected: '{pattern}' (context-aware)")
                    return True
        
        # Contextual closure patterns - these indicate satisfaction and goodbye
        contextual_patterns = [
            # "I am good" patterns - indicating satisfaction after receiving help
            ('i am good', 'thank'),
            ('i\'m good', 'thank'),
            ('im good', 'thank'),
            ('all good', 'thank'),
            
            # "I have what I need" patterns
            ('i have what i need', 'thank'),
            ('that\'s what i needed', 'thank'),
            ('got what i needed', 'thank'),
            
            # Satisfaction + gratitude patterns
            ('perfect', 'thank'),
            ('excellent', 'thank'),
            ('great', 'thank'),
            ('wonderful', 'thank'),
            
            # Resolution + gratitude patterns
            ('problem solved', 'thank'),
            ('issue resolved', 'thank'),
            ('all resolved', 'thank'),
            ('everything is clear', 'thank'),
        ]
        
        # Check contextual patterns
        for pattern, gratitude_word in contextual_patterns:
            if pattern in message_lower and gratitude_word in message_lower:
                # Make sure it's not a continuation (asking for more help)
                continuation_words = ['but', 'however', 'can you', 'what about', 'next', 'more', 'else', 'another', 'also', 'additionally']
                has_continuation = any(word in message_lower for word in continuation_words)
                if not has_continuation:
                    return True
        
        # Gratitude + completion (original logic enhanced)
        gratitude_words = ['thank', 'thanks', 'appreciate', 'grateful']
        completion_words = ['perfect', 'great', 'excellent', 'solved', 'fixed', 'resolved', 'complete', 'done']
        continuation_words = ['but', 'however', 'can you', 'what about', 'next', 'more', 'else', 'another']
        
        has_gratitude = any(word in message_lower for word in gratitude_words)
        has_completion = any(word in message_lower for word in completion_words)
        has_continuation = any(word in message_lower for word in continuation_words)
        
        # Trigger closure if gratitude + completion WITHOUT continuation indicators
        if has_gratitude and has_completion and not has_continuation:
            return True
        
        # Special case: very polite endings
        polite_endings = [
            'thank you very much',
            'thanks so much',
            'thank you so much',
            'much appreciated',
            'really appreciate',
            'thanks a lot'
        ]
        
        for ending in polite_endings:
            if ending in message_lower:
                # If it's a polite thank you without asking for more, it's likely closure
                continuation_words = ['but', 'however', 'can you', 'what about', 'could you', 'would you', 'help me', 'question']
                has_continuation = any(word in message_lower for word in continuation_words)
                if not has_continuation:
                    print(f"✅ Polite ending detected: '{ending}'")
                    return True
        
        print(f"❌ No session closing pattern detected for: '{message}'")
        return False
    
    def _detect_user_sentiment(self, message: str, conversation_history: List) -> str:
        """Detect user sentiment to customize closing message."""
        positive_indicators = ['thanks', 'thank you', 'helpful', 'great', 'excellent', 'solved', 'resolved', 'appreciate']
        negative_indicators = ['frustrated', 'unhappy', 'disappointed', 'problem', 'issue', 'not happy', 'angry']
        
        message_lower = message.lower()
        
        # Check recent conversation for sentiment
        recent_messages = [msg.content.lower() for msg in conversation_history[-5:] if hasattr(msg, 'content')]
        all_text = message_lower + ' ' + ' '.join(recent_messages)
        
        positive_score = sum(1 for word in positive_indicators if word in all_text)
        negative_score = sum(1 for word in negative_indicators if word in all_text)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _generate_closing_message(self, sentiment: str, product_name: Optional[str] = None) -> str:
        """Generate appropriate closing message based on sentiment."""
        company_name = COMPANY_NAME
        
        if sentiment == 'positive':
            messages = [
                f"Thank you for choosing {company_name}! I'm glad I could help you today. Have a wonderful day! 😊",
                f"It was my pleasure helping you today! Thanks for being a valued {company_name} customer. Take care! 🌟",
                f"Great to hear everything is resolved! Thank you for contacting {company_name}. Enjoy your day! ✨"
            ]
        elif sentiment == 'negative':
            messages = [
                f"I apologize if we couldn't fully resolve your concerns today. Please don't hesitate to contact us again. {company_name} values your feedback.",
                f"Thank you for your patience today. If you need further assistance, our customer service team is always here to help.",
                f"I understand your frustration. Please know that {company_name} is committed to making things right. Feel free to reach out anytime."
            ]
        else:
            messages = [
                f"Thank you for contacting {company_name} today. If you need any further assistance, feel free to reach out anytime!",
                f"Thanks for chatting with me today! {company_name} is always here when you need us. Have a great day!",
                f"It was good helping you today. Remember, {company_name} customer service is available whenever you need us!"
            ]
        
        import random
        base_message = random.choice(messages)
        
        if product_name:
            base_message += f"\n\nFor future reference about your {product_name}, you can always contact our support team."
        
        return base_message
    
    def _get_customer_details(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer details including email from the database.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with customer details or None if not found
        """
        try:
            from sqlalchemy import text
            db = next(get_database())
            
            # Use raw SQL to get customer details
            result = db.execute(
                text("SELECT customer_id, first_name, last_name, email, phone FROM customer WHERE customer_id = :customer_id"),
                {"customer_id": customer_id}
            ).fetchone()
            
            db.close()
            
            if result:
                return {
                    'customer_id': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'email': result[3],
                    'phone': result[4],
                    'full_name': f"{result[1]} {result[2]}"
                }
            else:
                print(f"Customer {customer_id} not found in database")
                return None
                
        except Exception as e:
            print(f"Error getting customer details: {e}")
            return None

    def close_session_and_store_conversation(self, session: CustomerSession, close_reason: str = "user_requested") -> Tuple[str, bool]:
        """
        Close the session and store conversation to Azure Blob Storage and Activity table.
        
        Args:
            session: The customer session to close
            close_reason: Reason for closing ('user_requested' or 'ui_closed')
            
        Returns:
            Tuple of (closing_message, success_status)
        """
        try:
            if not AZURE_SERVICES_AVAILABLE:
                print("⚠️ Azure services not available - cannot store conversation")
                return "Thank you for using our service. Have a great day!", False
            
            # Generate closing message if not already generated
            if close_reason == "user_requested":
                # Detect sentiment from last message
                last_user_message = next((msg.content for msg in reversed(session.messages) if msg.role == "user"), "")
                sentiment = self._detect_user_sentiment(last_user_message, session.messages)
                
                # Get product name from selected_product (handle both old string format and new dict format)
                selected_product = getattr(session, 'selected_product', None)
                if isinstance(selected_product, dict):
                    product_name = selected_product.get('product_name')
                else:
                    product_name = selected_product
                    
                closing_message = self._generate_closing_message(sentiment, product_name)
            else:
                closing_message = f"Thank you for using {COMPANY_NAME} customer service. Your conversation has been saved for our records."
            
            # Create Azure Blob Storage service
            azure_service = AzureBlobStorageService()
            
            # Generate conversation data
            conversation_data = azure_service.generate_conversation_data(session, session.customer_id)
            
            # Upload to Azure Blob Storage
            blob_url = azure_service.upload_conversation_file(session.session_id, conversation_data)
            
            if not blob_url:
                print("❌ Failed to upload conversation to Azure Blob Storage")
                return closing_message, False
            
            # Store activity in database if customer is identified
            activity_id = None
            if session.customer_id:
                try:
                    db = next(get_database())
                    
                    # Get product_id if available
                    product_id = None
                    if hasattr(session, 'selected_product') and session.selected_product:
                        if isinstance(session.selected_product, dict) and 'product_id' in session.selected_product:
                            product_id = session.selected_product['product_id']
                    
                    # Create activity record
                    activity_id = ActivityService.create_chatbot_activity(
                        db=db,
                        customer_id=session.customer_id,
                        session_id=session.session_id,
                        url_data=blob_url,
                        product_id=product_id,
                        description=f"Customer service chat session - {len(session.messages)} messages",
                        comments=f"Session closed by {close_reason.replace('_', ' ')}"
                    )
                    
                    if activity_id:
                        # Update activity with conversation summary
                        ActivityService.update_activity_with_conversation_summary(
                            db=db,
                            activity_id=activity_id,
                            conversation_summary=conversation_data
                        )
                        print(f"✅ Activity record created with ID: {activity_id}")
                    else:
                        print("⚠️ Failed to create activity record")
                    
                    db.close()
                    
                except Exception as db_error:
                    print(f"❌ Database error: {db_error}")
                    # Don't fail the whole process for DB errors
            
            # Send email notification to customer
            if session.customer_id and EMAIL_SERVICE_AVAILABLE:
                try:
                    # Get customer details including email
                    customer_details = self._get_customer_details(session.customer_id)
                    
                    if customer_details and customer_details.get('email'):
                        email_service = EmailService()
                        
                        # Get product name from selected_product
                        product_name = None
                        if hasattr(session, 'selected_product') and session.selected_product:
                            if isinstance(session.selected_product, dict):
                                product_name = session.selected_product.get('product_name')
                            else:
                                product_name = session.selected_product
                        
                        # Send conversation email with full content
                        email_sent = email_service.send_conversation_with_content_email(
                            customer_email=customer_details['email'],
                            customer_name=customer_details['full_name'],
                            session_id=session.session_id,
                            conversation_messages=session.messages,
                            product_name=product_name,
                            activity_id=activity_id
                        )
                        
                        if email_sent:
                            print(f"✅ Conversation summary email sent to {customer_details['email']}")
                        else:
                            print(f"⚠️ Failed to send email to {customer_details['email']}")
                    else:
                        print(f"⚠️ No email address found for customer {session.customer_id}")
                        
                except Exception as email_error:
                    print(f"❌ Email error: {email_error}")
                    # Don't fail the whole process for email errors
            
            print(f"✅ Conversation stored successfully at: {blob_url}")
            return closing_message, True
            
        except Exception as e:
            print(f"❌ Error closing session and storing conversation: {e}")
            import traceback
            traceback.print_exc()
            return f"Thank you for using {COMPANY_NAME} customer service. Have a great day!", False
    
    def process_message(self, message: str, session: CustomerSession, debug_mode: bool = False) -> Tuple[str, CustomerSession]:
        """Process customer message and return appropriate response with optional debug info"""
        
        print(f"🔍 Processing message: '{message}'")
        
        # Check if user wants to close the session
        if self._detect_session_closing(message):
            print("🔚 Session closing detected! Initiating closure process...")
            # Close session and store conversation
            closing_response, storage_success = self.close_session_and_store_conversation(session, "user_requested")
            
            # Mark session as closed
            session.customer_state = CustomerState.UNKNOWN
            session.messages.append(ChatMessage("assistant", closing_response))
            session.updated_at = datetime.now()
            
            if storage_success:
                print("✅ Session closed and conversation stored successfully")
            else:
                print("⚠️ Session closed but conversation storage failed")
            
            return closing_response, session
        
        print("➡️ Continuing with normal message processing...")
        # Add user message to session
        session.messages.append(ChatMessage("user", message))
        session.updated_at = datetime.now()
        
        response = ""
        debug_info = None
        
        # State machine logic
        if session.customer_state == CustomerState.UNKNOWN:
            if not message.strip():
                # Empty message - just return welcome without changing state
                response = self._generate_welcome_message()
                session.customer_state = CustomerState.COLLECTING_INFO
            elif len(session.messages) == 1:
                # First real user interaction - welcome and ask for info
                response = self._generate_welcome_message()
                session.customer_state = CustomerState.COLLECTING_INFO
            else:
                # Try to extract customer info
                extracted_info = self._extract_customer_info(message)
                
                if extracted_info:
                    session.customer_info.update(extracted_info)
                    
                    # Try to find customer in database - get ALL purchases (up to 10) but show only first 5
                    customer_id, all_purchases, has_more = self._database_lookup(session.customer_info, offset=0, limit=10)
                    
                    if customer_id:
                        session.customer_id = customer_id
                        session.all_purchases = all_purchases  # Store all purchases
                        session.displayed_purchases = all_purchases[:5]  # Show first 5
                        session.recent_purchases = session.displayed_purchases  # For backward compatibility
                        session.customer_state = CustomerState.IDENTIFIED
                        session.has_more_purchases = len(all_purchases) > 5
                        
                        # Welcome back message with first 5 recent purchases
                        name = session.customer_info.get('first_name', 'there')
                        response = f"Great to hear from you again, {name}! I can see your recent purchases:\n\n"
                        
                        for i, purchase in enumerate(session.displayed_purchases, 1):
                            response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                        
                        response += "\nWhich specific item do you need help with? You can tell me the number (1-5) or the product name."
                        session.customer_state = CustomerState.PRODUCT_SUPPORT
                    
                    else:
                        response = f"I have your {', '.join(extracted_info.keys())} now. Let me gather a bit more information to better assist you. Could you share your full name and phone number?"
                else:
                    # Ask for customer information
                    response = "To better assist you, could you please share your email address or phone number so I can look up your account?"
        
        elif session.customer_state == CustomerState.COLLECTING_INFO:
            # Continue collecting customer information
            extracted_info = self._extract_customer_info(message)
            session.customer_info.update(extracted_info)
            
            # Check if we have enough info now
            if session.customer_info.get('email') or session.customer_info.get('phone'):
                customer_id, all_purchases, has_more = self._database_lookup(session.customer_info, offset=0, limit=10)
                
                if customer_id:
                    session.customer_id = customer_id
                    session.all_purchases = all_purchases  # Store all purchases
                    session.displayed_purchases = all_purchases[:5]  # Show first 5
                    session.recent_purchases = session.displayed_purchases  # For backward compatibility
                    session.customer_state = CustomerState.IDENTIFIED
                    session.has_more_purchases = len(all_purchases) > 5
                    
                    name = session.customer_info.get('first_name', 'there')
                    response = f"Perfect, {name}! I found your account. Here are your recent purchases:\n\n"
                    
                    for i, purchase in enumerate(session.displayed_purchases, 1):
                        response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                    
                    response += "\nWhich specific item do you need help with? You can tell me the number (1-5) or the product name."
                    session.customer_state = CustomerState.PRODUCT_SUPPORT
                else:
                    response = "I don't see an existing account with that information. No problem! How can I help you today? Are you looking for information about our products?"
                    session.customer_state = CustomerState.PRODUCT_SEARCH
            else:
                response = "Could you please provide your email address or phone number so I can look up your account?"
        
        elif session.customer_state == CustomerState.IDENTIFIED:
            # Customer is identified, help with their needs
            message_lower = message.lower()
            
            # Check if they're asking about products
            product_keywords = ['product', 'item', 'buy', 'purchase', 'looking for', 'need', 'want', 'show me', 'find']
            if any(keyword in message_lower for keyword in product_keywords):
                session.customer_state = CustomerState.PRODUCT_SEARCH
                products = self._search_products(message)
                
                if products:
                    response = "Here are some products that might interest you:\n\n"
                    for product in products:
                        response += f"• {product['product_name']} ({product['category']}) - ${product['price']} (Stock: {product['stock_quantity']})\n"
                    response += "\nWould you like more details about any of these items?"
                else:
                    response = "I'd be happy to help you find products! What specifically are you looking for?"
            
            # Check if they're asking about recent purchases
            elif any(word in message_lower for word in ['issue', 'problem', 'help', 'support', 'return', 'exchange']):
                session.customer_state = CustomerState.HELPING_WITH_PURCHASE
                response = "I'm here to help! Which of your recent purchases do you need assistance with?\n\n"
                start_num = 1 if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5] else 6
                for i, purchase in enumerate(session.displayed_purchases, start_num):
                    response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
            
            else:
                response = self._generate_contextual_response(message, session)
        
        elif session.customer_state == CustomerState.PRODUCT_SEARCH:
            # Help with product search
            products = self._search_products(message)
            
            if products:
                response = "Here are the products I found for you:\n\n"
                for product in products:
                    response += f"• {product['product_name']} ({product['category']}) - ${product['price']} (Stock: {product['stock_quantity']})\n"
                response += "\nWould you like more information about any of these products?"
            else:
                response = "I couldn't find products matching that description. Could you try different keywords or let me know what category you're interested in?"
        
        elif session.customer_state == CustomerState.HELPING_WITH_PURCHASE:
            # Help with purchase issues
            response = self._generate_contextual_response(message, session)
        
        elif session.customer_state == CustomerState.PRODUCT_SUPPORT:
            # Handle specific product support
            if session.selected_product:
                # Check if user wants to switch to a different product (could be from any range 1-10)
                new_product = self._extract_product_from_input(message, session.displayed_purchases, session)
                
                # Get current product name for comparison
                current_product_name = session.selected_product.get('product_name') if isinstance(session.selected_product, dict) else session.selected_product
                
                if new_product and new_product != current_product_name:
                    # User is switching to a different product - determine which range it's in
                    # Note: session.selected_product is now updated in _extract_product_from_input
                    
                    # Find which range this product is in and update displayed purchases accordingly
                    product_index = next((i for i, p in enumerate(session.all_purchases) if p['product_name'] == new_product), -1)
                    
                    if product_index != -1:
                        if product_index < 5:
                            # Product is in range 1-5, show 1-5 if not already showing
                            if not (len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5]):
                                session.displayed_purchases = session.all_purchases[:5]
                                session.recent_purchases = session.displayed_purchases
                                session.has_more_purchases = len(session.all_purchases) > 5
                                response = f"I'll help you with {new_product}. Here are your purchases 1-5 for reference:\n\n"
                                for i, purchase in enumerate(session.displayed_purchases, 1):
                                    response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                                response += f"\nWhat specific question or issue do you have with {new_product}?"
                            else:
                                response = f"I'll help you with {new_product}. What specific question or issue do you have with this product?"
                        else:
                            # Product is in range 6-10, show 6-10 if not already showing
                            if not (len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[5:10]):
                                session.displayed_purchases = session.all_purchases[5:10]
                                session.recent_purchases = session.displayed_purchases
                                session.has_more_purchases = False
                                response = f"I'll help you with {new_product}. Here are your purchases 6-10 for reference:\n\n"
                                for i, purchase in enumerate(session.displayed_purchases, 6):
                                    response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                                response += f"\nWhat specific question or issue do you have with {new_product}?"
                            else:
                                response = f"I'll help you with {new_product}. What specific question or issue do you have with this product?"
                    else:
                        response = f"I'll help you with {new_product}. What specific question or issue do you have with this product?"
                
                elif any(word in message.lower() for word in ['different', 'other', 'switch', 'change', 'another', 'previous', 'earlier']):
                    # User wants to switch but didn't specify which product - show current range
                    start_num = 1 if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5] else 6
                    end_range = "1-5" if start_num == 1 else "6-10"
                    
                    response = f"Sure! Which product from your recent purchases would you like help with? (Currently showing {end_range}):\n\n" + \
                             "\n".join([f"{i+start_num}. {purchase['product_name']} - {purchase['sale_date']}" 
                                      for i, purchase in enumerate(session.displayed_purchases)])
                    
                    # Offer to show the other range if available
                    if start_num == 1 and len(session.all_purchases) > 5:
                        response += "\n\nOr say 'show 6-10' to see your other recent purchases."
                    elif start_num == 6:
                        response += "\n\nOr say 'show 1-5' to see your earlier purchases."
                    
                    session.selected_product = None
                
                # Check for explicit range switching requests
                elif any(phrase in message.lower() for phrase in ['show 1-5', 'show 1 to 5', 'first 5', 'earlier purchases', 'previous 5']):
                    # User wants to see purchases 1-5
                    session.displayed_purchases = session.all_purchases[:5]
                    session.recent_purchases = session.displayed_purchases
                    session.has_more_purchases = len(session.all_purchases) > 5
                    session.selected_product = None
                    
                    response = "Here are your purchases 1-5:\n\n"
                    for i, purchase in enumerate(session.displayed_purchases, 1):
                        response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                    response += "\nWhich specific item do you need help with? You can tell me the number (1-5) or the product name."
                
                elif any(phrase in message.lower() for phrase in ['show 6-10', 'show 6 to 10', 'next 5', 'later purchases', 'more recent']):
                    # User wants to see purchases 6-10
                    if len(session.all_purchases) > 5:
                        session.displayed_purchases = session.all_purchases[5:10]
                        session.recent_purchases = session.displayed_purchases
                        session.has_more_purchases = False
                        session.selected_product = None
                        
                        response = "Here are your purchases 6-10:\n\n"
                        for i, purchase in enumerate(session.displayed_purchases, 6):
                            response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                        response += "\nWhich specific item do you need help with? You can tell me the number (6-10) or the product name."
                    else:
                        response = "You only have 5 recent purchases. All of them are already shown above."
                
                # Check for requests beyond available range (11+)
                elif any(phrase in message.lower() for phrase in ['product 11', 'product 12', 'item 11', 'item 12', 'number 11', 'number 12']) or \
                     any(f'product {i}' in message.lower() or f'item {i}' in message.lower() or f'number {i}' in message.lower() 
                         for i in range(11, 21)):  # Check for 11-20
                    response = "I can only access your 10 most recent purchases. If you're looking for an older purchase, please contact our support team directly, and they can help you with your complete purchase history."
                else:
                    # Answer the question about the currently selected product
                    # Get product name from selected_product dictionary
                    current_product_name = session.selected_product.get('product_name') if isinstance(session.selected_product, dict) else session.selected_product
                    
                    # Try to find answer in PDF documentation
                    if debug_mode:
                        answer, debug_info = self._search_product_documentation(current_product_name, message, return_debug_info=True)
                        session.debug_info = debug_info  # Store debug info in session
                    else:
                        answer = self._search_product_documentation(current_product_name, message)
                    
                    if answer and "not available" not in answer.lower() and "could not find" not in answer.lower() and answer not in ["PRODUCT_NOT_IN_INDEX", "NO_INDEX_AVAILABLE", "SEARCH_ERROR"]:
                        response = answer
                    elif answer == "PRODUCT_NOT_IN_INDEX":
                        # Product not found in the index - provide specific message
                        response = f"I don't have information about {current_product_name} in my current knowledge base. Is there anything else I can help you with today?"
                    elif answer == "NO_INDEX_AVAILABLE":
                        # No product documentation available at all
                        response = "I don't have access to product documentation at the moment. Is there anything else I can help you with today?"
                    elif answer == "SEARCH_ERROR":
                        # Error during search
                        response = "I'm having trouble accessing the product information right now. Is there anything else I can help you with today?"
                    else:
                        # If no answer found in documentation, provide manufacturer contact
                        contact_info = self._get_manufacturer_contact(current_product_name)
                        response = f"I couldn't find specific information about that issue with {current_product_name} in our documentation. {contact_info}\n\nFeel free to ask me about other aspects of this product or select a different product from your purchase history."
            else:
                # No product selected yet, try to extract product from user message
                selected_product = self._extract_product_from_input(message, session.displayed_purchases, session)
                
                if selected_product:
                    # _extract_product_from_input already set session.selected_product as dictionary
                    response = f"I'll help you with {selected_product}. What specific question or issue do you have with this product?"
                    # Stay in PRODUCT_SUPPORT state for the actual question
                else:
                    # Check for explicit range switching requests first
                    if any(phrase in message.lower() for phrase in ['show 1-5', 'show 1 to 5', 'first 5', 'earlier purchases', 'previous 5']):
                        # User wants to see purchases 1-5
                        session.displayed_purchases = session.all_purchases[:5]
                        session.recent_purchases = session.displayed_purchases
                        session.has_more_purchases = len(session.all_purchases) > 5
                        
                        response = "Here are your purchases 1-5:\n\n"
                        for i, purchase in enumerate(session.displayed_purchases, 1):
                            response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                        response += "\nWhich specific item do you need help with? You can tell me the number (1-5) or the product name."
                    
                    elif any(phrase in message.lower() for phrase in ['show 6-10', 'show 6 to 10', 'next 5', 'later purchases', 'more recent']):
                        # User wants to see purchases 6-10
                        if len(session.all_purchases) > 5:
                            session.displayed_purchases = session.all_purchases[5:10]
                            session.recent_purchases = session.displayed_purchases
                            session.has_more_purchases = False
                            
                            response = "Here are your purchases 6-10:\n\n"
                            for i, purchase in enumerate(session.displayed_purchases, 6):
                                response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                            response += "\nWhich specific item do you need help with? You can tell me the number (6-10) or the product name."
                        else:
                            response = "You only have 5 recent purchases. All of them are already shown above."
                    
                    # Check for requests beyond available range (11+)
                    elif any(phrase in message.lower() for phrase in ['product 11', 'product 12', 'item 11', 'item 12', 'number 11', 'number 12']) or \
                         any(f'product {i}' in message.lower() or f'item {i}' in message.lower() or f'number {i}' in message.lower() 
                             for i in range(11, 21)):  # Check for 11-20
                        response = "I can only access your 10 most recent purchases. If you're looking for an older purchase, please contact our support team directly, and they can help you with your complete purchase history."
                    
                    else:
                        # Continue with existing auto-pagination logic
                        # Check if user is indicating they can't find what they want (auto-show more)
                        not_found_phrases = [
                            'not in this list', 'not in the list', 'not listed', 'not here', 
                            'don\'t see it', 'can\'t see it', 'not there', 'missing',
                            'not what i\'m looking for', 'not what i need', 'looking for something else',
                            'different product', 'other product', 'another product',
                            'not among these', 'not in these', 'none of these'
                        ]
                        
                        user_cant_find = any(phrase in message.lower() for phrase in not_found_phrases)
                        
                        # Check if user explicitly wants to see more purchases
                        explicit_more_request = any(phrase in message.lower() for phrase in ['more purchases', 'more products', 'see more', 'other purchases', 'next 5', '6-10', 'more items'])
                        
                        # Auto-show more purchases if user indicates they can't find what they want OR explicitly asks
                        if (user_cant_find or explicit_more_request) and session.has_more_purchases and len(session.all_purchases) > 5:
                            # Show purchases 6-10
                            session.displayed_purchases = session.all_purchases[5:10]
                            session.recent_purchases = session.displayed_purchases  # For backward compatibility
                            session.has_more_purchases = False  # No more after this
                            
                            if user_cant_find:
                                response = "No problem! Let me show you your next recent purchases (6-10):\n\n"
                            else:
                                response = "Here are your next recent purchases (6-10):\n\n"
                                
                            for i, purchase in enumerate(session.displayed_purchases, 6):
                                response += f"{i}. {purchase['product_name']} - {purchase['sale_date']}\n"
                            response += "\nWhich specific item do you need help with? You can tell me the number (6-10) or the product name."
                        
                        elif (user_cant_find or explicit_more_request) and not session.has_more_purchases:
                            response = "I can't retrieve more than 10 of your most recent purchases at the moment. If you're looking for an older purchase, please contact our support team directly."
                        
                        # Check if user wants to switch products or get general help
                        elif any(word in message.lower() for word in ['different', 'other', 'switch', 'change', 'another']):
                            # Show currently displayed purchases
                            start_num = 1 if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5] else 6
                            response = "Sure! Which product from your recent purchases would you like help with?\n\n" + \
                                     "\n".join([f"{i+start_num}. {purchase['product_name']} - {purchase['sale_date']}" 
                                              for i, purchase in enumerate(session.displayed_purchases)])
                            
                            # If user is seeing 1-5 and there are more, offer to show more
                            if session.has_more_purchases and start_num == 1:
                                response += "\n\nOr say 'show more purchases' to see purchases 6-10."
                        
                        else:
                            # User didn't find what they want in current list - provide helpful guidance
                            purchase_range = "1-5" if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5] else "6-10"
                            
                            if session.has_more_purchases and purchase_range == "1-5":
                                # Still showing 1-5 and have more - suggest ways to find what they want
                                response = f"I couldn't identify which product you're referring to from purchases 1-5. You can:\n\n" + \
                                         "• Tell me the number (1-5) or product name from the list above\n" + \
                                         "• Say something like 'it's not in this list' to see purchases 6-10\n" + \
                                         "• Ask me for help with something else"
                            else:
                                current_range = f"({purchase_range})" if purchase_range != "1-5" else "(1-5)"
                                response = f"I couldn't identify which product you're referring to. Please tell me the number {current_range} from your purchase list or the product name, or ask me for help with something else."
        
        # Add response to session
        session.messages.append(ChatMessage("assistant", response))
        
        return response, session
    
    def start_new_session(self) -> CustomerSession:
        """Start a new customer service session with welcome message"""
        session = CustomerSession()
        # Add welcome message immediately when session starts
        welcome_msg = self._generate_welcome_message()
        session.messages.append(ChatMessage("assistant", welcome_msg))
        return session


# For Streamlit compatibility
EnhancedChatAgent = CustomerServiceBot
ChatSession = CustomerSession
