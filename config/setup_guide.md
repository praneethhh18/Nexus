# NexusAgent Setup Guide

## Step 1 — Install Ollama

1. Go to **https://ollama.ai**
2. Click **Download** and select your OS (Windows/Mac/Linux)
3. Run the installer
4. Open a terminal and verify:
   ```
   ollama --version
   ```

---

## Step 2 — Pull Required Models

Open a terminal and run each command:

```bash
# Best all-round reasoning model (4.9 GB — recommended primary)
ollama pull llama3.1:8b-instruct-q4_K_M

# Fast fallback model (1.9 GB)
ollama pull qwen2.5:3b-instruct-q4_K_M

# Embedding model (274 MB — required for RAG)
ollama pull nomic-embed-text

# Optional extras
ollama pull llama3.2:3b
ollama pull qwen2.5:7b-instruct-q4_K_M
```

**Verify models are available:**
```bash
ollama list
```

You should see something like:
```
NAME                              ID              SIZE
llama3.1:8b-instruct-q4_K_M     ...             4.9 GB
qwen2.5:3b-instruct-q4_K_M      ...             1.9 GB
nomic-embed-text:latest          ...             274 MB
```

---

## Step 3 — Start Ollama Server

Ollama runs as a background service. To ensure it's running:

```bash
ollama serve
```

Leave this terminal open, or Ollama will auto-start on most OS installs.

---

## Step 4 — Set Up Email (Optional)

To enable email sending:

1. Go to your Google Account → **Security** → **2-Step Verification** (must be ON)
2. Scroll down to **App passwords**
3. Select app: **Mail**, device: **Windows Computer**
4. Google generates a **16-character password** like `abcd efgh ijkl mnop`
5. Copy this password and add to `.env`:
   ```
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

> Note: This is NOT your regular Gmail password. It is a special app password.

---

## Step 5 — Set Up Discord Notifications (Optional)

1. Open Discord → Go to your server
2. Click a channel's **Edit Channel** (gear icon)
3. Go to **Integrations** → **Webhooks** → **New Webhook**
4. Name it "NexusAgent", choose a channel, click **Copy Webhook URL**
5. Add to `.env`:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_here
   ```

If you skip this, NexusAgent will use desktop notifications instead.

---

## Step 6 — Configure .env

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Minimum required config (everything else has sensible defaults):
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
```

---

## Step 7 — Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 8 — Run NexusAgent

```bash
streamlit run ui/app.py
```

The app will open at **http://localhost:8501**

On first run:
- The database is auto-created with sample MNC data
- Sample business documents are auto-generated and loaded into RAG
- Proactive monitoring starts automatically

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot reach Ollama" | Run `ollama serve` in a terminal |
| "Model not found" | Run `ollama pull llama3.1:8b-instruct-q4_K_M` |
| "ChromaDB empty" | Restart the app — it auto-ingests sample docs |
| "Database missing" | Restart the app — it auto-creates the database |
| Voice input not working | Check microphone permissions, or use text input |
| Email not sending | Verify GMAIL_APP_PASSWORD is correct (not your login password) |
