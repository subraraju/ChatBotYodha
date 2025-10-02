# Secrets & Credentials Setup Guide for ChatBotYodha

This guide explains how to set up all required secrets and credentials for running the chatbot, including Google, Teams, Azure, and email integrations.

---

## 1. `.env` File
- **Copy** `.env.example` to `.env` and fill in your real values.
- **Never commit your real `.env` file to git!**

### Main fields:
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DATABASE_URL`: Your Azure PostgreSQL connection info.
- `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, `GROQ_API_KEY`: Get from your LLM provider dashboards.
- `SMTP_USERNAME`, `SMTP_PASSWORD`: Gmail address and [App Password](https://support.google.com/accounts/answer/185833?hl=en).
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`: From Azure Portal (App registrations > Your App > Overview & Certificates/Secrets).
- `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_TOKEN_FILE`: See below for Google setup.

---

## 2. Google Calendar API Credentials

### Steps to create `credentials.json`:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Go to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth client ID**
5. Choose **Desktop app**
6. Download the `credentials.json` file and place it in the project root
7. On first run, the app will prompt you to authenticate and create `token.json`

- **Never commit your real `credentials.json` or `token.json` to git!**
- Use `credentials.example.json` as a template for sharing config structure.

---

## 3. Microsoft Teams / Azure AD

- Go to [Azure Portal](https://portal.azure.com/)
- Register a new app in **Azure Active Directory > App registrations**
- Add **API permissions** for Microsoft Graph (OnlineMeetings.ReadWrite.All, etc.)
- Generate a **Client Secret** under **Certificates & secrets**
- Copy the `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` to your `.env`

---

## 4. Email (Gmail App Password)
- Go to [Google Account Security](https://myaccount.google.com/security)
- Enable 2-Step Verification
- Create an **App Password** for your Gmail
- Use this as `SMTP_PASSWORD` in `.env`

---

## 5. Twilio, Telegram, Tavily, Groq, Ollama, etc.
- Get API keys from each provider's dashboard
- Paste them into `.env` as shown in `.env.example`

---

## 6. Azure Blob Storage
- Go to [Azure Portal > Storage Accounts](https://portal.azure.com/)
- Get the **Connection String** and **Container Name**
- Add to `.env` as `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER_NAME`

---

## 7. General Security Tips
- **Never commit real secrets to git**
- Always use `.env` and `*.example` files for sharing config structure
- Rotate credentials regularly
- Use strong, unique passwords and API keys

---

For more details, see the main [README.md](README.md).
