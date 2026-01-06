# Login Credentials & Access Guide

This document contains all the test user credentials and how to access each interface in the application.

## Available Test Users

### Patient Interface
**URL:** `/login/patient/` or `/accounts/login/patient/`

**Test Users:**
- **Username:** `maria.santos`
- **Password:** `TestPass123!`
- **User Type:** Patient
- **Access:** Patient dashboard, profile, appointments, medical history

---

### Admin/Staff Interface
**URL:** `/login/admin/` or `/accounts/login/admin/`

**Test Users:**
1. **Username:** `admin.staff`
   - **Password:** `AdminPass123!`
   - **User Type:** Admin (Staff)
   - **Access:** Full admin dashboard with all features

2. **Username:** `admin`
   - **Password:** `admin123`
   - **User Type:** Admin (Superuser)
   - **Access:** Full admin dashboard + Django admin panel

---

### Owner Interface
**URL:** `/login/owner/` or `/accounts/login/owner/`

**Test Users:**
1. **Username:** `clinic.owner`
   - **Password:** `OwnerPass123!`
   - **User Type:** Owner
   - **Access:** Owner dashboard and management features

2. **Username:** `owner`
   - **Password:** `owner123`
   - **User Type:** Owner
   - **Access:** Owner dashboard and management features

---

### Attendant Interface
**URL:** `/login/attendant/` or `/accounts/login/attendant/`

**Test Users:**
1. **Username:** `attendant.01`
   - **Password:** `AttendPass123!`
   - **User Type:** Attendant
   - **Access:** Attendant dashboard and appointment management

2. **Username:** `attendant`
   - **Password:** `attendant123`
   - **User Type:** Attendant
   - **Access:** Attendant dashboard and appointment management

---

## Quick Access Summary

| Interface | Login URL | Username | Password |
|-----------|-----------|----------|----------|
| **Patient** | `/login/patient/` | `maria.santos` | `TestPass123!` |
| **Admin/Staff** | `/login/admin/` | `admin.staff` | `AdminPass123!` |
| **Owner** | `/login/owner/` | `clinic.owner` | `OwnerPass123!` |
| **Attendant** | `/login/attendant/` | `attendant.01` | `AttendPass123!` |

---

## Creating New Users

If you need to create more users, you can use these Django management commands:

### Create All Test Users
```bash
python manage.py create_test_users
```

### Create Admin Superuser
```bash
python manage.py create_superuser
```

### Create Owner & Attendant
```bash
python manage.py create_owner_attendant
```

### Create Custom User via Django Shell
```bash
python manage.py shell
```

Then in the shell:
```python
from accounts.models import User

# Create a patient
user = User.objects.create_user(
    username='newpatient',
    password='password123',
    user_type='patient',
    first_name='John',
    last_name='Doe',
    email='john@example.com'
)

# Create an admin
admin = User.objects.create_user(
    username='newadmin',
    password='password123',
    user_type='admin',
    first_name='Admin',
    last_name='User',
    email='admin@example.com',
    is_staff=True,
    is_superuser=True
)
```

---

## Login Selection Page

For staff, owner, and attendant users, there's also a login selection page:
**URL:** `/login/` or `/accounts/`

This page allows you to choose which interface to log into.

---

## Django Admin Panel

Superusers can also access the Django admin panel:
**URL:** `/admin/`

**Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

---

## Notes

- All test users are active and ready to use
- Passwords are case-sensitive
- If a user already exists, running the creation commands will update the password
- Patient users can only access patient interfaces
- Staff/Admin/Owner/Attendant users have access to their respective admin panels

