import os
import shutil
import gzip
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Backup the database (supports SQLite, PostgreSQL, MySQL)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backups (default: backups)',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress backup file using gzip',
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=10,
            help='Number of backups to keep (default: 10)',
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        compress = options['compress']
        keep_count = options['keep']
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(self.style.SUCCESS(f'Created backup directory: {output_dir}'))
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        db_engine = db_config['ENGINE']
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if 'sqlite' in db_engine.lower():
                backup_path = self.backup_sqlite(db_config, output_dir, timestamp, compress)
            elif 'postgresql' in db_engine.lower():
                backup_path = self.backup_postgresql(db_config, output_dir, timestamp, compress)
            elif 'mysql' in db_engine.lower():
                backup_path = self.backup_mysql(db_config, output_dir, timestamp, compress)
            else:
                self.stdout.write(self.style.ERROR(f'Unsupported database engine: {db_engine}'))
                return
            
            if backup_path and os.path.exists(backup_path):
                # Get file size
                file_size = os.path.getsize(backup_path) / (1024 * 1024)  # Size in MB
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Database backup created successfully!\n'
                        f'  Backup file: {backup_path}\n'
                        f'  File size: {file_size:.2f} MB\n'
                        f'  Timestamp: {timestamp}'
                    )
                )
                
                # Cleanup old backups
                self.cleanup_old_backups(output_dir, keep_count)
            else:
                self.stdout.write(self.style.ERROR('Backup failed: File was not created'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating backup: {str(e)}'))

    def backup_sqlite(self, db_config, output_dir, timestamp, compress):
        """Backup SQLite database"""
        db_path = db_config['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f'Database file not found: {db_path}'))
            return None
        
        backup_filename = f'db_backup_{timestamp}.sqlite3'
        backup_path = os.path.join(output_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Compress if requested
        if compress:
            compressed_path = f'{backup_path}.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_path)
            return compressed_path
        
        return backup_path

    def backup_postgresql(self, db_config, output_dir, timestamp, compress):
        """Backup PostgreSQL database using pg_dump"""
        db_name = db_config['NAME']
        db_user = db_config.get('USER', 'postgres')
        db_password = db_config.get('PASSWORD', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '5432')
        
        backup_filename = f'db_backup_{timestamp}.sql'
        backup_path = os.path.join(output_dir, backup_filename)
        
        # Set password via environment variable
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-d', db_name,
            '-f', backup_path,
            '--no-password'
        ]
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            # Compress if requested
            if compress:
                compressed_path = f'{backup_path}.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                return compressed_path
            
            return backup_path
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'pg_dump failed: {e.stderr}'))
            return None
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('pg_dump not found. Please install PostgreSQL client tools.'))
            return None

    def backup_mysql(self, db_config, output_dir, timestamp, compress):
        """Backup MySQL database using mysqldump"""
        db_name = db_config['NAME']
        db_user = db_config.get('USER', 'root')
        db_password = db_config.get('PASSWORD', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')
        
        backup_filename = f'db_backup_{timestamp}.sql'
        backup_path = os.path.join(output_dir, backup_filename)
        
        # Build mysqldump command
        cmd = [
            'mysqldump',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            db_name
        ]
        
        try:
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
            
            # Compress if requested
            if compress:
                compressed_path = f'{backup_path}.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                return compressed_path
            
            return backup_path
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'mysqldump failed: {e.stderr.decode()}'))
            return None
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('mysqldump not found. Please install MySQL client tools.'))
            return None

    def cleanup_old_backups(self, backup_dir, keep_count=10):
        """Keep only the most recent backups"""
        try:
            # Get all backup files (SQLite, SQL, and compressed)
            backup_files = []
            for ext in ['.sqlite3', '.sql', '.sqlite3.gz', '.sql.gz']:
                backup_files.extend([
                    os.path.join(backup_dir, f)
                    for f in os.listdir(backup_dir)
                    if f.startswith('db_backup_') and f.endswith(ext)
                ])
            
            # Sort by modification time (newest first)
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove old backups
            if len(backup_files) > keep_count:
                for old_backup in backup_files[keep_count:]:
                    os.remove(old_backup)
                    self.stdout.write(
                        self.style.WARNING(f'  Removed old backup: {os.path.basename(old_backup)}')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'  Could not cleanup old backups: {str(e)}')
            )

