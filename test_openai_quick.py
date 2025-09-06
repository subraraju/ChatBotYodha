#!/usr/bin/env python3

"""
Quick OpenAI API Test
Simple test to verify OpenAI API is working
"""
import os
from dotenv import load_dotenv

load_dotenv()

def quick_test():
    print("⚡ Quick OpenAI API Test")
    print("=" * 30)
    
    # Import and setup
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not api_key:
            print("❌ No OPENAI_API_KEY found")
            return
        
        print(f"🔑 API Key: {api_key[:10]}...")
        print(f"🤖 Model: {model}")
        
        # Initialize client
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test
        print("\n🧪 Testing API call...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are Yodha from Contoso. Be brief and friendly."},
                {"role": "user", "content": "Hi! Who are you?"}
            ],
            max_tokens=50
        )
        
        if response.choices:
            content = response.choices[0].message.content
            print(f"✅ Success! Response: {content}")
            print(f"📊 Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
        else:
            print("❌ No response received")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
