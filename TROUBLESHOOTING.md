# Troubleshooting Guide

## Common Development Issues

### 1. Code Changes Not Appearing (Python Backend)

**Incident Date:** October 21, 2025
**Time Lost:** 2+ hours

#### Symptoms
- Fixed code in files, but bug still appears when testing
- Test script shows fix working, but browser/API calls show old buggy behavior
- Changes work locally via test scripts but not via running server

#### Root Causes

**A. Python Bytecode Cache**
- Python caches compiled bytecode in `__pycache__` directories
- `uvicorn --reload` only watches for NEW file changes, doesn't reload existing cached modules
- Even with the fix in the `.py` file, the server may run old cached `.pyc` files

**B. Multiple Server Instances**
- Multiple `uvicorn` processes can run simultaneously
- Requests may randomly hit different servers (some with old code, some with new)
- Explains intermittent behavior: sometimes works, sometimes doesn't

#### Solution Checklist

Before debugging "why isn't my fix working":

```bash
# 1. Kill ALL Python processes
killall -9 python3 python

# 2. Clear ALL bytecode cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 3. Verify only ONE process on port 8000
lsof -i:8000
# Should show NOTHING or only your current server

# 4. Start fresh server
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Quick Diagnostic Script

Run this to check if your fix is actually loaded:

```bash
# Check if fix is in the file
grep -n "YOUR_FIX_PATTERN" services/your_service.py

# Check if there are multiple servers
lsof -i:8000

# Check for cached bytecode
find . -name "*.pyc" -path "./services/*"
```

---

### 2. Frontend Hitting Wrong Backend

**Incident Date:** October 21, 2025
**Time Lost:** 1+ hour (part of same troubleshooting session)

#### Symptoms
- Backend fix verified working via test scripts
- Backend fix verified in source code
- Browser still shows buggy behavior
- No requests appearing in local server logs

#### Root Cause
**Frontend `.env` pointing to production, not localhost**

The frontend has this configuration:
```javascript
// src/api/client.js
const API_URL = import.meta.env.VITE_API_URL || 'https://web-production-9c58.up.railway.app';
```

When `.env` contains:
```
VITE_API_URL=https://web-production-9c58.up.railway.app
```

**All browser requests go to Railway production, NOT your local server at localhost:8000**

#### Solution Checklist

When testing backend changes locally:

```bash
# 1. Check frontend .env
cd /Users/drewf/Desktop/Python/storyos-frontend
cat .env

# Should show:
# VITE_API_URL=http://localhost:8000

# 2. If pointing to Railway, fix it:
echo "VITE_API_URL=http://localhost:8000" > .env

# 3. Restart frontend (REQUIRED - Vite loads .env at startup)
# Kill the dev server (Ctrl+C) and restart:
npm run dev

# 4. Hard refresh browser
# Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

# 5. Verify requests hit local server
# Watch backend logs for incoming requests
```

#### Quick Diagnostic

```bash
# Check where frontend is pointing
cd /Users/drewf/Desktop/Python/storyos-frontend
cat .env

# Check if local backend is receiving requests
cd /Users/drewf/Desktop/Python/storyos_protoype
# Watch server logs - you should see requests when using browser

# Check if Railway is receiving requests instead
# If Railway shows new data but local doesn't, frontend is hitting Railway
```

---

### 3. When to Use Localhost vs Railway

#### Development (Testing Changes)
```bash
# Frontend .env
VITE_API_URL=http://localhost:8000

# Start both servers
cd /Users/drewf/Desktop/Python/storyos_protoype
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

cd /Users/drewf/Desktop/Python/storyos-frontend
npm run dev
```

#### Production (Sharing with Colleagues)
```bash
# Frontend .env
VITE_API_URL=https://web-production-9c58.up.railway.app

# Commit and push to trigger deployments
```

#### Quick Switch Commands

**Switch to local development:**
```bash
cd /Users/drewf/Desktop/Python/storyos-frontend
echo "VITE_API_URL=http://localhost:8000" > .env
# Restart frontend dev server
```

**Switch to production:**
```bash
cd /Users/drewf/Desktop/Python/storyos-frontend
echo "VITE_API_URL=https://web-production-9c58.up.railway.app" > .env
# Restart frontend dev server OR commit/push for Vercel
```

---

## General Debugging Workflow

### 1. Verify Your Fix Is Actually in the Code
```bash
# Search for your fix in the file
grep -n "PATTERN" path/to/file.py

# Check git diff to see uncommitted changes
git diff path/to/file.py
```

### 2. Verify Only One Server is Running
```bash
# Check for Python processes
ps aux | grep uvicorn

# Check what's on port 8000
lsof -i:8000

# Should see only ONE process
```

### 3. Verify Cache is Cleared
```bash
# List pycache directories
find . -name "__pycache__" -type d

# Should be empty or not exist after clearing
```

### 4. Verify Frontend is Hitting the Right Backend
```bash
# Check frontend env
cat /Users/drewf/Desktop/Python/storyos-frontend/.env

# Watch backend logs for requests
# When you use the browser, you should see requests appear
```

### 5. Test in Isolation
```bash
# Test backend directly with Python script (bypasses cache issues)
python test_script.py

# Test backend via curl
curl http://localhost:8000/health

# Test backend via frontend
# Use browser, watch for requests in backend logs
```

---

## Prevention

### Daily Development Checklist

**Starting development session:**
1. ✅ Check `.env` points to `http://localhost:8000`
2. ✅ Kill old Python processes: `killall -9 python3 python`
3. ✅ Clear cache: `find . -type d -name "__pycache__" -exec rm -rf {} +`
4. ✅ Start backend fresh: `uvicorn main:app --reload`
5. ✅ Start frontend: `npm run dev`

**Before deploying to production:**
1. ✅ Test fix locally first
2. ✅ Update `.env` to Railway URL
3. ✅ Commit and push backend changes
4. ✅ Verify Railway deployment
5. ✅ Commit and push frontend changes
6. ✅ Verify Vercel deployment

---

## Incident Log

### October 21, 2025 - Voice Transformation Bug

**Issue:** "Empowering" → "EmpoHexagon ABring"

**Fix Applied:** Word boundary regex in `services/voice_transformer.py:72`

**Troubleshooting Time:** 2+ hours

**Root Causes Found:**
1. Python bytecode cache had old code
2. Frontend `.env` pointed to Railway instead of localhost
3. Both issues made it appear fix wasn't working when it actually was

**Resolution:**
1. Cleared `__pycache__` directories
2. Restarted backend with fresh Python process
3. Updated frontend `.env` to `localhost:8000`
4. Restarted frontend dev server
5. Hard refreshed browser

**Lessons Learned:**
- Always check which backend the frontend is using (`cat .env`)
- Always clear Python cache when code changes don't appear
- Always verify only one server instance is running
- Watch server logs to confirm requests are hitting the right backend

**Prevention Added:**
- Created this TROUBLESHOOTING.md guide
- Added development setup checklist
- Documented common pitfalls and solutions
