from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.tools import Tool, StructuredTool
from langchain.agents import initialize_agent, AgentType 
from langchain.schema import AgentAction, AgentFinish

# Make groq import optional since we're primarily using Ollama
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None
    
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.api.tavily import tavily_service
from app.models.pydantic_models import ChatMessage, ChatSession
from dotenv import load_dotenv

load_dotenv()


class ChatbotAgent:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Model configuration - simplified to just 2 models
        self.sql_model = os.getenv("OLLAMA_SQL_MODEL", "sqlcoder:7b")  # For SQL generation only
        self.chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")  # For everything else (context + chat)
        
        self.use_ollama_primary = os.getenv("USE_OLLAMA_PRIMARY", "true").lower() == "true"

        # Database schema for SQL generation
        self.database_schema = """
        Database Schema (PostgreSQL):
        
        Table: customer
        - customer_id SERIAL PRIMARY KEY
        - party_type VARCHAR(20)
        - first_name VARCHAR(50)
        - last_name VARCHAR(50) 
        - middle_name VARCHAR(50)
        - email VARCHAR(100) UNIQUE
        - phone VARCHAR(20)
        - addr1 VARCHAR(50)
        - addr2 VARCHAR(50)
        - city VARCHAR(50)
        - state VARCHAR(50)
        - zipcode VARCHAR(20)
        - country VARCHAR(20)
        - comments VARCHAR(200)
        - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        
        Table: product
        - product_id SERIAL PRIMARY KEY
        - product_name VARCHAR(100)
        - category VARCHAR(50)
        - type VARCHAR(50)
        - version VARCHAR(20)
        - price DECIMAL(10, 2)
        - stock_quantity INT
        - start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        - end_dt TIMESTAMP
        - comments VARCHAR(200)
        - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        
        Table: sales
        - sale_id SERIAL PRIMARY KEY
        - customer_id INT REFERENCES customer(customer_id)
        - product_id INT REFERENCES product(product_id)
        - quantity INT
        - sale_date DATE
        - comments VARCHAR(200)
        - total_amount DECIMAL(10, 2)
        
        Table: activity
        - activity_id SERIAL PRIMARY KEY
        - customer_id INT REFERENCES customer(customer_id)
        - product_id INT REFERENCES product(product_id)
        - activity_type VARCHAR(50)
        - description TEXT
        - comments VARCHAR(200)
        - activity_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """

        # Initialize database connection with error handling
        self.db = None
        self.sql_toolkit = None
        if (
            self.database_url
            and self.database_url
            != "postgresql://username:password@your-azure-postgres-server.postgres.database.azure.com:5432/your_database"
        ):
            try:
                self.db = SQLDatabase.from_uri(self.database_url)
                self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self._get_llm())
                print("✅ Database connection successful")
            except Exception as e:
                print(f"⚠️  Database connection failed: {e}")
                print("⚠️  Continuing without database connectivity")

        # Initialize memory
        self.memory = ConversationBufferWindowMemory(k=10)

        # Initialize Groq client (optional)
        if GROQ_AVAILABLE and self.groq_api_key and self.groq_api_key != "your_groq_api_key":
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None

        # Initialize tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()

    def _get_llm(self):
        """Get the appropriate LLM based on configuration"""
        # Try Ollama first if USE_OLLAMA_PRIMARY is true
        if self.use_ollama_primary:
            try:
                print(f"🤖 Attempting to connect to Ollama with model: {self.ollama_model}")
                ollama_llm = ChatOllama(
                    model=self.ollama_model, 
                    base_url=self.ollama_base_url, 
                    temperature=0.7,
                    num_predict=2048,  # Max tokens
                    top_p=0.9,
                    repeat_penalty=1.1
                )
                # Test the connection
                test_response = ollama_llm.invoke("Hello, are you working?")
                print("✅ Ollama connection successful!")
                return ollama_llm
            except Exception as e:
                print(f"⚠️  Ollama initialization failed: {e}")
                print("🔄 Falling back to Groq...")

        # Try Groq as fallback or primary if Ollama is not preferred
        if self.groq_client:
            try:
                print("🤖 Using Groq LLM...")
                return self._create_groq_wrapper()
            except Exception as e:
                print(f"⚠️  Groq initialization failed: {e}")

        # If Groq failed but Ollama wasn't primary, try Ollama as final fallback
        if not self.use_ollama_primary:
            try:
                print(f"🤖 Attempting Ollama fallback with model: {self.ollama_model}")
                ollama_llm = ChatOllama(
                    model=self.ollama_model, 
                    base_url=self.ollama_base_url, 
                    temperature=0.7,
                    num_predict=2048,
                    top_p=0.9,
                    repeat_penalty=1.1
                )
                # Test the connection
                test_response = ollama_llm.invoke("Hello, are you working?")
                print("✅ Ollama fallback connection successful!")
                return ollama_llm
            except Exception as e:
                print(f"⚠️  Ollama fallback failed: {e}")

        # If both fail, create a simple mock LLM for testing
        print("⚠️  All LLM services failed, using mock LLM")
        return self._create_mock_llm()

    def _create_mock_llm(self):
        """Create a simple mock LLM for testing when no real LLM is available"""

        class MockLLM:
            def __call__(self, prompt, **kwargs):
                return "I'm a mock LLM. The real LLM services (Ollama/Groq) are not available. Please configure them for full functionality."

            def predict(self, prompt, **kwargs):
                return self(prompt, **kwargs)

        return MockLLM()

    def _create_groq_wrapper(self):
        """Create a wrapper for Groq API to work with LangChain"""

        class GroqLLM:
            def __init__(self, client):
                self.client = client

            def __call__(self, prompt, **kwargs):
                response = self.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",  # Updated to newer model
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2048,
                )
                return response.choices[0].message.content

            def invoke(self, prompt, **kwargs):
                """Support for newer LangChain invoke method"""
                return self(prompt, **kwargs)
            
            def predict(self, prompt, **kwargs):
                """Support for LangChain predict method"""
                return self(prompt, **kwargs)

        return GroqLLM(self.groq_client)

    def _get_specialized_llm(self, model_name):
        """Get a specialized LLM for specific tasks"""
        try:
            if self.use_ollama_primary:
                ollama_llm = ChatOllama(
                    model=model_name,
                    base_url=self.ollama_base_url,
                    temperature=0.1,  # Lower temperature for more precise responses
                    num_predict=1024,
                    top_p=0.9,
                )
                return ollama_llm
            else:
                return self._get_llm()
        except Exception as e:
            print(f"⚠️  Failed to get specialized LLM for {model_name}: {e}")
            return self._get_llm()

    def _contextualize_query(self, user_query, chat_history):
        """Use chat model to contextualize user query given chat history"""
        try:
            chat_llm = self._get_specialized_llm(self.chat_model)
            
            # Format chat history
            history_text = ""
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = "Human" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
            
            contextualization_prompt = f"""
Given the following chat conversation history and the most recent user query, convert the user query into a standalone question that can be understood without the chat context.

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

            if hasattr(chat_llm, 'invoke'):
                response = chat_llm.invoke(contextualization_prompt)
                contextualized = response.content if hasattr(response, 'content') else str(response)
            else:
                contextualized = chat_llm(contextualization_prompt)
            
            return contextualized.strip()
            
        except Exception as e:
            print(f"⚠️  Query contextualization failed: {e}")
            return user_query  # Return original query if contextualization fails

    def _generate_sql_query(self, contextualized_query):
        """Use SQLCoder model to generate PostgreSQL queries"""
        try:
            sql_llm = self._get_specialized_llm(self.sql_model)
            
            sql_prompt = f"""
{self.database_schema}

Instructions:
- Generate a PostgreSQL query to answer the following question
- Use proper PostgreSQL syntax
- Include appropriate JOINs when querying multiple tables
- Use table aliases for readability
- Return only the SQL query, no explanations
- If the question cannot be answered with the available schema, return "NO_SQL_POSSIBLE"

Question: {contextualized_query}

SQL Query:"""

            if hasattr(sql_llm, 'invoke'):
                response = sql_llm.invoke(sql_prompt)
                sql_query = response.content if hasattr(response, 'content') else str(response)
            else:
                sql_query = sql_llm(sql_prompt)
            
            # Clean up the SQL query
            sql_query = sql_query.strip()
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            print(f"⚠️  SQL generation failed: {e}")
            return None

    def _create_tools(self) -> List[Tool]:
        """Create function call tools for the agent"""
        tools = []

        # Smart SQL query execution tool
        def execute_smart_sql_query(user_query: str, chat_context: str = "") -> str:
            """Execute intelligent SQL queries using SQLCoder model with query contextualization"""
            try:
                if not self.db:
                    return "Database not available. Please configure DATABASE_URL in environment variables."
                
                # Parse chat context if provided
                chat_history = []
                if chat_context:
                    try:
                        chat_history = json.loads(chat_context)
                    except:
                        chat_history = []
                
                # Step 1: Contextualize the query using Phi model
                print(f"🔄 Contextualizing query: {user_query}")
                contextualized_query = self._contextualize_query(user_query, chat_history)
                print(f"🎯 Contextualized to: {contextualized_query}")
                
                # Step 2: Generate SQL using SQLCoder
                print(f"🔄 Generating SQL for: {contextualized_query}")
                sql_query = self._generate_sql_query(contextualized_query)
                
                if not sql_query or sql_query == "NO_SQL_POSSIBLE":
                    return f"Cannot generate SQL query for: {contextualized_query}. This might require external search or general knowledge."
                
                print(f"📝 Generated SQL: {sql_query}")
                
                # Step 3: Execute the SQL query
                try:
                    result = self.db.run(sql_query)
                    return f"Query: {contextualized_query}\nSQL: {sql_query}\nResults: {result}"
                except Exception as sql_error:
                    return f"SQL execution error for query '{sql_query}': {str(sql_error)}"
                
            except Exception as e:
                return f"Error in smart SQL execution: {str(e)}"

        # Customer data tool (enhanced)
        def get_customer_data(query: str) -> str:
            """Get customer information using intelligent SQL generation"""
            return execute_smart_sql_query(f"Find customers related to: {query}")

        # Product data tool (enhanced)
        def get_product_data(query: str) -> str:
            """Get product information using intelligent SQL generation"""
            return execute_smart_sql_query(f"Find products related to: {query}")

        # Sales data tool (enhanced)
        def get_sales_data(query: str) -> str:
            """Get sales information using intelligent SQL generation"""
            return execute_smart_sql_query(f"Find sales data related to: {query}")

        # Activity data tool (enhanced)
        def get_activity_data(query: str) -> str:
            """Get activity information using intelligent SQL generation"""
            return execute_smart_sql_query(f"Find activity data related to: {query}")

        # Advanced analytics tool
        def get_advanced_analytics(query: str) -> str:
            """Get advanced analytics using intelligent SQL generation"""
            return execute_smart_sql_query(f"Generate analytics for: {query}")

        # External search tool
        def search_external_info(query: str) -> str:
            """Search for external information using Tavily API. Use for general knowledge, best practices, industry information."""
            try:
                search_result = tavily_service.get_search_context(query, max_results=3)
                return f"External search results: {search_result}"
            except Exception as e:
                return f"External search error: {str(e)}"

        # Create tools
        tools = [
            Tool(
                name="execute_smart_sql_query",
                description="Execute intelligent SQL queries with automatic contextualization and SQL generation. Use for any database-related questions.",
                func=execute_smart_sql_query,
            ),
            Tool(
                name="get_customer_data",
                description="Get customer information using intelligent SQL generation. Use for queries about customers, customer details, customer search.",
                func=get_customer_data,
            ),
            Tool(
                name="get_product_data",
                description="Get product information using intelligent SQL generation. Use for queries about products, inventory, pricing, product features.",
                func=get_product_data,
            ),
            Tool(
                name="get_sales_data",
                description="Get sales information using intelligent SQL generation. Use for queries about sales, revenue, transactions, sales data.",
                func=get_sales_data,
            ),
            Tool(
                name="get_activity_data",
                description="Get activity/engagement information using intelligent SQL generation. Use for queries about customer activities, support interactions, engagement tracking.",
                func=get_activity_data,
            ),
            Tool(
                name="get_advanced_analytics",
                description="Get advanced analytics and insights using intelligent SQL generation. Use for complex analysis, reporting, and data insights.",
                func=get_advanced_analytics,
            ),
            Tool(
                name="search_external_info",
                description="Search for external information using Tavily API. Use for general knowledge, best practices, industry information not in our database.",
                func=search_external_info,
            ),
        ]

        return tools

    def _create_agent(self):
        """Create the function-calling agent with enhanced multi-step capabilities"""
        try:
            llm = self._get_llm()

            # Create a more sophisticated agent that can handle multi-step reasoning
            agent = initialize_agent(
                tools=self.tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory,
                handle_parsing_errors=True,
                max_iterations=10,  # Allow multiple iterations for complex queries
                early_stopping_method="generate",  # Continue until proper answer is generated
            )

            return agent
        except Exception as e:
            print(f"Error creating agent: {e}")
            return None

    def generate_response(
        self, message: str, customer_email: str = None, use_external_search: bool = True, chat_history: List[Dict] = None
    ) -> str:
        """Generate a response using multi-step function calls with enhanced SQL capabilities"""
        try:
            if self.agent is None:
                return "I apologize, but the chatbot agent is not properly initialized. Please check the configuration."

            # Prepare chat context for the smart SQL tool
            chat_context = ""
            if chat_history:
                chat_context = json.dumps(chat_history[-10:])  # Last 10 messages

            # Enhanced prompt that encourages use of the smart SQL system
            enhanced_message = f"""
            You are Yodha, a professional customer service representative with access to advanced database query capabilities.
            
            CRITICAL BEHAVIORAL INSTRUCTIONS:
            - You are ONLY Yodha speaking directly to a customer in live conversation
            - NEVER write emails, letters, or formal documents - you are talking to someone right now
            - NEVER start with "Dear [Customer]" or end with "Best Regards" or any signature
            - NEVER use phrases like "Here is a good answer", "This can be a response", or meta-commentary
            - **MANDATORY FORMATTING**: ALWAYS use **bold formatting** for:
              * Your main answer or direct response to the customer's question
              * Key product names, prices, and specifications
              * Important status information (available, in stock, warranty details)
              * Action items and recommendations
              * Any critical information the customer needs to know
            - Speak naturally and directly as Yodha - you are having a conversation, not writing a document
            - Provide only factual information from the database - DO NOT add details not found in results
            - If database returns no results, simply say "I don't have that information"
            
            IMPORTANT: You now have access to a smart SQL system that can:
            1. Automatically contextualize user queries based on chat history
            2. Generate sophisticated PostgreSQL queries using SQLCoder
            3. Handle complex database relationships and joins
            
            Available functions:
            - execute_smart_sql_query: Primary tool for ANY database-related questions (uses SQLCoder + Phi models)
            - get_customer_data: Customer information queries
            - get_product_data: Product information queries  
            - get_sales_data: Sales transaction queries
            - get_activity_data: Customer activity queries
            - get_advanced_analytics: Complex analytics and insights
            - search_external_info: External information and best practices
            
            Database Schema Available:
            - customer: Personal info, contact details, address
            - product: Product catalog, pricing, inventory
            - sales: Transaction history, amounts, dates
            - activity: Customer interactions, engagement tracking
            
            APPROACH:
            1. For any data-related question, prefer execute_smart_sql_query as it's most intelligent
            2. The system will automatically understand context from previous messages
            3. Complex queries will be handled intelligently by SQLCoder
            4. Provide clear, helpful responses based on the data
            
            User question: {message}
            {f"Customer context: {customer_email}" if customer_email else ""}
            {f"Chat context available: {len(chat_history)} previous messages" if chat_history else "No chat history"}
            
            Please help the user with their request using the most appropriate tools.
            """

            # Use the agent to process the message with enhanced reasoning
            response = self.agent.run(enhanced_message)

            return response

        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    def create_chat_session(self, customer_email: str) -> ChatSession:
        """Create a new chat session"""
        import uuid

        session_id = str(uuid.uuid4())
        now = datetime.now()

        return ChatSession(
            session_id=session_id,
            customer_email=customer_email,
            messages=[],
            created_at=now,
            updated_at=now,
        )

    def add_message_to_session(
        self, session: ChatSession, role: str, content: str
    ) -> ChatSession:
        """Add a message to the chat session"""
        message = ChatMessage(role=role, content=content, timestamp=datetime.now())

        session.messages.append(message)
        session.updated_at = datetime.now()

        return session

    def chat(
        self, message: str, session: ChatSession, use_external_search: bool = True
    ) -> tuple[str, ChatSession]:
        """Process a chat message and return response with updated session"""
        # Add user message to session
        session = self.add_message_to_session(session, "user", message)

        # Convert session messages to chat history format
        chat_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in session.messages
        ]

        # Generate response using function calls with chat history
        response = self.generate_response(
            message, session.customer_email, use_external_search, chat_history
        )

        # Add assistant response to session
        session = self.add_message_to_session(session, "assistant", response)

        return response, session

# Initialize the chatbot agent
chatbot_agent = ChatbotAgent()

# Alias for backward compatibility with enhanced agent
EnhancedChatAgent = ChatbotAgent
