"""Test the enhanced agent with SQLCoder and Phi model integration"""

import asyncio
import requests
import json
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from chatbot.agent import EnhancedChatAgent
from models.pydantic_models import ChatSession


def test_ollama_connection():
    """Test if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Ollama server is running - Version: {version_info.get('version', 'Unknown')}")
            return True
        else:
            print(f"❌ Ollama server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to Ollama server: {e}")
        return False


def check_model_availability(model_name):
    """Check if a specific model is available in Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Check for exact match or partial match
            for available_model in available_models:
                if model_name in available_model or available_model.startswith(model_name):
                    print(f"✅ Model '{model_name}' found as '{available_model}'")
                    return True
            
            print(f"❌ Model '{model_name}' not found")
            print(f"Available models: {available_models}")
            return False
        else:
            print(f"❌ Failed to get model list: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking models: {e}")
        return False


def pull_model(model_name):
    """Attempt to pull a model if not available"""
    print(f"🔄 Attempting to pull model: {model_name}")
    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'status' in data:
                            print(f"  {data['status']}")
                        if data.get('status') == 'success':
                            print(f"✅ Successfully pulled {model_name}")
                            return True
                    except json.JSONDecodeError:
                        continue
        else:
            print(f"❌ Failed to pull model: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error pulling model: {e}")
        return False


def test_model_response(model_name, prompt):
    """Test a model with a simple prompt"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'No response')
        else:
            return f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


def test_agent_functionality():
    """Test the enhanced agent with SQL capabilities"""
    print("\n🧪 Testing Enhanced Agent Functionality")
    
    try:
        # Initialize the enhanced agent
        agent = EnhancedChatAgent()
        print("✅ Agent initialized successfully")
        
        # Create a test session
        session = ChatSession(customer_email="test@example.com")
        
        # Test queries that should trigger SQL functionality
        test_queries = [
            "How many customers do we have?",
            "What are our top 5 products by sales?",
            "Show me recent customer activities",
            "What's the total revenue for this month?",
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing query: '{query}'")
            try:
                response, updated_session = agent.chat(query, session)
                print(f"🤖 Response: {response[:200]}..." if len(response) > 200 else f"🤖 Response: {response}")
                session = updated_session
            except Exception as e:
                print(f"❌ Error with query '{query}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False


def main():
    print("🚀 Testing Enhanced Agent with SQLCoder and Phi Integration")
    print("=" * 60)
    
    # Test Ollama connection
    if not test_ollama_connection():
        print("\n❌ Cannot proceed without Ollama server")
        return
    
    # Check required models
    required_models = ["sqlcoder:7b", "phi3:chat", "llama3.2:1b"]
    models_available = {}
    
    print(f"\n🔍 Checking required models...")
    for model in required_models:
        models_available[model] = check_model_availability(model)
    
    # Try to pull missing models
    missing_models = [model for model, available in models_available.items() if not available]
    
    if missing_models:
        print(f"\n📥 Missing models detected: {missing_models}")
        print("Attempting to pull missing models...")
        
        for model in missing_models:
            if pull_model(model):
                models_available[model] = True
            else:
                print(f"❌ Failed to pull {model}")
    
    # Test individual models with simple prompts
    print(f"\n🧪 Testing individual model responses...")
    
    # Test SQLCoder if available
    if models_available.get("sqlcoder:7b"):
        print(f"\n🔍 Testing SQLCoder:7b...")
        sql_prompt = "Generate SQL to count all customers from a table named 'customers'"
        sql_response = test_model_response("sqlcoder:7b", sql_prompt)
        print(f"SQL Response: {sql_response[:200]}...")
    
    # Test Phi3 if available
    if models_available.get("phi3:chat"):
        print(f"\n🔍 Testing phi3:chat...")
        phi_prompt = "Explain what this query means: 'show me top customers'"
        phi_response = test_model_response("phi3:chat", phi_prompt)
        print(f"Phi Response: {phi_response[:200]}...")
    
    # Test the enhanced agent
    if all(models_available.values()):
        test_agent_functionality()
    else:
        print(f"\n⚠️  Not all required models are available. Agent testing may be limited.")
        missing = [model for model, available in models_available.items() if not available]
        print(f"Missing: {missing}")
    
    print(f"\n✨ Testing complete!")


if __name__ == "__main__":
    main()
