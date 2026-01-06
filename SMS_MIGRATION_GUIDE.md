# SMS System Migration: IPROG → SkySMS

## Migration Summary

Successfully migrated the Django SMS system from IPROG to SkySMS with transactional messaging support.

## Changes Made

### 1. **services/sms_service.py**

- ✅ Renamed class: `IPROGSMSService` → `SkySMSService`
- ✅ Updated API endpoint: `https://sms.iprogtech.com/api/v1/sms_messages` → `https://skysms.skyio.site/api/v1/sms/send`
- ✅ Changed authentication: `Authorization: Bearer` → `X-API-Key` header
- ✅ Updated payload format:
  - Removed: `api_token`, `sender_id`, `template_header`
  - Added: `use_subscription: false`
  - Format: `{"phone_number": "+639xxxxxxxxx", "message": "...", "use_subscription": false}`
- ✅ Updated phone formatter: Now outputs `+639xxxxxxxxx` format (with + prefix) instead of `639xxxxxxxxx`
- ✅ Added 160-character truncation in `send_sms()` method
- ✅ Updated global instance: `sms_service = SkySMSService()`

### 2. **services/template_service.py**

- ✅ Added 160-character truncation to `render_template()` method
- ✅ Added 160-character truncation to `render_text()` method
- ✅ Added warning logs when messages are truncated
- ✅ Kept `[token]` replacement logic unchanged
- ✅ Removed IPROG-specific comments and documentation references
- ✅ Made all messaging transactional (no dashboard template dependency)

### 3. **beauty_clinic_django/settings.py**

- ✅ Replaced: `IPROG_SMS_API_KEY` → `SKYSMS_API_KEY`
- ✅ Updated config reference: `config('SKYSMS_API_KEY', default='')`

### 4. **REQUIRED_ENV_VARS.md**

- ✅ Updated documentation to reference `SKYSMS_API_KEY` instead of `IPROG_SMS_API_KEY`

## Environment Variable Update Required

### ⚠️ IMPORTANT: Update Your .env File

You need to update your `.env` file with the new API key:

1. **Rename the variable:**

   ```env
   # OLD (remove this):
   IPROG_SMS_API_KEY=43e61b75f8972bcf1ce0ee541a38d593fa6e4f61

   # NEW (add this):
   SKYSMS_API_KEY=your_skysms_api_key_here
   ```

2. **Keep these unchanged:**
   ```env
   SMS_ENABLED=True
   SMS_SENDER_ID=BEAUTY  # Not used by SkySMS but kept for compatibility
   ```

### For Production (Render.com)

Update environment variables in Render Dashboard:

1. Remove: `IPROG_SMS_API_KEY`
2. Add: `SKYSMS_API_KEY=your_skysms_api_key_here`

## Technical Specifications

### SkySMS API Details

- **Endpoint:** POST `https://skysms.skyio.site/api/v1/sms/send`
- **Authentication:** `X-API-Key` header
- **Phone Format:** `+639xxxxxxxxx` (with + prefix)
- **Character Limit:** 160 characters (auto-truncated)
- **Payload:**
  ```json
  {
    "phone_number": "+639123456789",
    "message": "Your message here (max 160 chars)",
    "use_subscription": false
  }
  ```

### Phone Number Formatting

The system accepts and converts these formats to `+639xxxxxxxxx`:

- `09123456789` → `+639123456789`
- `9123456789` → `+639123456789`
- `639123456789` → `+639123456789`
- `+639123456789` → `+639123456789` (unchanged)

### Message Truncation

- All messages are automatically truncated to 160 characters
- Warning logs are generated when truncation occurs
- Truncation happens in both:
  - `sms_service.send_sms()` - before sending to API
  - `template_service.render_template()` - when rendering templates
  - `template_service.render_text()` - when rendering text

## Testing Checklist

After updating your environment variables, test the following:

### 1. Basic SMS Sending

- [ ] Test via Owner SMS interface (`owner/sms_views.py`)
- [ ] Test via Admin SMS interface (`appointments/admin_sms_views.py`)

### 2. Appointment Workflows

- [ ] Book new appointment → SMS sent
- [ ] Confirm appointment → SMS sent
- [ ] Cancel appointment → SMS sent
- [ ] Reschedule appointment → SMS sent
- [ ] Reassign attendant → SMS sent to patient & attendant

### 3. Package Workflows

- [ ] Book package → SMS sent

### 4. Edge Cases

- [ ] Long message (>160 chars) → truncated properly
- [ ] Various phone formats → formatted correctly
- [ ] Missing/invalid phone → error handled

### 5. Scheduled Tasks

- [ ] Daily appointment reminders cron job

## Migration Benefits

1. **Transactional Messaging:** Send any message directly without pre-registering in dashboard
2. **Simplified API:** Cleaner payload structure with fewer fields
3. **Character Limit Enforcement:** Automatic 160-character truncation prevents API errors
4. **Better Phone Format:** International format (`+63`) is more standard
5. **No Template Dashboard Dependency:** Full control over message content in code

## Rollback Instructions

If you need to rollback to IPROG:

1. Restore `services/sms_service.py` from git history
2. Restore `services/template_service.py` from git history
3. Restore `beauty_clinic_django/settings.py` SMS section
4. Update `.env` to use `IPROG_SMS_API_KEY`
5. Restart the application

## Support

If issues arise:

1. Check debug logs in console/terminal
2. Verify API key is correct in `.env`
3. Test phone number formatting
4. Ensure messages are under 160 characters
5. Review SkySMS API documentation: https://skysms.skyio.site/

---

**Migration Completed:** January 4, 2026  
**Migration Status:** ✅ Ready for Testing
