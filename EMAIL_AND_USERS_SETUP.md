# 🔧 Email Notifications & Admin/Owner User Setup Guide

## ✅ What Has Been Fixed

### 1. **Email Notifications on Patient Registration** 
✓ Enhanced email service with better error logging
✓ Email welcome message integrated with registration flow
✓ Proper exception handling to diagnose delivery issues

### 2. **Admin & Owner User Seeding**
✓ Created new management command: `seed_admin_owner.py`
✓ Created simple Python script: `seed_users_simple.py` (no Django management required)

### 3. **Configuration Improvements**
✓ Added default values for Google OAuth credentials (allows app to start without OAuth setup)
✓ Made SMS service optional (gracefully handles missing API key)
✓ Enhanced error messages for debugging

---

## 📧 Email Notifications Setup

### Step 1: Configure Mailtrap Account

1. Go to [https://mailtrap.io](https://mailtrap.io)
2. Create a free account or log in
3. Navigate to **Email Sending → API Tokens**
4. Copy your **API Token**

### Step 2: Add Mailtrap Token to .env

Open your `.env` file and add:

```env
MAILTRAP_API_TOKEN=your_api_token_here
```

Replace `your_api_token_here` with the token you copied.

### Step 3: Verify Email Configuration

Test the email service:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from accounts.email_service import MailtrapEmailService
from accounts.models import User

# Get a test user
user = User.objects.filter(user_type='patient').first()

# Send test email
if user:
    service = MailtrapEmailService()
    result = service.send_welcome_email(user)
    print(result)
else:
    print("No patient found. Create a patient first.")
```

**Expected output:**
```
{'success': True, 'response': {...}, 'message': 'Welcome email sent successfully!'}
```

---

## 👤 Create Admin & Owner Users

### Option A: Using Simple Python Script (Recommended)

This method doesn't require correct database credentials if you're just setting up.

```bash
python seed_users_simple.py
```

**Output:**
```
============================================================
SKINNOVATION BEAUTY CLINIC - USER SEEDING
============================================================

✓ Owner user created successfully
✓ Admin user created successfully

============================================================
LOGIN CREDENTIALS
============================================================

Owner Account:
  Email:    owner@skinovation.com
  Password: owner@123456
  Login:    http://localhost:8000/accounts/login/owner/

Admin Account:
  Email:    admin@skinovation.com
  Password: admin@123456
  Login:    http://localhost:8000/accounts/login/admin/

============================================================

✓ User seeding completed successfully!
```

### Option B: Using Django Management Command

First, ensure your database credentials are correct in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'beauty_clinic_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password_here',  # ← Update this
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Then run:

```bash
python manage.py seed_admin_owner
```

---

## 🔐 Default Credentials

After running the seed script, use these credentials to log in:

### Owner Login
- **Email:** `owner@skinovation.com`
- **Password:** `owner@123456`
- **Login URL:** `http://localhost:8000/accounts/login/owner/`

### Admin/Staff Login
- **Email:** `admin@skinovation.com`
- **Password:** `admin@123456`
- **Login URL:** `http://localhost:8000/accounts/login/admin/`

---

## ✉️ Email Sending Flow

When a patient registers:

```
Patient Registration
    ↓
Form Validation
    ↓
User Created in Database
    ↓
Send Welcome Email
    ├─ API Call to Mailtrap
    ├─ Log Success/Failure
    └─ Continue regardless
    ↓
Send Welcome SMS (if phone available)
    ├─ API Call to SkySMS
    ├─ Log Success/Failure
    └─ Continue regardless
    ↓
User Logged In Automatically
```

---

## 🧪 Testing Email Notifications

### Test 1: Direct Registration Email

1. Go to registration page: `http://localhost:8000/accounts/register/`
2. Register with a valid Gmail address
3. Check both email and console for:
   - `[EMAIL] Attempting to send welcome email to user@gmail.com`
   - `[EMAIL] Welcome Email Response: ...`

### Test 2: Manual Email Send

```python
python manage.py shell

from accounts.models import User
from accounts.email_service import MailtrapEmailService

service = MailtrapEmailService()

# Send to specific user
user = User.objects.get(email='test@example.com')
result = service.send_welcome_email(user)
print(f"Email sent: {result['success']}")
print(f"Message: {result['message']}")
```

### Test 3: Check Mailtrap Account

1. Log in to [https://mailtrap.io](https://mailtrap.io)
2. Go to **Email Sending → Inbox**
3. You should see emails there when they're sent
4. Click on an email to verify it was received

---

## 🐛 Troubleshooting

### Issue: "MAILTRAP_API_TOKEN is not configured"

**Solution:**
1. Check your `.env` file has the token:
   ```env
   MAILTRAP_API_TOKEN=your_actual_token_here
   ```
2. Restart your server after adding to .env
3. Verify token is valid on mailtrap.io

### Issue: "Email not sending but no error"

**Check logs:**
1. Look at console output when registering
2. Search for `[EMAIL]` prefix messages
3. Check Mailtrap inbox at mailtrap.io

### Issue: "Connection to database failed"

**Solution:**
Option A (Recommended): Just use the simple script
```bash
python seed_users_simple.py
```

Option B: Fix database credentials
1. Open `beauty_clinic_django/settings.py`
2. Update the DATABASES section with correct credentials:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'beauty_clinic_db',
           'USER': 'postgres',
           'PASSWORD': 'correct_password',  # ← Fix this
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### Issue: "SMS not sending"

**Check:**
1. Ensure `SKYSMS_API_KEY` is set in `.env` (optional, but required to send SMS)
2. Verify phone format: `09123456789` or `+639123456789`
3. Check SkySMS account has credits

---

## 📋 Environment Variables Checklist

Ensure your `.env` file has:

```env
# Database (required)
DATABASE_URL=postgresql://postgres:password@localhost:5432/beauty_clinic_db

# Email (required for patient notifications)
MAILTRAP_API_TOKEN=your_mailtrap_token_here

# SMS (optional, but recommended)
SKYSMS_API_KEY=your_skysms_api_key

# Django (required)
SECRET_KEY=your_secret_key
DEBUG=True
```

---

## ✅ Success Checklist

After setup, verify:

- [ ] Owner user created and can log in with `owner@skinovation.com`
- [ ] Admin user created and can log in with `admin@skinovation.com`
- [ ] Patient registration sends welcome email
- [ ] Patient can see email in Mailtrap inbox (mailtrap.io)
- [ ] Console shows `[EMAIL] Welcome Email Response` messages
- [ ] All error logs show "success": True

---

## 📞 Quick Commands Reference

```bash
# Test email service
python manage.py shell < test_email.py

# Send test email to specific address
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()
from accounts.email_service import MailtrapEmailService
s = MailtrapEmailService()
result = s.send_test_email('your_email@gmail.com', 'Test User')
print(result)
"

# Check database connection
python manage.py dbshell

# View logs
tail -f /var/log/django/email.log
```

---

**Last Updated:** January 21, 2026
**Status:** Ready for Testing ✅
