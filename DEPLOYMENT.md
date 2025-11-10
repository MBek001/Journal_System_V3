# Deployment Guide - Imfaktor Journal System

## 📋 Prerequisites

- Python 3.9 or higher
- pip and virtualenv
- PostgreSQL or MySQL (recommended for production)
- HTTPS certificate (Let's Encrypt recommended)
- Domain name configured

## 🚀 Production Deployment Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/Journal_System_V3.git
cd Journal_System_V3
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Environment File

Create `.env` file in project root (see `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```env
# CRITICAL: Generate new secret key
SECRET_KEY=your-production-secret-key-here

# Production settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/journal_db

# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Admin credentials (TEMPORARY - migrate to Django User model)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-random-password
```

### 5. Generate Secret Key

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output to `.env` as `SECRET_KEY`.

### 6. Configure Database (Production)

For PostgreSQL:

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Create database
sudo -u postgres psql
CREATE DATABASE journal_db;
CREATE USER journal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE journal_db TO journal_user;
\q
```

Update `settings.py` for PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'journal_db',
        'USER': 'journal_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create Superuser

```bash
python manage.py createsuperuser
```

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 10. Set Up Web Server (Gunicorn + Nginx)

#### Install Gunicorn

```bash
pip install gunicorn
```

#### Create Gunicorn service

Create `/etc/systemd/system/journal.service`:

```ini
[Unit]
Description=Imfaktor Journal System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/Journal_System_V3
Environment="PATH=/path/to/Journal_System_V3/venv/bin"
ExecStart=/path/to/Journal_System_V3/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    JournalSystem.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Start Gunicorn

```bash
sudo systemctl start journal
sudo systemctl enable journal
```

#### Configure Nginx

Create `/etc/nginx/sites-available/journal`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /path/to/Journal_System_V3/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/Journal_System_V3/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/journal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 11. Set Up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 12. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 🔐 Post-Deployment Security

1. **Verify environment variables are set**:
   ```bash
   python manage.py check --deploy
   ```

2. **Test security headers**:
   ```bash
   curl -I https://yourdomain.com
   ```

3. **Set up monitoring**:
   - Configure error email notifications
   - Set up uptime monitoring
   - Configure log rotation

4. **Regular maintenance**:
   - Update dependencies monthly
   - Review access logs weekly
   - Backup database daily

## 🔄 Updating the Application

```bash
cd /path/to/Journal_System_V3
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart journal
```

## 📊 Monitoring and Logs

View application logs:
```bash
sudo journalctl -u journal -f
```

View Nginx logs:
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🗄️ Database Backup

Automated backup script:

```bash
#!/bin/bash
# /home/user/backup-journal-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/journal"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump journal_db > $BACKUP_DIR/journal_db_$DATE.sql

# SQLite backup (if using SQLite)
# cp /path/to/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Keep only last 7 days
find $BACKUP_DIR -name "journal_db_*.sql" -mtime +7 -delete

# Upload to remote storage (optional)
# aws s3 cp $BACKUP_DIR/journal_db_$DATE.sql s3://your-bucket/backups/
```

Add to crontab:
```bash
0 2 * * * /home/user/backup-journal-db.sh
```

## 🐛 Troubleshooting

### 502 Bad Gateway
- Check Gunicorn is running: `sudo systemctl status journal`
- Check socket file exists: `ls -la /run/gunicorn.sock`
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Static files not loading
- Run collectstatic: `python manage.py collectstatic`
- Check Nginx static file path in config
- Verify file permissions: `sudo chown -R www-data:www-data /path/to/staticfiles`

### Database connection errors
- Check DATABASE_URL in `.env`
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Test connection: `psql -U journal_user -d journal_db -h localhost`

## 📞 Support

For deployment assistance, contact:
- **Email**: support@imfaktor.uz
- **Documentation**: https://docs.imfaktor.uz

---

**Last Updated**: November 2025
