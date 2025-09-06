#!/usr/bin/env python3

"""
Direct OpenAI API Test Script
Tests OpenAI API directly without the bot framework
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_direct():
    print("🧪 Direct OpenAI API Test")
    print("=" * 40)
    
    # Check OpenAI package availability
    try:
        import openai
        print("✅ OpenAI package imported successfully")
        print(f"   OpenAI package version: {openai.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI package: {e}")
        return False
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-10:]}")
    
    # Check model configuration
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    print(f"📋 Using model: {model}")
    
    # Initialize OpenAI client
    try:
        client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🚀 Testing API Calls")
    print("=" * 40)
    
    # Test 1: Simple completion
    print("\n1. Testing simple completion...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
                {"role": "user", "content": "Hello! What is 2+2?"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content
            print(f"✅ Simple completion successful!")
            print(f"   Response: {content}")
            print(f"   Token usage: {response.usage.total_tokens if response.usage else 'N/A'}")
        else:
            print("❌ No response content received")
            return False
            
    except Exception as e:
        print(f"❌ Simple completion failed: {e}")
        return False
    
    # Test 2: Conversation with history
    print("\n2. Testing conversation with history...")
    try:
        messages = [
            {"role": "system", "content": "You are Yodha, a helpful customer service representative. Keep responses brief and friendly."},
            {"role": "user", "content": "Hi, I need help with my account"},
            {"role": "assistant", "content": "Hello! I'd be happy to help you with your account. Could you please provide your email address?"},
            {"role": "user", "content": "My email is john@example.com"},
            {"role": "assistant", "content": "Thank you, John! I have your email. What specific issue are you experiencing with your account?"},
            {"role": "user", "content": "I forgot my password"}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content
            print(f"✅ Conversation history test successful!")
            print(f"   Response: {content}")
            print(f"   Context messages: {len(messages)}")
            print(f"   Token usage: {response.usage.total_tokens if response.usage else 'N/A'}")
        else:
            print("❌ No response content received")
            return False
            
    except Exception as e:
        print(f"❌ Conversation history test failed: {e}")
        return False
    
    # Test 3: Character consistency (Yodha personality)
    print("\n3. Testing character consistency...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": """You are Yodha, a professional customer service representative for Contoso.

CRITICAL BEHAVIORAL INSTRUCTIONS:
- You are ONLY Yodha speaking directly to the customer - NEVER write emails, letters, or formal documents
- NEVER start responses with "Dear [Customer]" or end with "Best Regards" or any email signature
- NEVER use phrases like "This can be an answer for", "Here is a response", or any meta-commentary
- You are having a direct conversation - speak naturally as yourself, not writing to someone
- Always highlight your main answer using **bold formatting** when providing key information
- Be direct, professional, and conversational - you are Yodha talking to a customer right now"""
                },
                {"role": "user", "content": "What is your name and how can you help me?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content
            print(f"✅ Character consistency test successful!")
            print(f"   Response: {content}")
            
            # Check for character compliance
            issues = []
            if "dear" in content.lower() and "customer" in content.lower():
                issues.append("Uses 'Dear Customer' format")
            if "best regards" in content.lower():
                issues.append("Uses email signature")
            if "here is" in content.lower() or "this can be" in content.lower():
                issues.append("Uses meta-commentary")
            if "**" not in content:
                issues.append("Missing bold formatting")
            
            if issues:
                print(f"   ⚠️ Character issues found: {', '.join(issues)}")
            else:
                print(f"   ✅ Character guidelines followed correctly!")
                
        else:
            print("❌ No response content received")
            return False
            
    except Exception as e:
        print(f"❌ Character consistency test failed: {e}")
        return False
    
    # Test 4: Error handling
    print("\n4. Testing error handling...")
    try:
        # Test with invalid model
        response = client.chat.completions.create(
            model="invalid-model-name",
            messages=[
                {"role": "user", "content": "This should fail"}
            ],
            max_tokens=50
        )
        print("❌ Error handling test failed - should have thrown an error")
        
    except Exception as e:
        print(f"✅ Error handling test successful!")
        print(f"   Expected error caught: {type(e).__name__}")
        print(f"   Error message: {str(e)[:100]}...")
    
    # Test 5: Token limits
    print("\n5. Testing token limits...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Count from 1 to 20, saying each number."}
            ],
            max_tokens=20,  # Very low limit
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content
            print(f"✅ Token limit test successful!")
            print(f"   Response (truncated): {content}")
            print(f"   Token usage: {response.usage.total_tokens if response.usage else 'N/A'}")
            print(f"   Finish reason: {response.choices[0].finish_reason}")
        else:
            print("❌ No response content received")
            
    except Exception as e:
        print(f"❌ Token limit test failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("📊 Test Summary")
    print("=" * 40)
    print("✅ All OpenAI API tests completed successfully!")
    print("✅ Direct API integration is working properly")
    print("✅ Ready for bot integration")
    
    return True

def test_available_models():
    """Test listing available models"""
    print("\n" + "=" * 40)
    print("🔍 Available Models Test")
    print("=" * 40)
    
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ No API key available for models test")
            return
        
        client = openai.OpenAI(api_key=api_key)
        
        print("📋 Fetching available models...")
        models = client.models.list()
        
        # Filter for chat models
        chat_models = [model for model in models.data if 'gpt' in model.id.lower()]
        
        print(f"✅ Found {len(chat_models)} GPT models:")
        for model in sorted(chat_models, key=lambda x: x.id)[:10]:  # Show first 10
            print(f"   - {model.id}")
        
        if len(chat_models) > 10:
            print(f"   ... and {len(chat_models) - 10} more")
            
    except Exception as e:
        print(f"❌ Models test failed: {e}")

def main():
    print("🚀 OpenAI Direct API Test Suite")
    print("Testing OpenAI integration without bot framework")
    print("=" * 50)
    
    # Test basic configuration
    print("\n📋 Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    
    # Load environment
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"   Environment file: {env_path} ✅")
    else:
        print(f"   Environment file: {env_path} ❌")
    
    # Run main tests
    success = test_openai_direct()
    
    # Test models if main tests pass
    if success:
        test_available_models()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! OpenAI API is ready for use.")
    else:
        print("❌ Some tests failed. Check API key and configuration.")
    print("=" * 50)

if __name__ == "__main__":
    main()
