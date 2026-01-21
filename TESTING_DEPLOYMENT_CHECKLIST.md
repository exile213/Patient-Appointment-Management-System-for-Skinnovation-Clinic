# 🧪 System Updates Testing & Deployment Checklist

## Pre-Deployment Testing

### 1. Authentication System Testing ✅
- [ ] Patient can login with email and password
- [ ] Admin staff can login with email and password
- [ ] Owner can login with email and password
- [ ] Attendant can login with email and password
- [ ] Case-insensitive email matching works (test with CAPS emails)
- [ ] Invalid credentials show appropriate error message
- [ ] Inactive accounts are rejected with clear message
- [ ] Password reset still works
- [ ] Session management works correctly

**Testing URLs:**
- Patient: `/accounts/patient-login/`
- Admin: `/accounts/login/admin/`
- Owner: `/accounts/login/owner/`
- Attendant: `/accounts/login/attendant/`

---

### 2. Welcome Communications Testing ✅
- [ ] New patient registration triggers welcome email
- [ ] Welcome email arrives in patient inbox within 2 minutes
- [ ] Welcome email contains patient's first name
- [ ] Welcome email contains clinic introduction
- [ ] Welcome email contains getting started steps
- [ ] Welcome email contains support information
- [ ] Welcome SMS is sent after registration
- [ ] Welcome SMS has correct phone number
- [ ] Welcome SMS content is clear and actionable
- [ ] Email is not marked as spam (check spam folder)

**Test Registration:**
1. Go to `/accounts/register/`
2. Create test patient account
3. Check email inbox and SMS

**Check Email Headers:**
- From: noreply@skinovation.com
- Category: Welcome
- Subject: "Welcome to Skinnovation Beauty Clinic!"

---

### 3. Appointment Email Notifications Testing ✅
- [ ] Confirmation email sent when appointment confirmed
- [ ] Confirmation email shows correct appointment details
- [ ] Confirmation email shows attendant name
- [ ] Confirmation email has arrival instructions
- [ ] Confirmation email has cancellation policy
- [ ] Email and SMS delivery status shown in admin interface
- [ ] Reminder emails can be sent (manual test)
- [ ] Cancellation emails work (manual test)
- [ ] Rescheduled emails work (manual test)
- [ ] Reassignment emails work (manual test)

**Test Appointment Flow:**
1. Create new appointment
2. Confirm appointment
3. Check patient email inbox
4. Verify SMS sent
5. Check admin dashboard for notification status

**Email Categories to Check:**
- Appointment-Confirmation
- Appointment-Reminder
- Appointment-Cancellation
- Appointment-Rescheduled
- Appointment-Reassignment

---

### 4. Data Sorting Testing ✅
- [ ] Services page shows newest services first
- [ ] Services older than 1 week are below newer ones
- [ ] Packages page shows newest packages first
- [ ] Products page shows newest products first
- [ ] Pagination works correctly with DESC sorting
- [ ] Sorting persists when filtering
- [ ] Admin can see sorting order changes

**Test Pages:**
- Go to `/owner/manage/services/`
- Go to `/owner/manage/packages/`
- Go to `/owner/manage/products/`

**Verify Sorting:**
- Add new item
- Check that it appears at top of list
- Refresh page - still at top
- Compare with items added weeks ago (should be lower)

---

### 5. Package Management - Select All Testing ✅
- [ ] "Select All Services" checkbox is visible
- [ ] Clicking checkbox adds all services to form
- [ ] Unchecking checkbox resets to single selector
- [ ] Remove button only shows when multiple services
- [ ] Can manually remove services
- [ ] Save button creates package with all selected services
- [ ] Database correctly stores service relationships
- [ ] Edit form shows all selected services
- [ ] Updating services works correctly
- [ ] No duplicate services in same package

**Test Select All:**
1. Go to `/owner/manage/packages/`
2. Scroll to "Add New Package" form
3. Check "Select All Services" checkbox
4. All services should appear in list
5. Try clicking "Save Package"
6. Verify package created with all services

**Test Uncheck:**
1. Check "Select All" checkbox
2. Uncheck it
3. Should reset to single empty selector
4. Manually select one service
5. Click Save

**Test Edit:**
1. Edit existing package
2. Verify all services show correctly
3. Add/remove services
4. Click "Save Changes"
5. Verify update persisted

---

### 6. Responsive Design Testing ✅
- [ ] Login forms work on mobile (375px width)
- [ ] Login forms work on tablet (768px width)
- [ ] Login forms work on desktop (1920px width)
- [ ] Email templates render correctly on mobile
- [ ] Email templates render correctly on tablet
- [ ] Email templates render correctly on desktop
- [ ] Package management form works on mobile
- [ ] Data tables are readable on mobile
- [ ] Buttons are touch-friendly (min 44px)
- [ ] No horizontal scrolling needed

**Test Tools:**
- Chrome DevTools - Device Emulation
- Firefox Developer Tools - Responsive Mode
- Test Email Templates: https://www.emailonacid.com/

---

## Environment Configuration Checklist

### Email Configuration
- [ ] MAILTRAP_API_TOKEN is set in .env
- [ ] Mailtrap account has available email sends
- [ ] Sender email is configured correctly
- [ ] Email templates use correct clinic branding
- [ ] Reply-to address is configured (if needed)

### SMS Configuration
- [ ] SKYSMS_API_KEY is set in .env
- [ ] SkySMS account has SMS balance
- [ ] Phone number formatting is correct (+63 format)
- [ ] SMS sender ID is configured

### Django Configuration
- [ ] DEBUG = False in production
- [ ] ALLOWED_HOSTS includes production domain
- [ ] SECRET_KEY is unique and strong
- [ ] CSRF protection is enabled
- [ ] SECURE_SSL_REDIRECT = True in production
- [ ] SESSION_COOKIE_SECURE = True in production

---

## Security Checklist

### Authentication Security
- [ ] Passwords are hashed (never plain text)
- [ ] Email lookups are case-insensitive (prevents bypass)
- [ ] Inactive accounts are rejected
- [ ] Failed login attempts don't reveal if email exists
- [ ] Password reset token expires
- [ ] CSRF tokens on all forms
- [ ] XSS protection enabled

### Email Security
- [ ] Emails sent over secure connection (TLS/SSL)
- [ ] No sensitive data in email subject lines
- [ ] Patient data is not logged in plain text
- [ ] Email templates don't contain hardcoded secrets
- [ ] Unsubscribe/preference links (if applicable)

### SMS Security
- [ ] Phone numbers stored securely
- [ ] SMS content doesn't include sensitive data
- [ ] API keys not exposed in logs
- [ ] Phone number validation prevents injection

---

## Performance Testing

### Email Delivery
- [ ] Welcome email sends within 5 seconds of registration
- [ ] Appointment confirmation within 10 seconds
- [ ] Email queue doesn't slow down user interface
- [ ] Large batch emails don't timeout

### Database
- [ ] Sorting queries are optimized (use indexes)
- [ ] Pagination works with large datasets (1000+ items)
- [ ] Notification creation doesn't cause timeouts
- [ ] Service selection doesn't slow down form

### API Calls
- [ ] Mailtrap API calls timeout after 30 seconds
- [ ] SkySMS API calls timeout after 30 seconds
- [ ] Failed API calls don't crash application
- [ ] Error messages are logged for debugging

---

## Browser Compatibility Checklist

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Browsers
- [ ] Chrome Mobile
- [ ] Safari iOS
- [ ] Firefox Mobile
- [ ] Samsung Internet

### Features to Test in Each:
- Login form submission
- Email template rendering
- Form interactions (checkboxes, dropdowns)
- Navigation and links

---

## Production Deployment Steps

### 1. Pre-Deployment
- [ ] All tests pass
- [ ] Code review completed
- [ ] Database migrations tested on staging
- [ ] Backup created
- [ ] Rollback plan documented

### 2. Database Migration
```bash
python manage.py migrate
```
- [ ] No migration errors
- [ ] Data integrity verified
- [ ] Backup available for rollback

### 3. Static Files
```bash
python manage.py collectstatic --noinput
```
- [ ] CSS loads correctly
- [ ] JavaScript functions work
- [ ] Images display properly

### 4. Service Start
```bash
# Using Gunicorn
gunicorn beauty_clinic_django.wsgi:application --bind 0.0.0.0:8000
```
- [ ] Application starts without errors
- [ ] Port is listening
- [ ] Logs show no errors

### 5. Post-Deployment
- [ ] Email delivery verified
- [ ] SMS delivery verified
- [ ] Login functionality verified
- [ ] User experience tested
- [ ] Monitor logs for errors

---

## Troubleshooting Guide

### Email Not Sending
**Symptoms:** Users report no welcome email
**Solution Checklist:**
- [ ] Verify MAILTRAP_API_TOKEN in settings
- [ ] Check Mailtrap account has balance
- [ ] Verify patient email address is valid
- [ ] Check Django logs for errors
- [ ] Verify email service is instantiated
- [ ] Test with manual email send: `python manage.py shell`

### SMS Not Sending
**Symptoms:** Users report no welcome SMS
**Solution Checklist:**
- [ ] Verify SKYSMS_API_KEY is set
- [ ] Check phone number format (09xxxxx or +63xxxxx)
- [ ] Verify account has SMS balance
- [ ] Check message length (max 160 chars)
- [ ] Review API response in logs

### Login Not Working
**Symptoms:** Users can't login with email
**Solution Checklist:**
- [ ] Verify user email exists in database
- [ ] Check user account is active (archived=False)
- [ ] Verify password is correct (case-sensitive)
- [ ] Check for database connection issues
- [ ] Review auth backend configuration

### Select All Not Working
**Symptoms:** Checkbox doesn't select all services
**Solution Checklist:**
- [ ] Check browser console for JavaScript errors
- [ ] Verify `all_services` context variable exists
- [ ] Check element IDs match JavaScript selectors
- [ ] Verify service select dropdowns have name="service_ids"
- [ ] Clear browser cache and try again

---

## Monitoring & Logging

### Logs to Monitor
- `/var/log/django/email.log` - Email delivery logs
- `/var/log/django/sms.log` - SMS delivery logs
- `/var/log/django/auth.log` - Authentication logs
- `/var/log/django/error.log` - Error logs
- Django console output - Real-time issues

### Metrics to Track
- Email delivery rate (target: >95%)
- SMS delivery rate (target: >95%)
- Failed login attempts (investigate spikes)
- Email service response time (target: <2s)
- Database query times (target: <100ms)

### Alerts to Set Up
- Email delivery failure rate > 5%
- SMS delivery failure rate > 5%
- Database connection errors
- Memory usage > 80%
- Disk usage > 90%

---

## Success Criteria

Your deployment is successful when:

✅ All system updates are functioning
✅ Emails deliver to patient inboxes within 2 minutes
✅ SMS delivery rate is above 95%
✅ Login works with email for all user roles
✅ Welcome communications sent automatically
✅ Appointment notifications delivered
✅ Data sorting works correctly
✅ Package Select All feature functional
✅ No errors in application logs
✅ Users report positive experience

---

## Sign-Off

**Tester Name:** ___________________
**Date:** ___________________
**Status:** ✅ Ready for Production / ❌ Issues Found

**Issues Found (if any):**
```
1. 
2. 
3. 
```

**Sign-Off:** ___________________

---

**Document Version:** 1.0
**Last Updated:** January 21, 2026
**Status:** Ready for Testing
