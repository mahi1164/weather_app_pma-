import sqlite3

conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        datetime TEXT NOT NULL,
        temperature REAL,
        description TEXT
    )
''')

conn.commit()
conn.close()
print("Database initialized successfully.")
