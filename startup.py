#!/usr/bin/env python3
"""
Startup script for the Agentic Chatbot application
"""
import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/version", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama():
        print("Starting Ollama...")
        try:
            # Try to start Ollama (this might need to be adjusted based on your Ollama installation)
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(5)  # Give Ollama time to start

            if check_ollama():
                print("✅ Ollama started successfully")

                # Try to pull Llama2 model
                print("Checking for Llama2 model...")
                try:
                    subprocess.run(
                        ["ollama", "pull", "llama2"], check=True, timeout=300
                    )
                    print("✅ Llama2 model ready")
                except subprocess.TimeoutExpired:
                    print("⚠️  Llama2 model download timed out (continuing anyway)")
                except subprocess.CalledProcessError:
                    print("⚠️  Could not download Llama2 model (continuing anyway)")
            else:
                print("⚠️  Ollama failed to start")
        except FileNotFoundError:
            print("⚠️  Ollama not found. Please install Ollama from https://ollama.ai/")
    else:
        print("✅ Ollama is already running")


def start_api_server():
    """Start the FastAPI server"""
    print("Starting FastAPI server...")
    try:
        python_path = sys.executable
        cmd = [
            python_path,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ]

        process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give the server time to start
        time.sleep(5)

        # Check if server is running
        import requests

        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ FastAPI server started successfully")
                return process
            else:
                print(f"❌ FastAPI server health check failed: {response.status_code}")
        except requests.RequestException as e:
            print(f"❌ FastAPI server not responding: {e}")

        return process

    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {e}")
        return None


def start_streamlit():
    """Start the Streamlit app"""
    print("Starting Streamlit app...")
    try:
        python_path = sys.executable
        cmd = [
            python_path,
            "-m",
            "streamlit",
            "run",
            "streamlit_app.py",
            "--server.port",
            "8501",
        ]

        process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print("✅ Streamlit app starting...")
        print("🌐 Streamlit will be available at: http://localhost:8501")
        return process

    except Exception as e:
        print(f"❌ Failed to start Streamlit app: {e}")
        return None


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "langchain",
        "sqlalchemy",
        "psycopg2",
        "azure-storage-blob",
        "tavily-python",
        "pydantic",
        "requests",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed")
        return True


def check_environment():
    """Check environment configuration"""
    print("Checking environment configuration...")

    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found. Creating template...")
        # The .env template was already created in previous steps

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv(env_file)

    required_vars = ["DATABASE_URL"]
    optional_vars = [
        "TAVILY_API_KEY",
        "GROQ_API_KEY",
        "EMAIL_USERNAME",
        "TWILIO_ACCOUNT_SID",
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)

    if missing_required:
        print(
            f"❌ Missing required environment variables: {', '.join(missing_required)}"
        )
        print("Please configure them in the .env file")
        return False

    if missing_optional:
        print(
            f"⚠️  Missing optional environment variables: {', '.join(missing_optional)}"
        )
        print("Some features may not work without these")

    print("✅ Environment configuration checked")
    return True


def main():
    """Main startup function"""
    print("=" * 60)
    print("🤖 AGENTIC CHATBOT STARTUP")
    print("=" * 60)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check environment
    if not check_environment():
        print("⚠️  Continuing with incomplete configuration...")

    # Start Ollama
    start_ollama()

    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server. Exiting.")
        sys.exit(1)

    # Start Streamlit
    streamlit_process = start_streamlit()

    print("\n" + "=" * 60)
    print("🚀 STARTUP COMPLETE")
    print("=" * 60)
    print("📊 FastAPI Server: http://localhost:8000")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🖥️  Streamlit App: http://localhost:8501")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all services")

    try:
        # Keep the script running
        while True:
            time.sleep(1)

            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break

            if streamlit_process and streamlit_process.poll() is not None:
                print("❌ Streamlit app stopped unexpectedly")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")

        if api_process:
            api_process.terminate()
            print("✅ API server stopped")

        if streamlit_process:
            streamlit_process.terminate()
            print("✅ Streamlit app stopped")

        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
