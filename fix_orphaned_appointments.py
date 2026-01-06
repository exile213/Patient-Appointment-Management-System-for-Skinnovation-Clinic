import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Find appointments with invalid attendant_id
cursor.execute('''
    SELECT id, attendant_id 
    FROM appointments 
    WHERE attendant_id NOT IN (SELECT id FROM users)
''')
bad_appointments = cursor.fetchall()

print(f'Found {len(bad_appointments)} appointments with invalid attendant_id:')
for row in bad_appointments:
    print(f'  Appointment ID: {row[0]}, Invalid Attendant ID: {row[1]}')

if bad_appointments:
    # Get a valid attendant user
    cursor.execute("SELECT id FROM users WHERE user_type='attendant' LIMIT 1")
    valid_attendant = cursor.fetchone()
    
    if valid_attendant:
        valid_attendant_id = valid_attendant[0]
        print(f'\nReassigning to valid attendant ID: {valid_attendant_id}')
        
        # Update all invalid appointments
        invalid_ids = [row[1] for row in bad_appointments]
        for invalid_id in set(invalid_ids):
            cursor.execute(
                'UPDATE appointments SET attendant_id = ? WHERE attendant_id = ?',
                (valid_attendant_id, invalid_id)
            )
            print(f'  Updated appointments with attendant_id={invalid_id}')
        
        conn.commit()
        print(f'\nSuccessfully fixed {len(bad_appointments)} appointments!')
    else:
        print('ERROR: No valid attendant found!')
else:
    print('No orphaned appointments found. Database is clean!')

conn.close()
