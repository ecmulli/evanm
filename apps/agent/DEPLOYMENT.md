# Railway Deployment Guide

## 🚀 Quick Deploy to Railway

1. **Push to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "feat: add Railway deployment with bearer token auth"
   git push origin main
   ```

2. **Create Railway Project**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Choose the `packages/agent` directory as the root

3. **Set Environment Variables** in Railway dashboard:
   ```
   OPENAI_API_KEY=your_openai_api_key
   HUB_NOTION_API_KEY=your_notion_api_key  
   HUB_NOTION_DB_ID=your_notion_database_id
   BEARER_TOKEN=your_secure_random_token
   DEBUG=false
   ```

## 🔐 Authentication

The API now requires a bearer token for all requests:

```bash
# Example authenticated request
curl -X POST https://your-app.railway.app/api/v1/task_creator \
  -H "Authorization: Bearer your_secure_token" \
  -H "Content-Type: application/json" \
  -d '{"text_inputs": ["Your task description"], "dry_run": true}'
```

## 🏥 Health Check

Railway will automatically health check the service at:
- `GET /api/v1/health`

## 📝 Bearer Token Generation

Generate a secure random token:
```bash
# Option 1: OpenSSL
openssl rand -hex 32

# Option 2: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 3: Online generator
# Use a secure random token generator
```

## 🔄 Updates

To deploy updates:
1. Push changes to GitHub
2. Railway automatically redeploys
3. Monitor logs in Railway dashboard

## 🐛 Troubleshooting

- **Build fails**: Check Dockerfile and dependencies
- **Health check fails**: Verify the `/api/v1/health` endpoint
- **Auth errors**: Ensure BEARER_TOKEN is set and correct
- **OpenAI errors**: Verify OPENAI_API_KEY is valid
- **Notion errors**: Check Notion API keys and database IDs

## 📊 Monitoring

Monitor your deployment:
- Railway dashboard shows logs, metrics, and health
- Health endpoint: `https://your-app.railway.app/api/v1/health`
- API docs: `https://your-app.railway.app/docs`
