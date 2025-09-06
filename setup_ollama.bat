@echo off
echo ============================================
echo Ollama GPT/OSS Model Setup for Windows
echo ============================================

echo.
echo Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama is not installed!
    echo.
    echo 📥 Please install Ollama first:
    echo 1. Go to https://ollama.ai
    echo 2. Download the Windows installer
    echo 3. Run the installer
    echo 4. Restart this script
    echo.
    pause
    exit /b 1
)

echo ✅ Ollama is installed!

echo.
echo 🔍 Checking if Ollama server is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama server is not running!
    echo.
    echo 🚀 Starting Ollama server in background...
    start "Ollama Server" cmd /c "ollama serve"
    echo Waiting for server to start...
    timeout /t 5 /nobreak >nul
)

echo.
echo 📦 Checking installed models...
ollama list

echo.
echo 📥 Would you like to download the recommended model? (llama3.2:1b - 1.3GB)
set /p choice="Enter Y/N: "
if /i "%choice%"=="Y" (
    echo Downloading llama3.2:1b... This may take a few minutes...
    ollama pull llama3.2:1b
    if %errorlevel% equ 0 (
        echo ✅ Model downloaded successfully!
    ) else (
        echo ❌ Download failed. Check your internet connection.
        pause
        exit /b 1
    )
)

echo.
echo 🧪 Testing the setup...
python test_ollama_basic.py

echo.
echo 🎉 Setup complete! 
echo.
echo 📝 To use with your chatbot:
echo 1. Add to your .env file:
echo    USE_OLLAMA_PRIMARY=true
echo    OLLAMA_MODEL=llama3.2:1b
echo 2. Your chatbot will now use local GPT models!
echo.
pause
