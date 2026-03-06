# Quick Start Guide

## 🚀 One-Command Startup

```bash
python run.py
```

That's it! This will:
1. ✓ Install frontend dependencies (if needed)
2. ✓ Start FastAPI backend on `http://localhost:8000`
3. ✓ Start React frontend on `http://localhost:5173`
4. ✓ Automatically open browser to frontend
5. ✓ Show you the dashboard

**Press Ctrl+C to stop everything**

---

## 📋 Prerequisites (One-Time Setup)

### 1. Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 3. Configure Credentials
```bash
# Copy template
cp .env.example .env

# Edit .env and add:
OPENAI_API_KEY=sk-proj-...your-key...
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
HUBSPOT_API_KEY=... (or CONVERTKIT_API_KEY=...)
```

### 4. Get Gmail App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Get 16-char password, paste in `.env` as `GMAIL_APP_PASSWORD`

---

## 🎯 Using the Application

### Settings (Do First!)
1. Open http://localhost:5173
2. Click "Settings" in sidebar
3. Paste in:
   - OpenAI API key
   - Gmail email + app password
4. Click "Test Connections" to verify
5. Click "Save Settings"

### Generate Campaign
1. Click "Generate" in sidebar
2. Select:
   - **Segment**: new_phoenix, active_phoenix, etc.
   - **Campaign Type**: onboarding, upsell_*, reactivation
   - **Recipient Count**: number of emails to generate
3. Click "Generate Campaign"
4. View generated emails with **blue citation links** (click to see source)
5. Markdown file automatically saved to `generated/` folder

### View Analytics
1. Click "Analytics" to see:
   - Weekly performance charts
   - Open rate, click rate, conversion rate
   - Optimization suggestions

### View Segments
1. Click "Segments" to see:
   - All audience segments
   - Contact distribution
   - Segment definitions

### Dashboard
1. Click "Dashboard" to see:
   - Key metrics overview
   - Quick action buttons
   - This week's summary

---

## 🔗 API Endpoints

All accessible from frontend, but can also use directly:

```bash
# Get all segments
curl http://localhost:8000/api/segments

# Generate campaign
curl -X POST http://localhost:8000/api/campaigns/generate \
  -H "Content-Type: application/json" \
  -d '{
    "segment": "new_phoenix",
    "campaign_type": "onboarding",
    "recipient_count": 100
  }'

# Get weekly analytics
curl http://localhost:8000/api/analytics/weekly-report

# RAG query
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "brand voice guidelines", "k": 3}'

# API Documentation
curl http://localhost:8000/docs  # Or visit in browser
```

---

## 🔍 Verify Setup

Run the verification script:
```bash
python verify_setup.py
```

This checks:
- ✓ Python version (3.9+)
- ✓ Virtual environment
- ✓ Dependencies installed
- ✓ Project files present
- ✓ .env configured
- ✓ Directories created

---

## 📁 Important Directories

```
generated/           # Campaign markdown files (output)
rag_index/          # FAISS vector index (auto-created)
frontend/           # React app
src/api/            # REST endpoints
src/rag/            # RAG pipeline
settings_store.json # Runtime credentials (git-ignored)
.env               # API keys (git-ignored)
```

---

## 🐛 Troubleshooting

### "Frontend won't load"
```bash
# Install dependencies manually
cd frontend
npm install
npm run dev
```

### "Port already in use"
The app uses ports 8000 and 5173. If they're in use:
```bash
# Kill the process using the port (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change ports in:
# - run.py (line with --port)
# - frontend/vite.config.js (port: 5173)
```

### "RAG index not working"
```bash
# Rebuild the index
curl http://localhost:8000/api/rag/rebuild-index

# Check status
curl http://localhost:8000/api/rag/index-status
```

### "Gmail not working"
- Verify App Password (16 chars, no hyphens)
- Check 2FA is enabled on Gmail account
- Test from Settings page → "Test Connections"

### "Settings not saving"
- Check write permissions in project directory
- Check `settings_store.json` exists
- Check file isn't locked by another process

---

## 📖 Documentation

- **IMPLEMENTATION_SUMMARY.md** - Complete technical overview
- **GETTING_STARTED.md** - Detailed setup instructions
- **SPECIFICATION.md** - Technical requirements
- **CLAUDE.md** - Development guidelines
- **API Docs** - http://localhost:8000/docs (interactive)

---

## 💡 Tips

1. **Save Campaign Files** - They're auto-saved to `generated/` with source links
2. **Test Before Send** - Always review generated content before sending
3. **Check Citations** - Click blue source links to see where content came from
4. **Monitor Analytics** - Track open/click rates to optimize future campaigns
5. **Rotate Credentials** - Regenerate API keys periodically for security

---

## 🔐 Security Notes

- Never commit `.env` file
- API keys are stored locally in `settings_store.json`
- Passwords are never shown in full (masked in UI)
- Use Gmail App Password, not your main password
- Delete credentials when done testing

---

## ✨ What's New (March 2026)

- **RAG Pipeline**: AI cites sources automatically
- **Full UI**: Professional React dashboard
- **Gmail Sending**: Send campaigns via email
- **One-Command Startup**: `python run.py` does everything
- **Settings Management**: Save credentials in UI
- **Citation Links**: Click to view source documents

---

**Questions?** Check IMPLEMENTATION_SUMMARY.md for detailed docs.
