# 🚀 Deployment Guide

Deploy AI Data Analyst to any Docker-compatible platform with minimal configuration changes.

## Quick Reference

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| Railway | Easy | $5-20/mo | Prototyping |
| Render | Easy | $7-25/mo | Small business |
| DigitalOcean App Platform | Easy | $12+/mo | Production |
| AWS ECS | Medium | Variable | Enterprise |
| Google Cloud Run | Medium | Pay-per-use | Startups |
| Azure Container Apps | Medium | Variable | Enterprise |
| Self-hosted VPS | Hard | $5+/mo | Full control |

## Universal Requirements

Every deployment needs:

1. **PostgreSQL 14+ database** (managed or self-hosted)
2. **Environment variables** set correctly
3. **Docker image** built and pushed to a registry
4. **Domain name** (optional but recommended)

## Environment Variables for Production

```env
# Required
DATABASE_URL=postgresql://user:pass@prod-host:5432/db
OPENROUTER_API_KEY=your-key
ENVIRONMENT=production

# Recommended
LOG_LEVEL=WARNING
APP_HOST=0.0.0.0
APP_PORT=8000

# Safety (tighter for prod)
QUERY_TIMEOUT_SECONDS=15
MAX_ROWS_PER_QUERY=500
```

---

## Railway Deployment

**Easiest option for MVP.**

### Steps:

1. **Sign up** at railway.app
2. **New Project** → Deploy from GitHub → Select `ai-data-analyst`
3. **Add PostgreSQL** service → Railway provisions it
4. **Set environment variables:**
   - Copy DATABASE_URL from Postgres service
   - Add OPENROUTER_API_KEY
   - Set ENVIRONMENT=production
5. **Deploy** — Railway auto-builds and deploys

### Cost:
- $5/month starter
- Scales automatically

### Domain:
Railway provides free `.up.railway.app` subdomain. Custom domain in settings.

---

## Render Deployment

**Free tier available for testing.**

### Steps:

1. **Sign up** at render.com
2. **New Web Service** → Connect GitHub repo
3. **Configure:**
   - Runtime: Docker
   - Region: Nearest to users
   - Instance: Starter ($7/mo) or Free
4. **Add PostgreSQL:**
   - New PostgreSQL service
   - Copy Internal Database URL
5. **Environment Variables:**
   - DATABASE_URL (from step 4)
   - OPENROUTER_API_KEY
   - ENVIRONMENT=production
6. **Deploy**

### Free Tier Limitations:
- Spins down after inactivity
- Slower cold starts
- Limited hours/month

---

## DigitalOcean App Platform

**Reliable and affordable.**

### Steps:

1. **Create App** → Docker → GitHub repo
2. **Add Database** → PostgreSQL
3. **Environment:**
   - Auto-inject DATABASE_URL from managed DB
   - Add secrets for API keys
4. **Deploy**

### Cost:
- $12/month basic (512MB RAM)
- $25/month professional (1GB RAM)
- Managed DB: $15/month

---

## AWS ECS (Fargate)

**Enterprise-grade, more complex setup.**

### Steps:

1. **Push image to ECR:**
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_ECR
docker build -t ai-data-analyst .
docker tag ai-data-analyst YOUR_ECR/ai-data-analyst:latest
docker push YOUR_ECR/ai-data-analyst:latest
```

2. **Create ECS cluster** (Fargate launch type)

3. **Create task definition:**
   - Image: from ECR
   - Port: 8000
   - Environment variables
   - Log configuration (CloudWatch)

4. **Create service:**
   - Load balancer (ALB)
   - Auto-scaling policies
   - Health checks

5. **Add RDS PostgreSQL:**
   - Instance in same VPC
   - Security group allows ECS

### Cost:
- Fargate: ~$15/mo (0.25 vCPU, 0.5GB)
- RDS t4g.micro: $15/mo
- ALB: $16/mo
- Total: ~$50/mo minimum

---

## Google Cloud Run

**Pay-per-use, great for variable traffic.**

### Steps:

1. **Push image:**
```bash
gcloud auth configure-docker
docker build -t gcr.io/YOUR_PROJECT/ai-data-analyst .
docker push gcr.io/YOUR_PROJECT/ai-data-analyst
```

2. **Deploy:**
```bash
gcloud run deploy ai-data-analyst \
  --image gcr.io/YOUR_PROJECT/ai-data-analyst \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=xxx,DATABASE_URL=xxx,ENVIRONMENT=production
```

3. **Add Cloud SQL PostgreSQL** for database

### Cost:
- Free tier: 2M requests/month
- Pay-per-use after
- Cloud SQL: $10-25/mo

---

## Self-Hosted VPS (Ubuntu)

**Full control, cheapest for high volume.**

### Setup:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Install Docker Compose
sudo apt install docker-compose

# 3. Clone repo
git clone https://github.com/sriharshpragya/ai-data-analyst.git
cd ai-data-analyst

# 4. Configure
cp .env.example .env
nano .env  # Set your keys

# 5. Set production env
export ENVIRONMENT=production

# 6. Deploy
docker-compose up -d

# 7. Setup nginx reverse proxy
# ... (nginx config example)

# 8. Get SSL cert
# ... (certbot example)
```

### Cost:
- DigitalOcean droplet: $6/mo (1GB)
- Hetzner: $4/mo (2GB)
- Contabo: $5/mo (4GB)

---

## Production Checklist

Before going live:

### Security
- [ ] Use production API keys (not development)
- [ ] Set ENVIRONMENT=production
- [ ] Use dedicated PostgreSQL user with READ-ONLY permissions
- [ ] Enable SSL/TLS for database connection
- [ ] Enable HTTPS on web app
- [ ] Set up firewall rules
- [ ] Remove Adminer from production (or password protect)
- [ ] Rotate credentials regularly

### Reliability
- [ ] Set up health check monitoring
- [ ] Configure auto-restart on failure
- [ ] Set resource limits (memory, CPU)
- [ ] Enable logging aggregation
- [ ] Set up backup strategy for DB
- [ ] Configure error tracking (Sentry)

### Performance
- [ ] Enable connection pooling
- [ ] Configure appropriate timeouts
- [ ] Set up CDN for static files
- [ ] Enable gzip compression
- [ ] Monitor and tune query costs

### Monitoring
- [ ] Application logs
- [ ] Database queries
- [ ] Error rates
- [ ] Response times
- [ ] Cost tracking

---

## Scaling Strategies

### Vertical Scaling
- Increase container resources
- Upgrade database tier
- Simple but limited

### Horizontal Scaling
- Multiple app instances behind load balancer
- Requires shared state management
- Better for high traffic

### Database Scaling
- Read replicas for query offloading
- Connection pooling (PgBouncer)
- Query result caching (Redis)

---

## Common Issues

### Database Connection Fails
Cause: Wrong DATABASE_URL format
Fix: Verify username:password@host:port/db format
### High Latency
Cause: LLM API in different region
Fix: Choose LLM provider region closest to app
### Out of Memory
Cause: Large query results
Fix: Reduce MAX_ROWS_PER_QUERY
### Timeout Errors
Cause: Slow queries
Fix: Add database indexes, increase QUERY_TIMEOUT

---

## Support

Issues? Open a GitHub issue.

Selling this? Consider offering deployment as a service.
