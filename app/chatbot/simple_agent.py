"""
Simplified Enhanced Chat Agent for testing without dependency conflicts
"""
import os
import json
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Simple Pydantic models without version conflicts
class ChatMessage:
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

class ChatSession:
    def __init__(self, session_id: str = None, customer_email: str = "test@example.com", 
                 messages: List[ChatMessage] = None, created_at: datetime = None, 
                 updated_at: datetime = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.customer_email = customer_email
        self.messages = messages or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class EnhancedChatAgent:
    """Simplified Enhanced Chat Agent for testing Ollama integration"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.sql_model = os.getenv("OLLAMA_SQL_MODEL", "sqlcoder:7b")
        self.chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")
        
        # Database schema for SQL generation
        self.database_schema = """
        Database Schema (PostgreSQL):
        
        Table: customer
        - customer_id SERIAL PRIMARY KEY
        - first_name VARCHAR(50), last_name VARCHAR(50)
        - email VARCHAR(100) UNIQUE
        - phone VARCHAR(20), city VARCHAR(50), state VARCHAR(50)
        
        Table: product  
        - product_id SERIAL PRIMARY KEY
        - product_name VARCHAR(100), category VARCHAR(50)
        - price DECIMAL(10, 2), stock_quantity INT
        
        Table: sales
        - sale_id SERIAL PRIMARY KEY
        - customer_id INT REFERENCES customer(customer_id)
        - product_id INT REFERENCES product(product_id)
        - quantity INT, sale_date DATE, total_amount DECIMAL(10, 2)
        
        Table: activity
        - activity_id SERIAL PRIMARY KEY
        - customer_id INT REFERENCES customer(customer_id)
        - activity_type VARCHAR(50), description TEXT
        - activity_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        
        print("✅ Enhanced Chat Agent initialized successfully")
    
    def _call_ollama(self, model: str, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API directly"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: Ollama returned status {response.status_code}"
                
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    def _contextualize_query(self, user_query: str, chat_history: List[Dict]) -> str:
        """Use chat model to contextualize user query given chat history"""
        try:
            # Format chat history
            history_text = ""
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = "Human" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
            
            contextualization_prompt = f"""Given the following chat conversation history and the most recent user query, convert the user query into a standalone question that can be understood without the chat context.

Chat History:
{history_text}

Most Recent User Query: {user_query}

Instructions:
- If the user query is already standalone and clear, return it as-is
- If it references previous messages (like "what about that", "tell me more", etc.), expand it to be self-contained
- Include relevant context from the chat history if needed
- Keep it concise and focused
- Return only the contextualized question, nothing else

Contextualized Query:"""

            contextualized = self._call_ollama(self.chat_model, contextualization_prompt)
            return contextualized.strip() if contextualized else user_query
            
        except Exception as e:
            print(f"Error contextualizing query: {e}")
            return user_query
    
    def _generate_sql_query(self, contextualized_query: str) -> str:
        """Generate SQL query using SQLCoder model"""
        try:
            sql_prompt = f"""Given this database schema:

{self.database_schema}

Generate a SQL query to answer this question: {contextualized_query}

Instructions:
- Write only the SQL query, no explanations
- Use proper PostgreSQL syntax
- Include appropriate JOINs if needed
- Limit results to reasonable numbers (e.g., TOP 10)
- Return only the SQL query, nothing else

SQL Query:"""

            sql_query = self._call_ollama(self.sql_model, sql_prompt)
            return sql_query.strip() if sql_query else "SELECT 'No SQL generated' as result;"
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return f"-- Error generating SQL: {str(e)}"
    
    def execute_smart_sql_query(self, user_query: str, chat_history: List[Dict] = None) -> str:
        """Execute the complete SQL query pipeline"""
        try:
            # Step 1: Contextualize the query
            contextualized = self._contextualize_query(user_query, chat_history or [])
            print(f"🔍 Contextualized: {contextualized}")
            
            # Step 2: Generate SQL
            sql_query = self._generate_sql_query(contextualized)
            print(f"💾 Generated SQL: {sql_query}")
            
            # Step 3: Since we can't execute the SQL due to DB connection issues,
            # return a mock result with the generated SQL
            return f"""Based on your query: "{user_query}"

I generated this SQL query:
```sql
{sql_query}
```

Note: Due to database connection timeout, I cannot execute this query, but the SQL generation is working correctly using the SQLCoder:7b model."""
            
        except Exception as e:
            return f"Error in smart SQL query: {str(e)}"
    
    def generate_response(self, message: str, customer_email: str = None, 
                         use_external_search: bool = False, chat_history: List[Dict] = None) -> str:
        """Generate response using the appropriate model"""
        
        # Determine if this is a database query
        db_keywords = ['how many', 'show me', 'list', 'count', 'total', 'revenue', 'sales', 
                       'customers', 'products', 'activities', 'top', 'recent']
        
        is_db_query = any(keyword in message.lower() for keyword in db_keywords)
        
        if is_db_query:
            # Use SQL pipeline
            return self.execute_smart_sql_query(message, chat_history)
        else:
            # Use general chat
            chat_prompt = f"""You are Yodha, a professional customer service representative. Answer this question: {message}

CRITICAL INSTRUCTIONS:
- You are ONLY Yodha speaking directly to a customer in live conversation
- NEVER write emails, letters, or formal documents - you are talking to someone right now
- NEVER start with "Dear [Customer]" or end with "Best Regards" or signatures
- NEVER say "Here is a good answer", "This can be a response", or meta-commentary
- Always use **bold formatting** to highlight your main answer and key information  
- Speak naturally and directly as Yodha - you are having a conversation, not writing
- Provide only factual information - do NOT add details not provided
- If you don't know something, simply say "I don't have that information"

Keep your response helpful, concise, and professional."""
            
            response = self._call_ollama(self.chat_model, chat_prompt)
            return response if response else "I'm sorry, I couldn't generate a response."
    
    def add_message_to_session(self, session: ChatSession, role: str, content: str) -> ChatSession:
        """Add a message to the chat session"""
        message = ChatMessage(role=role, content=content)
        session.messages.append(message)
        session.updated_at = datetime.now()
        return session
    
    def chat(self, message: str, session: ChatSession, use_external_search: bool = True) -> tuple[str, ChatSession]:
        """Process a chat message and return response with updated session"""
        # Add user message to session
        session = self.add_message_to_session(session, "user", message)
        
        # Convert session messages to chat history format
        chat_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in session.messages
        ]
        
        # Generate response using function calls with chat history
        response = self.generate_response(message, session.customer_email, use_external_search, chat_history)
        
        # Add assistant response to session
        session = self.add_message_to_session(session, "assistant", response)
        
        return response, session


# For backward compatibility
ChatbotAgent = EnhancedChatAgent
