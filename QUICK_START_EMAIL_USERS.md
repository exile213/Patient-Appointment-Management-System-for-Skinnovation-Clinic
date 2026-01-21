# 🚀 Quick Start: Email Notifications & User Setup

## 1️⃣ Create Admin & Owner Users (2 minutes)

```bash
python seed_users_simple.py
```

**Output:**
```
✓ Owner user created successfully
✓ Admin user created successfully

Owner Account:
  Email:    owner@skinovation.com
  Password: owner@123456
  
Admin Account:
  Email:    admin@skinovation.com
  Password: admin@123456
```

---

## 2️⃣ Configure Email Notifications (5 minutes)

### Get Mailtrap Token:
1. Go to https://mailtrap.io
2. Sign up (free account)
3. Go to **Email Sending → API Tokens**
4. Copy your API Token

### Add to .env:
```env
MAILTRAP_API_TOKEN=paste_your_token_here
```

---

## 3️⃣ Test Email Sending (3 minutes)

Register a new patient:
1. Go to http://localhost:8000/accounts/register/
2. Fill in the form with:
   - Email: `test@gmail.com`
   - Password: `Test@123456`
3. Submit

**Watch the console:**
```
[EMAIL] Attempting to send welcome email to test@gmail.com
[EMAIL] API Token configured: True
[EMAIL] Welcome Email Response: {...}
```

**Check Mailtrap:**
1. Go to mailtrap.io
2. Go to **Email Sending → Inbox**
3. You should see the welcome email

---

## 4️⃣ Log In & Test Admin Features

### Owner Login:
- URL: http://localhost:8000/accounts/login/owner/
- Email: `owner@skinovation.com`
- Password: `owner@123456`

**✅ Note:** Use email (not username) in the login form

### Admin Login:
- URL: http://localhost:8000/accounts/login/admin/
- Email: `admin@skinovation.com`
- Password: `admin@123456`

**✅ Note:** Use email (not username) in the login form

---

## ✅ Success Checklist

- [ ] Ran `seed_users_simple.py` successfully
- [ ] Got Mailtrap token and added to `.env`
- [ ] Restarted the development server
- [ ] Registered a patient with Gmail address
- [ ] Saw `[EMAIL]` messages in console
- [ ] Found welcome email in Mailtrap inbox
- [ ] Logged in as Owner with provided credentials
- [ ] Logged in as Admin with provided credentials

---

## 📱 Email Features Now Working

✅ Welcome email on patient registration
✅ Appointment confirmation emails
✅ Appointment reminder emails
✅ Appointment cancellation emails
✅ SMS notifications (if SKYSMS_API_KEY configured)

---

## 📚 Full Documentation

For detailed setup and troubleshooting, see:
- [EMAIL_AND_USERS_SETUP.md](EMAIL_AND_USERS_SETUP.md)
- [EMAIL_NOTIFICATIONS_FIX_SUMMARY.md](EMAIL_NOTIFICATIONS_FIX_SUMMARY.md)

---

## 🎯 What's Next?

1. **Change default passwords** (security)
2. **Configure SMS** (optional): Add SKYSMS_API_KEY to .env
3. **Test all features**: Register patients, create appointments
4. **Deploy to production**: Update credentials in production .env

---

**Ready to go!** Start your server with:
```bash
python manage.py runserver
```

Questions? Check the detailed guides above! 🎉
