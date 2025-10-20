# StoryOS API - Deployment Info

## 🚀 Live Deployment

**Production URL:** https://web-production-9c58.up.railway.app

### API Documentation
- **Interactive Docs (Swagger):** https://web-production-9c58.up.railway.app/docs
- **Alternative Docs (ReDoc):** https://web-production-9c58.up.railway.app/redoc
- **API Info:** https://web-production-9c58.up.railway.app/

### Health Check
- **Health Endpoint:** https://web-production-9c58.up.railway.app/health

---

## 📡 API Endpoints

### UNF (Unified Narrative Framework)
- `GET /unf/layers` - List all layers
- `GET /unf/elements` - List elements (filter by layer/status)
- `POST /unf/elements` - Create element
- `PUT /unf/elements/{id}` - Update element (creates new version)
- `GET /unf/elements/{id}/versions` - Get version history

**Example:**
```bash
curl https://web-production-9c58.up.railway.app/unf/layers
```

### Brand Voices
- `GET /voices` - List all voices
- `GET /voices/{id}` - Get specific voice

**Example:**
```bash
curl https://web-production-9c58.up.railway.app/voices
```

### Story Models
- `GET /story-models` - List all story models
- `GET /story-models/{id}` - Get specific model

**Example:**
```bash
curl https://web-production-9c58.up.railway.app/story-models
```

### Templates
- `GET /templates` - List all templates
- `GET /templates/{id}` - Get template with bindings

**Example:**
```bash
curl https://web-production-9c58.up.railway.app/templates
```

### Deliverables
- `GET /deliverables` - List all deliverables
- `POST /deliverables` - Create deliverable
- `GET /deliverables/{id}/with-alerts` - Get with impact alerts ⚠️

**Example:**
```bash
curl https://web-production-9c58.up.railway.app/deliverables
```

---

## 🔧 Railway Configuration

### Environment Variables Set:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for database access

### Deployment Method:
- **GitHub Repository:** https://github.com/FirstPersonSF/storyos-api
- **Auto-deploy:** Enabled (pushes to `main` branch trigger deployments)
- **Platform:** Railway (https://railway.com)

### Build Configuration:
- **Runtime:** Python 3.13 (from `runtime.txt`)
- **Dependencies:** Installed from `requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (from `Procfile`)

---

## 🛠️ Railway CLI Usage

### Setup:
```bash
# Login to Railway
railway login

# Link to project (run in project directory)
cd /Users/drewf/Desktop/Python/storyos_protoype
railway link
```

### Common Commands:
```bash
# Deploy current code
railway up

# View live logs
railway logs

# Open project dashboard
railway open

# Check deployment status
railway status

# Set environment variable
railway variables set KEY=value

# Run script in Railway environment
railway run python scripts/check_data.py
```

---

## 📊 Current Data

The database is pre-loaded with test data:
- **3 UNF Layers:** Category, Vision, Messaging
- **6 UNF Elements:** Including Vision Statement, Problem, Principles, etc.
- **2 Brand Voices:** Corporate Brand Voice, Product Division Voice
- **2 Story Models:** PAS (Problem-Agitate-Solve), Inverted Pyramid
- **2 Deliverable Templates:** Brand Manifesto, Press Release
- **2 Sample Deliverables:** Created by workflow test

---

## 🔄 Making Changes

### Update Code:
```bash
# Make your changes locally
git add .
git commit -m "Your commit message"
git push origin main

# Railway will automatically deploy
```

### Update Environment Variables:
1. Go to Railway dashboard
2. Select your project
3. Click "Variables" tab
4. Add/edit variables
5. Deployment will restart automatically

### View Deployment Logs:
```bash
railway logs --follow
```

Or view in Railway dashboard.

---

## 🧪 Testing the API

### Test with curl:
```bash
# Get API info
curl https://web-production-9c58.up.railway.app/

# Get all layers
curl https://web-production-9c58.up.railway.app/unf/layers

# Get all elements
curl https://web-production-9c58.up.railway.app/unf/elements

# Get deliverables
curl https://web-production-9c58.up.railway.app/deliverables
```

### Test with Python:
```python
import requests

# Get all layers
response = requests.get('https://web-production-9c58.up.railway.app/unf/layers')
layers = response.json()
print(layers)

# Create a new element
new_element = {
    "layer_id": "ef50e3d1-46d2-4789-b712-e74bbd935f3e",
    "name": "Test Element",
    "content": "This is a test element",
    "version": "1.0",
    "status": "draft"
}
response = requests.post(
    'https://web-production-9c58.up.railway.app/unf/elements',
    json=new_element
)
print(response.json())
```

### Test with JavaScript/Fetch:
```javascript
// Get all deliverables
fetch('https://web-production-9c58.up.railway.app/deliverables')
  .then(response => response.json())
  .then(data => console.log(data));

// Create a deliverable
fetch('https://web-production-9c58.up.railway.app/deliverables', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: "My Deliverable",
    template_id: "bead3239-b220-4c3a-acd0-8ab0b22a1e60",
    status: "draft",
    instance_data: {},
    metadata: {}
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 🎯 Next Steps

### Potential Enhancements:
1. **Frontend UI** - Build React/Vue app to interact with API
2. **Authentication** - Add user authentication and authorization
3. **Neo4j Integration** - Connect graph database for relationship tracking
4. **LLM Integration** - Add AI-powered Brand Voice transformation
5. **WebSockets** - Real-time updates for impact alerts
6. **Email Notifications** - Alert users when Elements are updated
7. **Export Functionality** - Export Deliverables to PDF/Word
8. **Version Comparison** - Visual diff between Element versions

### Database Management:
```bash
# Run scripts via Railway CLI
railway run python scripts/check_data.py
railway run python scripts/load_dummy_data.py
railway run python scripts/clear_all_data.py
```

---

## 📝 Support

- **GitHub Repository:** https://github.com/FirstPersonSF/storyos-api
- **Railway Dashboard:** https://railway.com/dashboard
- **API Documentation:** https://web-production-9c58.up.railway.app/docs

---

**Deployed:** October 20, 2025
**Version:** 1.0.0
**Platform:** Railway
**Runtime:** Python 3.13.3
