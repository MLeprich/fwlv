# Production Deployment Checklist

## Pre-Deployment Checks

### 1. Environment Configuration
- [ ] `.env` file configured with production values
- [ ] `SECRET_KEY` set to secure random value (not default)
- [ ] `DEBUG=False` in environment
- [ ] `ALLOWED_HOSTS` contains production domain(s)
- [ ] `DATABASE_URL` points to production database
- [ ] `REDIS_URL` points to production Redis instance
- [ ] `CELERY_BROKER_URL` configured correctly
- [ ] Email settings configured (SMTP)
- [ ] `ADMIN_URL` set to non-default secure path

### 2. Security Validation
- [ ] All forms have CSRF protection
- [ ] All views require authentication (@login_required or LoginRequiredMixin)
- [ ] Object-level permissions implemented where needed
- [ ] File upload size limits configured (20MB)
- [ ] HTTPS enforcement enabled (`SECURE_SSL_REDIRECT=True`)
- [ ] HSTS header configured (1 year)
- [ ] Secure cookies enabled (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- [ ] X-Frame-Options set to DENY
- [ ] Content-Type nosniff enabled
- [ ] Django Axes configured for brute-force protection

### 3. Database
- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Database backup strategy in place
- [ ] Database connection pooling enabled (CONN_MAX_AGE=600)
- [ ] Database performance indexes created
- [ ] No pending migrations (`python manage.py showmigrations`)

### 4. Static Files
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Whitenoise configured for static file serving
- [ ] Static file compression enabled
- [ ] Media files directory writable by web server

### 5. Redis & Caching
- [ ] Redis server running and accessible
- [ ] Redis authentication configured if needed
- [ ] Cache keys prefixed (`flvs_prod`)
- [ ] Session backend using Redis
- [ ] Celery connected to Redis broker

### 6. Celery Background Tasks
- [ ] Celery worker running
- [ ] Celery beat scheduler running (for periodic tasks)
- [ ] Celery monitoring in place
- [ ] Task queue size monitored

### 7. Web Server (Nginx + Gunicorn)
- [ ] Nginx configured with SSL certificate
- [ ] SSL certificate valid and not expired
- [ ] Gunicorn running as systemd service
- [ ] Gunicorn worker count appropriate (2-4 x CPU cores)
- [ ] Gunicorn timeout configured (30s default)
- [ ] Static files served by Nginx (not Django)
- [ ] Media files served by Nginx (not Django)
- [ ] Rate limiting configured in Nginx

### 8. Logging & Monitoring
- [ ] Log directory writable (`/logs/`)
- [ ] Log rotation configured (RotatingFileHandler)
- [ ] Audit log for sensitive operations (BTM, permissions)
- [ ] Security log for failed logins, permission denials
- [ ] Error tracking configured (Sentry optional)
- [ ] Application monitoring in place

### 9. Permissions & Users
- [ ] Superuser account created
- [ ] Default permissions and groups created
- [ ] Test user accounts removed
- [ ] Password policies enforced (min 10 characters)
- [ ] 2FA enabled for BTM users (if BTM module active)

### 10. Performance Optimization
- [ ] Database query optimization (select_related, prefetch_related)
- [ ] Database indexes on frequently queried fields
- [ ] Template caching enabled in production
- [ ] View caching configured for dashboards
- [ ] Redis cache timeout configured (5 minutes default)

### 11. Backup & Recovery
- [ ] Database backup script configured
- [ ] Daily full backups scheduled
- [ ] Backup retention policy (30 days daily, 12 months weekly)
- [ ] Media files backup scheduled
- [ ] Backup encryption enabled (AES-256)
- [ ] Restore procedure tested

### 12. Testing
- [ ] All critical user flows tested in production-like environment
- [ ] Login/Logout working
- [ ] Personnel CRUD operations working
- [ ] Qualifications management working
- [ ] Inspections tracking working
- [ ] Duty hours tracking working
- [ ] File uploads working
- [ ] Email notifications working (if configured)
- [ ] Reports generation working
- [ ] Export functionality tested (Excel, CSV)

## Deployment Steps

### 1. Code Deployment
```bash
# Pull latest code
cd /var/www/lager.resqware.de
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply migrations
python manage.py migrate --noinput
```

### 2. Service Restart
```bash
# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Celery
sudo systemctl restart celery
sudo systemctl restart celerybeat

# Reload Nginx
sudo systemctl reload nginx
```

### 3. Cache Clearing (if needed)
```bash
# Clear Django cache
python manage.py cache_clear

# Or restart Redis
sudo systemctl restart redis
```

### 4. Verification
```bash
# Check Gunicorn status
sudo systemctl status gunicorn

# Check Celery status
sudo systemctl status celery
sudo systemctl status celerybeat

# Check Nginx status
sudo systemctl status nginx

# Check Redis status
sudo systemctl status redis

# Check logs for errors
tail -f /var/www/lager.resqware.de/logs/flvs.log
tail -f /var/log/nginx/error.log
```

## Post-Deployment Checks

- [ ] Website loads correctly (https://lager.resqware.de)
- [ ] SSL certificate valid (green lock in browser)
- [ ] Login working
- [ ] Dashboard loads with correct data
- [ ] No JavaScript errors in browser console
- [ ] No 500 errors in logs
- [ ] Database queries performing well (check query time in logs)
- [ ] Redis cache hit rate acceptable
- [ ] Email notifications working (test send)
- [ ] Background tasks executing (check Celery logs)

## Rollback Procedure

If issues occur after deployment:

```bash
# 1. Rollback code
git reset --hard <previous-commit-hash>

# 2. Rollback migrations (if database changes were made)
python manage.py migrate <app_name> <previous_migration_number>

# 3. Restart services
sudo systemctl restart gunicorn celery celerybeat

# 4. Clear cache
python manage.py cache_clear
```

## Security Hardening (Optional but Recommended)

- [ ] Fail2ban configured for SSH and HTTP brute-force protection
- [ ] UFW firewall configured (allow only 22, 80, 443)
- [ ] Automatic security updates enabled
- [ ] SSH key-only authentication (disable password auth)
- [ ] Non-root user for application
- [ ] Database not exposed to public internet
- [ ] Redis password authentication enabled
- [ ] Rate limiting at Nginx level (10 req/sec per IP)

## Maintenance Tasks

### Daily
- Monitor logs for errors
- Check disk space
- Verify backups completed successfully

### Weekly
- Review security logs for suspicious activity
- Check SSL certificate expiry date
- Review database performance metrics
- Test backup restore procedure

### Monthly
- Update dependencies (`pip list --outdated`)
- Review and optimize slow database queries
- Rotate logs older than 30 days
- Test disaster recovery procedure

## Performance Monitoring

### Key Metrics to Track
- Response time (target: <200ms for p95)
- Database query count per request (target: <20)
- Cache hit rate (target: >80%)
- Celery task queue size (target: <100)
- Memory usage (target: <80%)
- CPU usage (target: <70% average)
- Disk space (target: >20% free)

### Tools
- Django Debug Toolbar (development only)
- Gunicorn logs (response time per request)
- PostgreSQL slow query log
- Redis INFO command (cache stats)
- Nginx access logs (request rate)

## Emergency Contacts

- **System Administrator:** [Name, Phone, Email]
- **Database Administrator:** [Name, Phone, Email]
- **Developer Lead:** [Name, Phone, Email]
- **Feuerwehr Contact:** [Name, Phone, Email]

## References

- [CLAUDE.md](CLAUDE.md) - Project architecture and conventions
- [PERMISSIONS.md](PERMISSIONS.md) - Permission system documentation
- [DATA_MODEL.md](DATA_MODEL.md) - Database schema documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment instructions

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0
**Reviewed By:** [Name]
**Next Review Date:** [Date + 3 months]
