from django.core.management.base import BaseCommand
import mysql.connector


class Command(BaseCommand):
    help = 'Debug attendants table structure'

    def handle(self, *args, **options):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='beauty_clinic2'
            )
            cursor = conn.cursor(dictionary=True)
            self.stdout.write('Connected to MySQL database successfully!')
            
            cursor.execute("SELECT * FROM attendants LIMIT 1")
            attendant = cursor.fetchone()
            
            if attendant:
                self.stdout.write('Attendant data structure:')
                for key, value in attendant.items():
                    self.stdout.write(f'  {key}: {value} (type: {type(value)})')
            else:
                self.stdout.write('No attendants found')
                
        except Exception as e:
            self.stdout.write(f'Error: {e}')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
