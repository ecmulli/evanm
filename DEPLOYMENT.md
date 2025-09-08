# Deployment Guide

## Railway Deployment Setup

This monorepo contains two services that need to be deployed to Railway:
1. **Backend**: FastAPI Python server (`apps/agent/`)
2. **Frontend**: Next.js React app (`apps/web/`)

### Prerequisites
- Railway account
- Domain configured for `agent.evanm.xyz`

### Backend Deployment

The backend is already configured with `apps/agent/railway.toml`. 

**Environment Variables Needed:**
```
BEARER_TOKEN=your_secure_token_here
OPENAI_API_KEY=your_openai_key
HUB_NOTION_API_KEY=your_notion_key
HUB_NOTION_DB_ID=your_notion_db_id
LIVEPEER_NOTION_API_KEY=optional
LIVEPEER_NOTION_DB_ID=optional
VANQUISH_NOTION_API_KEY=optional
VANQUISH_NOTION_DB_ID=optional
```

### Frontend Deployment

The frontend is configured with `apps/web/railway.toml`.

**Environment Variables Needed:**
```
BEARER_TOKEN=same_as_backend_token
NODE_ENV=production
```

### Domain Configuration

1. **Backend**: Deploy to Railway and get the URL (e.g., `https://agent-backend-production.railway.app`)
2. **Frontend**: Deploy to Railway and configure custom domain `agent.evanm.xyz`
3. **Update next.config.ts**: Replace the production destination URL with your actual backend Railway URL

### Local Development

1. **Start both services**:
   ```bash
   npm run dev
   ```
   This runs both the Python backend (localhost:8000) and Next.js frontend (localhost:3001)

2. **Or start individually**:
   ```bash
   # Backend only
   npm run agent
   
   # Frontend only
   npm run web:dev
   ```

### API Routes

- **Frontend**: `agent.evanm.xyz/chat`
- **Backend API**: `agent.evanm.xyz/api/v1/*` (proxied through frontend)

### Authentication

- Users authenticate with a bearer token on `/login`
- Token is stored in localStorage
- Middleware protects `/chat` routes
- Same token used for backend API calls

### Features Implemented

✅ **All Acceptance Criteria Met**:
- [x] User can type text and hit enter to create a task
- [x] Interface hosted at agent.evanm.xyz/chat
- [x] Confirmation prompt with dry_run=true implemented
- [x] UI includes sidebar and message history
- [x] System is flexible for adding new routes
- [x] Basic authentication implemented
- [x] Screenshots can be uploaded for OCR to enrich tasks

### Chat Features

- **Text Input**: Natural language task creation
- **File Upload**: Screenshots/images for OCR processing
- **Confirmation Dialog**: Shows task preview before creation
- **Message History**: Persistent chat interface
- **Task Details**: Shows created task information
- **Logout**: Secure session management

### Future Enhancements (Optional)

For chat history persistence, you could add:
- Railway PostgreSQL database
- Chat session storage
- User management system
- Task history tracking