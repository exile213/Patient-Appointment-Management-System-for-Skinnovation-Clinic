#!/usr/bin/env python
"""
SQLite to PostgreSQL Migration Script
Automates the migration process with data transfer
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Project settings
PROJECT_ROOT = Path(__file__).parent
SQLITE_DB = PROJECT_ROOT / 'db.sqlite3'
DATA_DUMP_FILE = PROJECT_ROOT / 'data_dump.json'
BACKUP_DIR = PROJECT_ROOT / 'db_backups'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(step_num, text):
    """Print a step number with text"""
    print(f"[Step {step_num}] {text}")

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    print(f"  Running: {' '.join(cmd)}")
    if description:
        print(f"  Purpose: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed")
        print(f"  Error: {e.stderr}")
        return False

def step_1_backup_sqlite():
    """Step 1: Backup SQLite database"""
    print_step(1, "Backing up SQLite database")
    
    if not SQLITE_DB.exists():
        print("  ✗ SQLite database not found!")
        return False
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"db_backup_{timestamp}.sqlite3"
    
    import shutil
    try:
        shutil.copy2(SQLITE_DB, backup_file)
        print(f"  ✓ Backed up to: {backup_file}")
        return True
    except Exception as e:
        print(f"  ✗ Backup failed: {e}")
        return False

def step_2_dump_sqlite_data():
    """Step 2: Dump data from SQLite to JSON"""
    print_step(2, "Exporting data from SQLite to JSON")
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'manage.py'),
        'dumpdata',
        '--all',
        '--indent=2',
        f'--output={DATA_DUMP_FILE}'
    ]
    
    if not run_command(cmd, "Export all data from SQLite to JSON file"):
        return False
    
    # Verify file was created
    if DATA_DUMP_FILE.exists():
        file_size = DATA_DUMP_FILE.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"  ✓ Data dump file created: {file_size:.2f} MB")
        return True
    else:
        print("  ✗ Data dump file not created")
        return False

def step_3_run_migrations():
    """Step 3: Run migrations on PostgreSQL"""
    print_step(3, "Running migrations on PostgreSQL")
    
    # Set Django settings module
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'beauty_clinic_django.settings'
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'manage.py'),
        'migrate',
        '--noinput'
    ]
    
    print(f"  Using DATABASE_URL from .env")
    print(f"  Running migrations...")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        print(f"  ✓ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Migration failed")
        print(f"  Error: {e.stderr}")
        return False

def step_4_load_data():
    """Step 4: Load data into PostgreSQL"""
    print_step(4, "Loading data into PostgreSQL")
    
    if not DATA_DUMP_FILE.exists():
        print(f"  ✗ Data dump file not found: {DATA_DUMP_FILE}")
        return False
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'manage.py'),
        'loaddata',
        str(DATA_DUMP_FILE)
    ]
    
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'beauty_clinic_django.settings'
    
    print(f"  Loading data from: {DATA_DUMP_FILE}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        print(f"  ✓ Data loaded successfully")
        if result.stderr:
            print(f"  Note: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Data load failed")
        print(f"  Error: {e.stderr}")
        return False

def step_5_verify_migration():
    """Step 5: Verify migration success"""
    print_step(5, "Verifying migration")
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'manage.py'),
        'shell',
        '-c',
        """
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from appointments.models import Appointment
from services.models import Service
from products.models import Product
from packages.models import Package
from payments.models import Payment

User = get_user_model()

print(f"Users: {User.objects.count()}")
print(f"User Profiles: {UserProfile.objects.count()}")
print(f"Appointments: {Appointment.objects.count()}")
print(f"Services: {Service.objects.count()}")
print(f"Products: {Product.objects.count()}")
print(f"Packages: {Package.objects.count()}")
print(f"Payments: {Payment.objects.count()}")
"""
    ]
    
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'beauty_clinic_django.settings'
    
    print(f"  Checking data in PostgreSQL database...")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        print(f"  ✓ Verification successful!")
        print(f"\n  Data counts in PostgreSQL:")
        for line in result.stdout.strip().split('\n'):
            if line:
                print(f"    {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Verification failed")
        print(f"  Error: {e.stderr}")
        return False

def main():
    """Main migration workflow"""
    print_header("SQLite to PostgreSQL Migration")
    
    # Check .env file exists
    env_file = PROJECT_ROOT / '.env'
    if not env_file.exists():
        print("  ✗ .env file not found! Create it with DATABASE_URL first.")
        return False
    
    print("  ✓ .env file detected")
    print(f"  ✓ SQLite database: {SQLITE_DB.exists()}")
    print(f"  ✓ Project root: {PROJECT_ROOT}")
    
    steps = [
        ("Backup SQLite Database", step_1_backup_sqlite),
        ("Dump SQLite Data to JSON", step_2_dump_sqlite_data),
        ("Run PostgreSQL Migrations", step_3_run_migrations),
        ("Load Data into PostgreSQL", step_4_load_data),
        ("Verify Migration Success", step_5_verify_migration),
    ]
    
    completed_steps = []
    
    for i, (name, func) in enumerate(steps, 1):
        print_header(f"Step {i}: {name}")
        success = func()
        completed_steps.append((name, success))
        
        if not success:
            print_header("Migration Failed")
            print(f"  Failed at: {name}")
            print(f"\n  Please fix the issue and try again.")
            return False
    
    # Success summary
    print_header("Migration Complete!")
    print("  ✓ All steps completed successfully\n")
    
    print("  Next steps:")
    print(f"  1. Verify your Django app works with PostgreSQL:")
    print(f"     python manage.py runserver")
    print(f"\n  2. Test key functionality (login, appointments, etc.)")
    print(f"\n  3. Delete the old SQLite database when ready:")
    print(f"     del {SQLITE_DB}")
    print(f"\n  4. Backup the data_dump.json file for records:")
    print(f"     Keep {DATA_DUMP_FILE}")
    print(f"\n  5. When deploying to Render:")
    print(f"     - Render will auto-set DATABASE_URL")
    print(f"     - Just push your code (with .env in .gitignore)")
    print(f"     - Run 'migrate' and 'loaddata' during deployment hook")
    print()

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
