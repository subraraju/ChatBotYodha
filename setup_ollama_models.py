#!/usr/bin/env python3
"""
Setup script for downloading and configuring GPT-style OSS models in Ollama
"""

import subprocess
import sys
import time
import requests

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} successful!")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False

def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Setup GPT-style OSS models in Ollama"""
    
    print("🚀 Ollama GPT/OSS Model Setup")
    print("=" * 40)
    
    # Check if Ollama is installed
    if not run_command("ollama --version", "Checking Ollama installation"):
        print("❌ Ollama not found. Please install Ollama first:")
        print("   Windows: Download from https://ollama.ai")
        print("   macOS: brew install ollama")
        print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
        return
    
    # Start Ollama server if not running
    if not check_ollama_running():
        print("🔄 Starting Ollama server...")
        subprocess.Popen("ollama serve", shell=True)
        time.sleep(3)  # Give it time to start
        
        if not check_ollama_running():
            print("❌ Failed to start Ollama server. Please start it manually with: ollama serve")
            return
    
    print("✅ Ollama server is running!")
    
    # List of recommended GPT-style models
    models = [
        {
            "name": "llama3.2:1b",
            "description": "Small, fast LLaMA 3.2 model (1.3GB)",
            "recommended": True
        },
        {
            "name": "llama3.2:3b", 
            "description": "Medium LLaMA 3.2 model (2.0GB)",
            "recommended": True
        },
        {
            "name": "llama3.1:8b",
            "description": "Large LLaMA 3.1 model (4.7GB)",
            "recommended": False
        },
        {
            "name": "mistral:7b",
            "description": "Mistral 7B model (4.1GB)",
            "recommended": False
        },
        {
            "name": "codellama:7b",
            "description": "Code-focused LLaMA model (3.8GB)",
            "recommended": False
        }
    ]
    
    print("\n📦 Available Models:")
    for i, model in enumerate(models, 1):
        status = "⭐ Recommended" if model["recommended"] else "Optional"
        print(f"  {i}. {model['name']} - {model['description']} ({status})")
    
    print("\n🔄 Installing recommended models...")
    
    for model in models:
        if model["recommended"]:
            success = run_command(
                f"ollama pull {model['name']}", 
                f"Downloading {model['name']}"
            )
            if success:
                # Test the model
                print(f"🧪 Testing {model['name']}...")
                test_success = run_command(
                    f'ollama run {model["name"]} "Hello, are you working?" --verbose',
                    f"Testing {model['name']}"
                )
                if not test_success:
                    print(f"⚠️  {model['name']} downloaded but test failed")
            else:
                print(f"⚠️  Failed to download {model['name']}")
    
    # Show final status
    print("\n📊 Final Status:")
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Installed models:")
            print(result.stdout)
        else:
            print("❌ Could not list models")
    except:
        print("❌ Could not check model status")
    
    print("\n🎉 Setup complete!")
    print("\n📝 Next steps:")
    print("1. Run the test script: python test_ollama_integration.py")
    print("2. Set environment variable: USE_OLLAMA_PRIMARY=true")
    print("3. Set your preferred model: OLLAMA_MODEL=llama3.2:1b")
    print("4. Start your chatbot application")

if __name__ == "__main__":
    main()
