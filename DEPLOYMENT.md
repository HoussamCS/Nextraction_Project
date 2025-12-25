# Deployment Guide - NEXTRACION

## Pre-Deployment Checklist

### Security ✅
- [x] API key NOT committed to git (using `.env.example`)
- [x] CORS restricted to specific domains (not `*`)
- [x] API docs disabled in production (redoc_url=None, docs_url=None)
- [ ] **TODO:** Add API key validation/authentication before production
- [ ] **TODO:** Set up HTTPS/SSL certificate
- [ ] **TODO:** Add rate limiting (implement with Nginx or dedicated service)

### Configuration ✅
- [x] Port configurable via `PORT` environment variable
- [x] Host configurable via `HOST` environment variable
- [x] CORS origins configurable via `ALLOWED_ORIGINS`
- [ ] **TODO:** Update ALLOWED_ORIGINS for your domain

### Data Persistence ⚠️
- [x] In-memory vector store enabled (temporary)
- [ ] **TODO:** For production, set up persistent Chroma DB or PostgreSQL

## Deployment Steps

### 1. Create `.env` file on your server

```bash
# Copy template
cp .env.example .env

# Edit with your values
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini
PORT=8001
HOST=0.0.0.0  # For production, expose to all interfaces (with firewall)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run with gunicorn (for production)

```bash
pip install gunicorn
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 src.main:app
```

Or use Docker:

```bash
docker build -t nextracion .
docker run -p 8001:8001 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ALLOWED_ORIGINS=https://yourdomain.com \
  nextracion
```

### 4. Set up reverse proxy (Nginx/Apache)

Recommend Nginx for HTTPS/SSL termination:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Monitor logs

```bash
# Check uvicorn logs
tail -f /var/log/nextracion.log

# Monitor API usage
curl http://127.0.0.1:8001/health
```

## Post-Deployment

### Critical Tasks
- [ ] Test CORS restriction (requests from wrong domain should fail)
- [ ] Verify only POST and GET methods are allowed
- [ ] Monitor OpenAI API costs
- [ ] Set up error alerts
- [ ] Backup vector database (if using persistent storage)
- [ ] Set up rate limiting via Nginx or API Gateway

### Optional Enhancements
- [ ] Add request size limits (URL length, question length)
- [ ] Add database connection pooling
- [ ] Set up caching layer (Redis)
- [ ] Add API authentication (JWT tokens)
- [ ] Add request logging and analytics
- [ ] Set up health check alerts

## Environment Variables Reference

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENAI_API_KEY` | ❌ Required | Your OpenAI API key |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model to use |
| `OPENAI_MODEL` | `text-embedding-3-small` | Embedding model |
| `PORT` | `8001` | Server port |
| `HOST` | `127.0.0.1` | Server host (0.0.0.0 for production) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:8001` | CORS origins |
| `TOP_K_CHUNKS` | `5` | Top chunks to retrieve per query |
| `MAX_DEPTH` | `2` | Web scraper max depth |
| `MAX_PAGES` | `10` | Web scraper max pages |

## Troubleshooting

### "429 Too Many Requests"
- Rate limiter is working correctly
- Increase time between requests or implement request queue

### "CORS error"
- Check `ALLOWED_ORIGINS` matches your frontend domain
- Must include protocol: `https://` not just domain.com

### "No relevant chunks found"
- Vector database might have restarted (data lost)
- Re-ingest the URLs
- For production, use persistent storage

### OpenAI API Errors
- Verify API key is valid
- Check API quota at https://platform.openai.com/account/billing/usage
- Monitor rate limits

## Cost Optimization

- **Embeddings**: ~$0.02 per 1M tokens (use text-embedding-3-small)
- **Chat**: ~$0.015 per 1K tokens (use gpt-4o-mini)
- Consider caching embeddings to reduce costs
- Implement request size limits

## Support

For issues:
1. Check logs: `tail -f your-log-file`
2. Test health: `curl http://yourserver:8001/health`
3. Verify `.env` file has all required variables
