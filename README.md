# Skinovation Beauty Clinic - Django Version

This is a Django conversion of the original PHP beauty clinic management system. The application provides a comprehensive platform for managing beauty clinic operations including appointments, services, packages, products, and user management.

## 🚀 Quick Start (For New Users)

**Want to run this on a new PC? Follow these simple steps:**

### Windows Users (Easiest Method):

1. **Double-click `setup.bat`** - Wait 2-5 minutes for setup
2. **Double-click `run.bat`** - Start the server
3. **Open browser** → http://127.0.0.1:8000

### PyCharm Users:

1. Open project in PyCharm
2. Set Python interpreter to `venv` folder
3. Run `manage.py` or create Django Server configuration
4. Access at http://127.0.0.1:8000

**Default Admin Login:**

- URL: http://127.0.0.1:8000/admin
- Username: `admin`
- Password: `admin123`

**Note:**

- Make sure Python 3.8+ is installed. The setup script will handle everything else automatically.
- **Important:** Python 3.13 may have compatibility issues. If you encounter migration errors, use Python 3.11 or 3.12 instead.
- If you get migration import errors, run `fix_migration.bat` to fix it.

---

## Features

### User Management

- **Custom User Model**: Extended Django's AbstractUser with additional fields
- **Multiple User Types**: Patients, Admins, and Owners
- **Authentication**: Login, registration, and profile management
- **User Profiles**: Complete user information with phone numbers and personal details

### Core Functionality

- **Services Management**: Beauty and skincare services with categories
- **Products Management**: Skincare products with inventory tracking
- **Packages Management**: Service packages with session tracking
- **Appointments**: Booking system for services, products, and packages
- **Notifications**: Real-time notifications for appointments and updates
- **Feedback System**: Customer feedback and ratings

### Admin Features

- **Dashboard**: Comprehensive admin dashboard with statistics
- **User Management**: Manage patients, admins, and staff
- **Service Management**: Add, edit, and manage services
- **Product Management**: Inventory and product management
- **Package Management**: Create and manage service packages
- **Appointment Management**: View and manage all appointments
- **Store Hours**: Configure clinic operating hours
- **Closed Dates**: Manage clinic closure dates

## Project Structure

```
beauty_clinic_django/
├── accounts/                 # User management app
│   ├── models.py            # Custom User model and related models
│   ├── views.py             # Authentication views
│   ├── admin.py             # Admin configuration
│   └── urls.py              # URL routing
├── services/                 # Services management app
│   ├── models.py            # Service and category models
│   ├── views.py             # Service views
│   ├── admin.py             # Admin configuration
│   └── urls.py              # URL routing
├── products/                 # Products management app
│   ├── models.py            # Product models
│   ├── views.py             # Product views
│   ├── admin.py             # Admin configuration
│   └── urls.py              # URL routing
├── packages/                 # Packages management app
│   ├── models.py            # Package and booking models
│   ├── views.py             # Package views
│   ├── admin.py             # Admin configuration
│   └── urls.py              # URL routing
├── appointments/             # Appointments management app
│   ├── models.py            # Appointment and notification models
│   ├── views.py             # Appointment views
│   ├── admin.py             # Admin configuration
│   └── urls.py              # URL routing
├── templates/                # Django templates
│   ├── base.html            # Base template
│   ├── home.html            # Home page
│   ├── accounts/            # Authentication templates
│   ├── services/            # Service templates
│   ├── products/            # Product templates
│   ├── packages/            # Package templates
│   └── appointments/        # Appointment templates
├── static/                   # Static files (CSS, JS, images)
├── media/                    # User uploaded files
└── beauty_clinic_django/     # Main project settings
    ├── settings.py          # Django settings
    ├── urls.py              # Main URL configuration
    └── wsgi.py              # WSGI configuration
```

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Django 5.2.1 or higher

### Installation Steps

1. **Clone or navigate to the project directory**

   ```bash
   cd beauty_clinic_django
   ```

2. **Install Django (if not already installed)**

   ```bash
   pip install django
   ```

3. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser**

   ```bash
   python manage.py create_superuser
   ```

   This creates an admin user with:

   - Username: `admin`
   - Password: `admin123`

5. **Run the development server**

   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Database Models

### User Management

- **User**: Custom user model with user types (patient, admin, owner)
- **Attendant**: Clinic staff members
- **StoreHours**: Operating hours configuration
- **ClosedDates**: Clinic closure dates

### Services

- **ServiceCategory**: Service categories (Facials, IPL, etc.)
- **Service**: Individual services with pricing and duration
- **HistoryLog**: Audit trail for service changes

### Products

- **Product**: Skincare products with inventory tracking

### Packages

- **Package**: Service packages with session details
- **PackageBooking**: User package purchases
- **PackageAppointment**: Individual package session appointments

### Appointments

- **Appointment**: Regular appointments for services/products
- **Request**: Reschedule and cancellation requests
- **CancellationRequest**: Cancellation request tracking
- **Feedback**: Customer feedback and ratings
- **Notification**: System notifications

## Key Features Converted from PHP

### 1. User Authentication

- **Original**: PHP sessions with custom login system
- **Django**: Django's built-in authentication with custom user model

### 2. Database Operations

- **Original**: MySQL with PDO/mysqli
- **Django**: SQLite (default) with Django ORM

### 3. Template System

- **Original**: PHP includes and HTML
- **Django**: Django template system with inheritance

### 4. URL Routing

- **Original**: PHP file-based routing
- **Django**: Django URL patterns with namespacing

### 5. Admin Interface

- **Original**: Custom admin pages
- **Django**: Django admin interface with custom configurations

## Usage

### For Patients

1. Register an account or login
2. Browse services, packages, and products
3. Book appointments
4. View appointment history
5. Leave feedback

### For Admins

1. Login with admin credentials
2. Access admin panel at `/admin/`
3. Manage users, services, products, and packages
4. View and manage appointments
5. Configure store hours and closed dates

### For Owners

1. Login with owner credentials
2. Access owner-specific dashboard
3. View business analytics and reports

## Configuration

### Settings

- **Database**: SQLite (can be changed to PostgreSQL/MySQL)
- **Timezone**: Asia/Manila
- **Language**: English
- **Static Files**: Configured for development and production

### Customization

- Modify `settings.py` for database configuration
- Update templates in the `templates/` directory
- Customize static files in the `static/` directory
- Add new apps by creating new Django apps

## Development

### Adding New Features

1. Create new Django apps for new functionality
2. Define models in `models.py`
3. Create views in `views.py`
4. Configure URLs in `urls.py`
5. Create templates in `templates/` directory
6. Run migrations for model changes

### Testing

```bash
python manage.py test
```

### Creating Superusers

```bash
python manage.py createsuperuser
```

## Production Deployment

### Requirements

- Web server (Nginx/Apache)
- WSGI server (Gunicorn/uWSGI)
- Database (PostgreSQL recommended)
- Static file serving

### Environment Variables

Set the following environment variables for production:

- `DEBUG=False`
- `SECRET_KEY=your-secret-key`
- `DATABASE_URL=your-database-url`
- `ALLOWED_HOSTS=your-domain.com`

## Migration from PHP

### Data Migration

To migrate existing data from the PHP version:

1. Export data from MySQL database
2. Create Django fixtures or management commands
3. Import data using Django's data loading mechanisms

### File Migration

- Static files are already copied from the original `assets/` directory
- Update file paths in templates if needed
- Configure media file handling for user uploads

## 🔔 Automated Appointment Reminders (Cron Jobs)

This application supports automated appointment reminders via external cron service (cron-job.org):

### Reminder Schedule:

- **2 days before** appointment date
- **1 day before** appointment date
- **1 hour before** appointment time

### Setup Instructions:

**After deploying to Render**, follow the **CRONJOB_SETUP_GUIDE.md** for detailed configuration instructions.

**Quick Overview:**

1. Set `CRON_SECRET_TOKEN` in Render environment variables
2. Create cron-job.org account (free)
3. Create 3 cron jobs pointing to your Render endpoints:
   - `https://your-app.onrender.com/api/cron/reminders/?filter=2days&token=YOUR_TOKEN`
   - `https://your-app.onrender.com/api/cron/reminders/?filter=1day&token=YOUR_TOKEN`
   - `https://your-app.onrender.com/api/cron/reminders/?filter=1hour&token=YOUR_TOKEN`

See **CRONJOB_SETUP_GUIDE.md** for full step-by-step instructions.

## Support

For issues or questions:

1. Check Django documentation
2. Review the original PHP code for reference
3. Check Django logs for error messages

## License

This project maintains the same license as the original PHP version.

---

**Note**: This Django version maintains the same functionality as the original PHP application while leveraging Django's built-in features for better maintainability and security.
