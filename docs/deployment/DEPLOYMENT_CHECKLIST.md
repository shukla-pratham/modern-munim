# Production Deployment Checklist

## Pre-Deployment

### Environment Variables

**⚠️ IMPORTANT**: **NO external API keys are required**. All values are internal secrets or your own infrastructure URLs.

**Required**:
- [ ] `DATABASE_URL` - PostgreSQL connection string (production database)
  - **Type**: Connection string (not an API key)
  - **Get from**: Your PostgreSQL provider (Railway, Render, Supabase, Neon)
- [ ] `SECRET_KEY` - Strong secret key (min 32 chars)
  - **Type**: Internal secret (NOT an external API key)
  - **Generate**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - **Purpose**: JWT token signing (internal use only)

**Optional** (have defaults):
- [ ] `ALGORITHM` - JWT algorithm (default: HS256)
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)
- [ ] `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- [ ] `LOG_LEVEL` - Logging level (INFO for production)
- [ ] `ENVIRONMENT` - Set to "production"

See `CONFIGURATION.md` for complete details.

### Database Setup
- [ ] Create production PostgreSQL database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify all tables created correctly
- [ ] Create database indexes (most are auto-created, verify)
- [ ] Set up database backups

### Backend Setup
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify Prophet installation (may require system dependencies)
- [ ] Test database connection
- [ ] Run seed data (optional, for demo)
- [ ] Set up logging (file or cloud logging service)

### Frontend Setup
- [ ] Install dependencies: `npm install`
- [ ] Set `NEXT_PUBLIC_API_URL` to production backend URL
  - **Type**: URL string (not an API key)
  - **Example**: `https://api.yourdomain.com`
- [ ] Build: `npm run build`
- [ ] Test build locally: `npm start`

## Deployment

### Backend (Railway/Render/Heroku)
- [ ] Deploy backend code
- [ ] Set all environment variables
- [ ] Run database migrations on first deploy
- [ ] Verify health check: `GET /health`
- [ ] Test API endpoints
- [ ] Set up scheduled job for AI batch processing (cron or scheduler)

### Frontend (Vercel/Netlify)
- [ ] Deploy frontend code
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable
- [ ] Verify CORS allows frontend origin
- [ ] Test authentication flow
- [ ] Test all user flows

## Post-Deployment

### Verification
- [ ] Health check returns healthy status
- [ ] Database connection working
- [ ] Authentication working (login/register)
- [ ] Customer can browse products
- [ ] Customer can create orders
- [ ] Admin can access admin endpoints
- [ ] Admin can manage products
- [ ] Admin can view AI insights
- [ ] AI batch job runs successfully

### Monitoring Setup
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Set up application logs
- [ ] Monitor database performance
- [ ] Set up alerts for:
  - Health check failures
  - High error rates
  - Database connection failures
  - Job failures

### Scheduled Jobs
- [ ] Set up daily AI batch job (recommended: 2 AM)
- [ ] Verify job locking works (no concurrent runs)
- [ ] Monitor job run history
- [ ] Set up alerts for job failures

## Security Checklist

- [ ] SECRET_KEY is strong and unique (32+ characters)
  - **Note**: This is internally generated, NOT an external API key
- [ ] Database credentials are secure
- [ ] CORS origins are restricted to production domains
- [ ] HTTPS enabled for all endpoints
- [ ] Admin endpoints require authentication
- [ ] Customer endpoints require authentication
- [ ] No sensitive data in logs
- [ ] Database backups encrypted
- [ ] No external API keys stored (none required)
- [ ] Environment variables properly secured

## Performance Checklist

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] API response times acceptable
- [ ] Frontend bundle size optimized
- [ ] Images optimized (if any)
- [ ] Caching configured (if applicable)

## Free-Tier Verification

- [ ] No paid services required ✅
- [ ] No external API keys needed ✅
- [ ] All dependencies are open-source ✅
- [ ] Free-tier hosting sufficient ✅
- [ ] Total cost: $0/month ✅

## Rollback Plan

- [ ] Keep previous deployment version available
- [ ] Database migration rollback plan
- [ ] Environment variable backup
- [ ] Test rollback procedure

## Maintenance

### Regular Tasks
- [ ] Monitor error logs daily
- [ ] Review job run history weekly
- [ ] Check database size and performance monthly
- [ ] Review and update dependencies quarterly
- [ ] Backup verification monthly

### Updates
- [ ] Test updates in staging first
- [ ] Run database migrations carefully
- [ ] Verify backward compatibility
- [ ] Update documentation
