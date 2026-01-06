#!/usr/bin/env python
"""
Clear PostgreSQL database and recreate fresh
"""
import psycopg2
import sys

try:
    # First, disconnect all existing connections
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='imperial12',
        port=5432,
        database='postgres'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Terminating all connections to beauty_clinic_db...")
    cursor.execute("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'beauty_clinic_db'
        AND pid <> pg_backend_pid();
    """)
    
    print("Dropping database...")
    cursor.execute("DROP DATABASE IF EXISTS beauty_clinic_db;")
    
    print("Creating fresh database...")
    cursor.execute("CREATE DATABASE beauty_clinic_db;")
    
    print("✓ Database recreated successfully!")
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
