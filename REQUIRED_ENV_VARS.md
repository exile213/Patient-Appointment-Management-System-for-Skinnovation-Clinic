# Environment Variables for Render Deployment

## 🚀 Quick Setup Guide for Render Free Tier

### Step 1: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: Your app name (e.g., `skinovation-beauty-clinic`)
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn beauty_clinic_django.wsgi:application`
   - **Plan**: `Free`

### Step 2: Create PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `skinovation-db` (or your preferred name)
   - **Database**: Auto-generated
   - **User**: Auto-generated
   - **Plan**: `Free` (1GB limit)
3. Click "Create Database"
4. **Important**: Copy the "Internal Database URL" from the database info page

### Step 3: Link Database to Web Service

1. Go back to your Web Service
2. Go to "Environment" tab
3. Add the database connection (see variables below)

---

## 📋 REQUIRED Environment Variables

Add these in **Render Dashboard → Your Web Service → Environment**:

### 🔴 CRITICAL (Must Have for Deployment)

```bash
# Django Core Settings
SECRET_KEY=<generate-using-command-below>
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com

# Database (Render PostgreSQL)
DATABASE_URL=<internal-database-url-from-render-postgresql>

# Cloudinary for Media Files (Free Tier: 10GB storage, 25 credits/month)
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
# Get this from: https://cloudinary.com/console (Sign up for free account)
```

### 🟡 GOOGLE OAUTH (Required if using Google Sign-In)

```bash
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-google-client-secret
```

**Important**: Add this redirect URI in [Google Cloud Console](https://console.cloud.google.com/):

- `https://your-app-name.onrender.com/accounts/google/login/callback/`

### 🟢 OPTIONAL Features (Can be omitted)

#### Email Configuration (Mailtrap SMTP)

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-mailtrap-username
EMAIL_HOST_PASSWORD=your-mailtrap-password
DEFAULT_FROM_EMAIL=Skinovation Beauty Clinic <noreply@skinovation.com>
MAILTRAP_API_TOKEN=your-mailtrap-api-token
```

#### SMS Configuration (SkySMS)

```bash
SMS_ENABLED=True
SKYSMS_API_KEY=your-skysms-api-key
SMS_SENDER_ID=BEAUTY
```

#### Cron Job Authentication (For Automated Reminders)

```bash
CRON_SECRET_TOKEN=your-random-50-character-token
# Generate using: python -c "import secrets; print(secrets.token_urlsafe(50))"
# This secures your cron endpoints from unauthorized access
```

**Note**: The app works perfectly without email/SMS. These are optional features for password reset and notifications. The CRON_SECRET_TOKEN is **required** if you plan to use automated appointment reminders via cron-job.org.

---

## 🔧 How to Generate Required Values

### Generate SECRET_KEY (Django Secret)

**Option 1 - Python Command:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Option 2 - Online Generator:**
Visit: https://djecrety.ir/

**Example Output:**

```
xK8_zQ9mL2nP5vR7wT1yU4oI6hJ3fG0bN8aS2dF5gH7jK9lM
```

### Generate CRON_SECRET_TOKEN (Cron Authentication)

**Use the same method as SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Example Output:**

```
aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6g
```

### Get DATABASE_URL (PostgreSQL Connection)

1. In Render Dashboard, go to your PostgreSQL database
2. Copy the **Internal Database URL** (starts with `postgresql://`)
3. Format: `postgresql://user:password@host:5432/database`

**Example:**

```
postgresql://skinovation_user:xYz123@dpg-abc123.oregon-postgres.render.com/skinovation_db
```

### Get CLOUDINARY_URL (Media File Storage)

1. Sign up at [Cloudinary](https://cloudinary.com/users/register/free) (Free account)
2. Go to [Dashboard](https://cloudinary.com/console)
3. Copy the **API Environment variable** (starts with `cloudinary://`)

**Example:**

```
cloudinary://123456789012345:AbcDeFgHiJkLmNoPqRsTuVwXyZ@your-cloud-name
```

**Free Tier Limits:**

- Storage: 10 GB
- Bandwidth: 25 credits/month (~25GB)
- Transformations: 25 credits/month

---

## 🎯 Render-Specific Configuration

### Build Script (`build.sh`)

Already created in your project root. This script:

- Installs dependencies from `requirements.txt`
- Collects static files
- Runs database migrations

### Procfile

Already created. Tells Render how to start your app with Gunicorn.

### Runtime

Python 3.11.9 specified in `runtime.txt`

---

## ⚙️ Render Free Tier Limitations

**Be aware of these free tier constraints:**

1. **Web Service**:

   - Spins down after 15 minutes of inactivity
   - First request after inactivity takes ~30-60 seconds (cold start)
   - 750 hours/month free (essentially always-on for one service)

2. **PostgreSQL Database**:

   - 1 GB storage limit
   - Expires after 90 days (you'll need to create a new one)
   - Shared resources (slower than paid tiers)

3. **Static Files**:

   - Served via WhiteNoise (no CDN on free tier)
   - Gzip compression enabled

4. **Media Files**:
   - Stored in Cloudinary (Render filesystem is ephemeral)
   - 10 GB storage on Cloudinary free tier

---

## 🚨 Security Checklist

Before deploying to production:

- [ ] `DEBUG=False` in environment variables
- [ ] Strong `SECRET_KEY` (50+ characters, randomly generated)
- [ ] Google OAuth credentials moved to environment variables (not hardcoded)
- [ ] `ALLOWED_HOSTS` includes your Render domain
- [ ] PostgreSQL `DATABASE_URL` from Render (internal URL for better performance)
- [ ] Cloudinary `CLOUDINARY_URL` configured for media uploads
- [ ] SSL/HTTPS automatically enabled by Render (no configuration needed)

---

## 📝 Local Development vs Production

**Local (Development):**

```bash
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
# Uses local SQLite or PostgreSQL
# Uses local media/ folder for uploads
```

**Render (Production):**

```bash
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=<render-postgresql-url>
CLOUDINARY_URL=<cloudinary-api-url>
```

---

## 🐛 Troubleshooting

### Issue: App won't start

- Check Render logs: Dashboard → Your Service → Logs
- Verify all CRITICAL environment variables are set
- Ensure `build.sh` has execute permissions (should be default)

### Issue: Static files not loading

- Check if `collectstatic` ran in build logs
- Verify `STATIC_ROOT` and `STATICFILES_STORAGE` in settings.py
- Clear browser cache

### Issue: Media uploads not working

- Verify `CLOUDINARY_URL` is set correctly
- Check Cloudinary dashboard for upload errors
- Ensure `DEBUG=False` (media storage only switches to Cloudinary in production)

### Issue: Database connection errors

- Use **Internal Database URL**, not External
- Verify PostgreSQL database is running (not paused/expired)
- Check database hasn't hit 1GB limit

### Issue: Google OAuth not working

- Add Render redirect URI in Google Cloud Console
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Check if credentials are valid (not expired/revoked)

---

## 📚 Additional Resources

- [Render Django Deployment Guide](https://render.com/docs/deploy-django)
- [Cloudinary Django Integration](https://cloudinary.com/documentation/django_integration)
- [Django Production Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

---

## 🔄 Deployment Workflow

1. **Push to GitHub**: `git push origin main`
2. **Render Auto-Deploys**: Watches your GitHub repo
3. **Build Process**: Runs `build.sh` automatically
4. **Health Check**: Render verifies app is running
5. **Live**: Your app is accessible at `https://your-app-name.onrender.com`

**First deployment may take 3-5 minutes. Subsequent deployments are faster.**

---

---

# 🔔 STEP 9: Setup Automated Appointment Reminders (After Deployment)

**⚠️ IMPORTANT: Complete this AFTER your app is deployed and running on Render.**

## Overview

Your app includes automated appointment reminder functionality that sends SMS to patients:

- **2 days before** appointment → Asks to confirm/reschedule/cancel via website
- **1 day before** appointment → Final reminder
- **1 hour before** appointment → Last-minute reminder

We'll use **cron-job.org** (free external cron service) to trigger these reminders automatically.

---

## Prerequisites Check

Before proceeding, verify:

- ✅ App is deployed and running on Render
- ✅ `SMS_ENABLED=True` in Render environment variables
- ✅ `SKYSMS_API_KEY` is configured
- ✅ You can access: `https://your-app-name.onrender.com`

---

## Step 9.1: Generate Cron Secret Token

**On your local machine**, generate a secure token:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Example output:**

```
aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6g
```

**💾 SAVE THIS TOKEN** - you'll need it in the next steps!

---

## Step 9.2: Add Token to Render

1. Go to **Render Dashboard** → Your Web Service
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add:
   ```
   Key: CRON_SECRET_TOKEN
   Value: <paste-your-generated-token-from-step-9.1>
   ```
5. Click **"Save Changes"**
6. Wait for automatic redeploy (~2 minutes)

---

## Step 9.3: Test Cron Endpoint (Verify It Works)

1. **Open browser** and visit:

   ```
   https://your-app-name.onrender.com/api/cron/health/
   ```

2. **You should see:**

   ```json
   {
     "status": "healthy",
     "service": "Skinovation Beauty Clinic Cron Service"
   }
   ```

3. **Test reminder endpoint** (replace YOUR_APP_NAME and YOUR_TOKEN):

   ```
   https://your-app-name.onrender.com/api/cron/reminders/?filter=1day&token=YOUR_CRON_SECRET_TOKEN
   ```

4. **Expected response:**
   ```json
   {
     "success": true,
     "filter": "1day",
     "message": "Reminder task executed successfully",
     "output": "..."
   }
   ```

**If you get errors**, check troubleshooting section at the bottom.

---

## Step 9.4: Create cron-job.org Account

1. Go to **https://cron-job.org/**
2. Click **"Sign Up for Free"**
3. Fill in:
   - Email address
   - Password
   - Accept terms
4. **Verify your email** (check inbox/spam)
5. **Login** to dashboard

---

## Step 9.5: Create Cron Job #1 - Reminder 2 Days Before

1. In cron-job.org dashboard, click **"Create cron job"** (green button)

2. **Fill in these settings:**

   **Title:**

   ```
   Skinovation - 2 Days Before Reminder
   ```

   **Address (URL):** ⚠️ Replace `your-app-name` and `YOUR_TOKEN`

   ```
   https://your-app-name.onrender.com/api/cron/reminders/?filter=2days&token=YOUR_CRON_SECRET_TOKEN
   ```

   **Schedule:**

   - Execute: **Every day**
   - At: **09:00** (9 AM - when reminders sent)
   - Timezone: **Asia/Manila** (or your timezone)

3. **Click "Advanced" to expand more options:**

   - Request Method: **GET**
   - Request Timeout: **300** seconds
   - ✅ Enable "Save responses" (for debugging)
   - ✅ Enable "Redirect success"

4. **Notifications (Optional but recommended):**

   - ✅ "Notify me on failure"
   - After: **1** failed execution

5. **Click "Create cron job"**

---

## Step 9.6: Create Cron Job #2 - Reminder 1 Day Before

1. Click **"Create cron job"** again

2. **Settings:**

   **Title:**

   ```
   Skinovation - 1 Day Before Reminder
   ```

   **Address (URL):**

   ```
   https://your-app-name.onrender.com/api/cron/reminders/?filter=1day&token=YOUR_CRON_SECRET_TOKEN
   ```

   **Schedule:**

   - Execute: **Every day**
   - At: **09:00**
   - Timezone: **Asia/Manila**

3. **Advanced:** Same as Cron Job #1

4. **Click "Create cron job"**

---

## Step 9.7: Create Cron Job #3 - Reminder 1 Hour Before

1. Click **"Create cron job"** again

2. **Settings:**

   **Title:**

   ```
   Skinovation - 1 Hour Before Reminder
   ```

   **Address (URL):**

   ```
   https://your-app-name.onrender.com/api/cron/reminders/?filter=1hour&token=YOUR_CRON_SECRET_TOKEN
   ```

   **Schedule:**

   - Execute: **Every hour** (or select specific hours like 8 AM - 6 PM for business hours)
   - Minutes: **00** (at the top of each hour)
   - Timezone: **Asia/Manila**

   💡 **Tip:** If appointments only during business hours (8 AM - 6 PM), select only hours: 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18

3. **Advanced:** Same settings

4. **Click "Create cron job"**

---

## Step 9.8: Test Your Cron Jobs

### Test in cron-job.org:

1. Find your cron job in the dashboard
2. Click the **"▶ Run now"** button (play icon)
3. Wait 30-60 seconds (Render free tier cold start)
4. Check **"Execution history"** tab:
   - ✅ **Green checkmark** = Success
   - ❌ **Red X** = Failed (click to see error)

### Check Execution Details:

1. Click on a successful execution
2. View **"Response"** tab:
   ```json
   {
     "success": true,
     "filter": "2days",
     "output": "Reminder Sending Completed - Filter: 2days\n  Total Processed: 5\n  ✓ Sent Successfully: 5"
   }
   ```

### Verify SMS Sent:

1. Check your phone or patient phones
2. Or check Render logs:
   - Render Dashboard → Your Service → **Logs**
   - Look for: `✓ Reminder sent to...`

---

## 📊 Monitoring Your Cron Jobs

### In cron-job.org Dashboard:

**For each cron job, you can see:**

- ✅ Last execution time
- ✅ Success/failure status
- ✅ Execution history (last 50 runs)
- ✅ Response time
- ✅ HTTP status code
- ✅ Response body

**Set up email notifications:**

- Get alerts when cron job fails
- Set threshold (e.g., notify after 2 consecutive failures)

### In Render Logs:

1. Go to Render Dashboard → Your Service → **"Logs"**
2. Look for entries like:
   ```
   ✓ Reminder sent to John Doe for 2026-01-08 at 14:00 (2 days before)
   Reminder Sending Completed - Filter: 2days
     Total Processed: 5
     ✓ Sent Successfully: 5
   ```

---

## 🐛 Troubleshooting Cron Jobs

### ❌ Error: 401 Unauthorized

**Problem:** Invalid token

**Solution:**

1. Check `CRON_SECRET_TOKEN` is set in Render environment
2. Verify token in URL matches exactly (no extra spaces)
3. Check token didn't get truncated when copying

---

### ❌ Error: 500 Internal Server Error

**Problem:** App crashed during execution

**Solution:**

1. Check Render logs for Python error traceback
2. Verify `SMS_ENABLED=True`
3. Verify `SKYSMS_API_KEY` is set
4. Test endpoint manually in browser first

---

### ✅ Success but "Sent: 0"

**Problem:** No appointments found for that time period

**Solution:**

- **This is NORMAL** if no appointments scheduled
- The response will say: `"✓ Sent Successfully: 0"`
- Create test appointments to verify it works
- Check appointments are in "confirmed" or "scheduled" status

---

### ⏱️ Error: Timeout / App Spun Down

**Problem:** Render free tier cold start

**Solution:**

1. **This is expected** on first cron call after 15 min inactivity
2. Increase timeout in cron-job.org to **300 seconds** (5 minutes)
3. App will respond eventually (30-60 sec cold start)
4. Subsequent cron calls will be fast

**Optional:** Keep app warm by adding a health check cron:

- URL: `https://your-app-name.onrender.com/api/cron/health/`
- Schedule: Every 10 minutes (no token needed)
- This prevents app from spinning down

---

### 🔐 Security: Token Visible in Logs?

**Question:** Is my token exposed in cron-job.org logs?

**Answer:**

- Execution logs are **private to your account only**
- Only you can see them (not public)
- For extra security, rotate token every 90 days

**Advanced (Optional):** Use Authorization header instead:

1. In cron-job.org, click "Advanced" when creating job
2. Add custom header: `Authorization: Bearer YOUR_TOKEN`
3. Change URL to: `https://your-app.onrender.com/api/cron/reminders/?filter=2days` (remove `&token=...`)

---

## 📅 What Each Cron Job Does

### Cron Job #1: 2 Days Before (Daily at 9 AM)

- Finds appointments scheduled for 2 days from now
- Sends SMS: _"You have an appointment on {date}. Please log into your account to confirm, reschedule, or cancel."_
- Patients can visit website to take action

### Cron Job #2: 1 Day Before (Daily at 9 AM)

- Finds appointments scheduled for tomorrow
- Sends SMS: _"Reminder: Your appointment is tomorrow at {time}. We look forward to seeing you!"_
- Final confirmation reminder

### Cron Job #3: 1 Hour Before (Every Hour)

- Finds appointments starting in ~1 hour
- Sends SMS: _"Your appointment starts in 1 hour ({time} today). Please arrive on time."_
- Last-minute reminder to prevent no-shows

---

## 💡 Tips & Best Practices

### Recommended Settings:

- **2-days reminder**: Daily at 9:00 AM
- **1-day reminder**: Daily at 9:00 AM
- **1-hour reminder**: Every hour during business hours (8 AM - 6 PM)

### Free Tier Limits:

- **cron-job.org**: 100 requests/day (plenty for most clinics)
- **Your usage**: ~3 requests/day + 10-16 requests/day (if hourly) = ~20/day
- **Well within free limits!**

### If You Need More:

- Upgrade to Sustaining Member: $30/year → 5,000 requests/day
- Or reduce 1-hour cron to only business hours to save requests

### Customize SMS Messages:

- Edit templates in Django admin or `services/sms_service.py`
- Include website link for confirm/reschedule actions
- Keep messages under 160 characters to avoid multi-part SMS charges

---

## ✅ Setup Complete Checklist

Verify all these are done:

- [ ] `CRON_SECRET_TOKEN` added to Render environment
- [ ] App redeployed with new token
- [ ] Health check endpoint works (returns "healthy")
- [ ] Reminder endpoint works (returns success)
- [ ] cron-job.org account created and verified
- [ ] 3 cron jobs created (2-days, 1-day, 1-hour)
- [ ] All cron jobs tested with "Run now" button
- [ ] Execution history shows green checkmarks
- [ ] SMS actually sent to test phone number
- [ ] Email notifications enabled for failures

---

## 🎉 You're All Set!

Your automated appointment reminder system is now live! Patients will automatically receive SMS reminders:

- **2 days before** their appointment
- **1 day before** their appointment
- **1 hour before** their appointment time

The system runs 24/7 automatically via cron-job.org (free forever).

**Next Steps:**

- Monitor first few executions to ensure everything works
- Adjust timing if needed (e.g., send at 8 AM instead of 9 AM)
- Review SMS delivery rates weekly
- Enjoy automated patient communication! 🚀
