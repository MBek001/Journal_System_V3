# Security Policy

## 🔒 Security Overview

This document outlines the security measures implemented in the Imfaktor Journal System and provides recommendations for maintaining security.

## ✅ Implemented Security Features

### 1. **Environment Variables (CRITICAL)**
- `SECRET_KEY` moved to environment variables
- `EMAIL_HOST_PASSWORD` moved to environment variables
- `DEBUG` configurable via environment
- `ALLOWED_HOSTS` configurable via environment

### 2. **Session Security**
- Session duration reduced from 2 weeks to 1 hour
- `SESSION_COOKIE_HTTPONLY = True` (prevents JavaScript access)
- Production HTTPS-only cookies via `SESSION_COOKIE_SECURE`

### 3. **Security Headers**
```python
# Production security headers (when DEBUG=False)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 4. **Django Built-in Protection**
- CSRF middleware enabled
- SQL injection protection via Django ORM
- XSS protection via template auto-escaping

## ⚠️ Known Security Issues (TO BE FIXED)

### Critical Priority

1. **Admin Authentication System**
   - **Issue**: Custom admin login uses plain text credentials comparison
   - **File**: `main/admin_views.py:22-24`
   - **Recommendation**: Replace with Django's built-in User model
   ```python
   from django.contrib.auth import authenticate, login

   user = authenticate(username=username, password=password)
   if user is not None:
       login(request, user)
   ```

2. **No Rate Limiting on Login**
   - **Issue**: Admin login endpoint vulnerable to brute force
   - **File**: `main/admin_views.py:27-42`
   - **Recommendation**: Install and implement django-ratelimit
   ```bash
   pip install django-ratelimit
   ```
   ```python
   from django_ratelimit.decorators import ratelimit

   @ratelimit(key='ip', rate='5/h', method='POST')
   def admin_login(request):
       # ...
   ```

3. **HTML Injection via |safe Filter**
   - **Issue**: User-controlled content marked as safe in templates
   - **Files**: `templates/article_detail.html`, `templates/author_detail.html`, etc.
   - **Recommendation**: Install bleach and sanitize HTML
   ```bash
   pip install bleach
   ```
   ```python
   import bleach

   # In model save() method or form clean():
   self.abstract = bleach.clean(
       self.abstract,
       tags=['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li'],
       attributes={'a': ['href', 'title']},
       strip=True
   )
   ```

4. **File Upload Validation**
   - **Issue**: Only MIME type validation, no magic bytes check
   - **File**: `main/views.py:268-271`
   - **Recommendation**: Use python-magic for file validation
   ```bash
   pip install python-magic
   ```
   ```python
   import magic

   def validate_pdf(file):
       mime = magic.from_buffer(file.read(2048), mime=True)
       file.seek(0)
       return mime == 'application/pdf'
   ```

### High Priority

5. **Print Statements in Production**
   - **Issue**: Debug information exposed in logs
   - **Files**: `main/views.py`, `main/admin_views.py`
   - **Action**: Replace all `print()` with proper logging
   ```python
   import logging
   logger = logging.getLogger(__name__)

   # Replace:
   print(f"Error: {error}")
   # With:
   logger.error(f"Error: {error}")
   ```

6. **Empty Exception Handlers**
   - **Issue**: Errors silently ignored
   - **Files**: `main/admin_views.py` (multiple locations)
   - **Action**: Catch specific exceptions and log
   ```python
   # Replace:
   try:
       journal.cover_image.delete()
   except:
       pass

   # With:
   try:
       journal.cover_image.delete()
   except (FileNotFoundError, AttributeError) as e:
       logger.warning(f"Could not delete cover image: {e}")
   ```

### Medium Priority

7. **Database Query Optimization**
   - Add database indexes to frequently queried fields:
   ```python
   # In models.py
   slug = models.SlugField(..., db_index=True)
   is_published = models.BooleanField(..., db_index=True)
   ```

8. **Missing Security Headers (OPTIONAL)**
   - Consider adding Content Security Policy (CSP)
   - Add Permissions-Policy header

## 🚀 Deployment Checklist

Before deploying to production, ensure:

- [ ] Create `.env` file with all required environment variables (see `.env.example`)
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set `SECRET_KEY` to a new, random value (generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- [ ] Configure `EMAIL_HOST_PASSWORD` with app-specific password
- [ ] Set up HTTPS certificate (Let's Encrypt recommended)
- [ ] Configure database backups
- [ ] Set up monitoring and logging
- [ ] Review and remove all print() statements
- [ ] Implement rate limiting on login endpoints
- [ ] Replace custom admin auth with Django User model

## 🔑 Environment Variables Required

Create a `.env` file in project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
```

## 📋 Security Best Practices

1. **Never commit sensitive data**
   - Add `.env` to `.gitignore`
   - Use environment variables for all secrets
   - Rotate credentials regularly

2. **Keep dependencies updated**
   ```bash
   pip install --upgrade pip
   pip list --outdated
   pip install --upgrade django
   ```

3. **Regular security audits**
   ```bash
   pip install safety
   safety check
   ```

4. **Monitor logs**
   - Check Django logs regularly
   - Set up error notifications
   - Monitor failed login attempts

5. **Database backups**
   - Automate daily backups
   - Test restore procedures
   - Store backups securely offsite

## 🐛 Reporting Security Issues

If you discover a security vulnerability, please email:
- **Email**: security@imfaktor.uz
- **Do NOT** create a public GitHub issue

We will respond within 48 hours and work with you to address the issue.

## 📚 Additional Resources

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Releases](https://www.djangoproject.com/weblog/)

---

**Last Updated**: November 2025
**Version**: 1.0
