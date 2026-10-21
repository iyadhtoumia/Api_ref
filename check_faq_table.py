import sqlite3

conn = sqlite3.connect('users.db')
result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faqs'").fetchone()
print(f"FAQs table exists: {result is not None}")

if result:
    count = conn.execute("SELECT COUNT(*) FROM faqs").fetchone()[0]
    print(f"FAQ count: {count}")
else:
    print("Creating FAQs table...")
    conn.execute('''
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    print("FAQs table created successfully")

conn.close()
