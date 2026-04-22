# Bluehost Deployment Guide

This guide explains how to deploy the Business Management System to your Bluehost server at `westernitsolutions.com.au/Application`.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step-by-Step Deployment](#step-by-step-deployment)
3. [Post-Deployment Setup](#post-deployment-setup)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)

## Prerequisites

### What You Need
- SSH access to your Bluehost account
- cPanel access
- Your domain: `westernitsolutions.com.au`
- The path: `/public_html/Application/` (we'll create this)

### Verify Python Support
Bluehost supports Python via Passenger WSGI. Verify:

1. Login to cPanel
2. Look for "Setup Python App" or "Passenger" under Software section
3. Note the Python version available (we need 3.6+)

## Step-by-Step Deployment

### Step 1: Upload Files to Bluehost

1. **Via SSH** (Recommended):
```bash
# Connect to your Bluehost server
ssh username@westernitsolutions.com.au

# Navigate to public_html
cd public_html

# Create Application directory
mkdir -p Application
cd Application

# Clone or upload your application
# Option A: Clone from Git (if you have Git repo)
git clone your-repo-url .

# Option B: Upload via FTP/SFTP
# Use FileZilla or WinSCP to upload files to /public_html/Application/
```

### Step 2: Setup Python Environment

1. **SSH into server**:
```bash
ssh username@westernitsolutions.com.au
cd ~/public_html/Application
```

2. **Create virtual environment**:
```bash
# Check Python version available
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

3. **Create .env file**:
```bash
# Copy example
cp .env.example .env

# Edit with your production settings
nano .env
```

Change these values:
```
FLASK_ENV=production
SECRET_KEY=your-very-secure-random-key-here
DATABASE_URL=sqlite:///business_management.db
```

### Step 3: Configure Passenger via cPanel

1. **Login to cPanel**
2. **Find and click "Setup Python App"** (or "Passenger Python Web Application")
3. **Create new Python application**:
   - **Python version**: 3.9 or higher
   - **Application path**: `/home/username/public_html/Application`
   - **Application startup file**: `passenger_wsgi.py`
   - **Application entry point**: `app`

4. **Click "Setup"**

5. **Update .htaccess** (if exists, or create one):
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^ passenger_wsgi.py [QSA,L]
</IfModule>
```

### Step 4: Initialize Database

1. **SSH into your Bluehost account**:
```bash
ssh username@westernitsolutions.com.au
cd ~/public_html/Application

# Activate venv
source venv/bin/activate

# Initialize database
python3 << 'EOF'
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
print("Database initialized successfully!")
EOF
```

2. **Verify database was created**:
```bash
ls -la business_management.db
```

### Step 5: Set Permissions

```bash
cd ~/public_html/Application

# Set correct permissions
chmod -R 755 .
chmod -R 777 venv/lib/python*/site-packages
chmod 666 business_management.db  # Database file needs write access

# Make sure Passenger can write to database
chmod 777 .
```

### Step 6: Verify Setup

1. **Check Passenger is running**:
```bash
cd ~/public_html/Application
# Look for tmp/restart.txt
ls -la tmp/

# Restart Passenger by touching restart.txt
touch tmp/restart.txt
```

2. **Test your application**:
```
Visit: https://westernitsolutions.com.au/Application
Expected: "Welcome to Business Management System" message or dashboard
```

3. **Check error logs if issues**:
```bash
# Login via SSH and check error logs
tail -f ~/public_html/Application/tmp/error.log
tail -f ~/public_html/Application/tmp/production.log
```

## Post-Deployment Setup

### SSL Certificate

1. Bluehost typically includes free AutoSSL
2. Login to cPanel → AutoSSL
3. Ensure your domain is included
4. Your application is now at: `https://westernitsolutions.com.au/Application`

### Database Backup

1. **Automatic backup** (using cPanel):
   - Go to cPanel → Backup
   - Create automatic daily backups

2. **Manual backup**:
```bash
# Via SSH
cd ~/public_html/Application
cp business_management.db business_management.db.backup
```

### Performance Optimization

If using database frequently, consider:

1. **Upgrade to MySQL**:
   - Create MySQL database in cPanel
   - Update .env: `DATABASE_URL=mysql+pymysql://user:password@hostname/dbname`
   - Rerun database initialization

2. **Enable Caching**:
   - Consider adding Redis cache (if available on Bluehost)

### Monitoring

1. **Check disk space**:
```bash
df -h ~/public_html
```

2. **Monitor database size**:
```bash
du -h ~/public_html/Application/business_management.db
```

## Troubleshooting

### Issue: "502 Bad Gateway" or "500 Internal Server Error"

**Solution**:
1. SSH into server
2. Check error logs:
```bash
tail -f ~/public_html/Application/tmp/error.log
tail -f ~/public_html/Application/tmp/production.log
```

3. Common causes:
   - Missing dependencies: `pip install -r requirements.txt`
   - Wrong Python version: Check Passenger settings
   - Database permissions: `chmod 666 business_management.db`

### Issue: "Module not found" error

**Solution**:
```bash
# Ensure requirements are installed in venv
source venv/bin/activate
pip install -r requirements.txt

# Restart Passenger
touch tmp/restart.txt
```

### Issue: Database file permission error

**Solution**:
```bash
# Make database writable
chmod 666 business_management.db

# Make directory writable
chmod 755 .
```

### Issue: Application not accessible at domain

**Solution**:
1. Verify DNS is pointing to Bluehost
2. Check A records in Bluehost DNS settings
3. Check .htaccess configuration
4. Verify SSL certificate is valid

### Issue: Slow queries or timeouts

**Solution**:
1. Upgrade to MySQL database for better performance
2. Increase PHP/Python memory limits in .htaccess:
```apache
php_value memory_limit 256M
```

## Maintenance

### Regular Tasks

**Weekly**:
- Check application logs for errors
- Monitor disk usage

**Monthly**:
- Backup database
- Review reports for data integrity
- Check for software updates

### Updating Application

1. **SSH into server**:
```bash
ssh username@westernitsolutions.com.au
cd ~/public_html/Application
```

2. **Backup current version**:
```bash
cp -r . ../Application_backup_$(date +%Y%m%d)
```

3. **Update files**:
```bash
# Via Git (if repo)
git pull origin main

# Or upload new files via SFTP
```

4. **Install any new dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

5. **Restart Passenger**:
```bash
touch tmp/restart.txt
```

### Database Migrations

If you add new features:

1. **Create migration** (on local machine):
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

2. **Apply on Bluehost**:
```bash
ssh username@westernitsolutions.com.au
cd ~/public_html/Application
source venv/bin/activate
flask db upgrade
```

## Important Notes

### Why No Docker?

Docker is not needed (and not typical) on Bluehost shared hosting:
- Bluehost doesn't support Docker containers
- Passenger WSGI provides the application server
- SQLite database is simpler to manage
- Direct file system access is available

### Database Choice

**SQLite** (default):
- ✅ No external database setup needed
- ✅ Good for single-server deployments
- ✅ Easy backups (just copy file)
- ❌ Not ideal for high concurrency
- ❌ Not best for very large datasets

**MySQL**:
- ✅ Better for high traffic
- ✅ Better concurrency support
- ✅ Available on Bluehost
- ❌ Requires setup in cPanel
- ❌ Need to manage separately

## Support & Help

For Bluehost-specific support:
- Bluehost Help: https://www.bluehost.com/support
- Contact: Via cPanel support ticket

For application issues:
- Check error logs
- Review this guide's troubleshooting section

## Next Steps

After deployment, you should:

1. ✅ Verify application is online
2. ✅ Test creating a customer
3. ✅ Test creating a product
4. ✅ Test creating a quote/invoice
5. ✅ Test reports generation
6. ✅ Setup regular backups

Congratulations! Your Business Management System is now live!
