"""
Database setup script - Run this to initialize the database
"""

import sqlite3
import os

DATABASE = 'users.db'

def setup_database():
    """Create database and tables"""
    
    # Remove old database if exists (for fresh start)
    if os.path.exists(DATABASE):
        print(f"Removing existing database: {DATABASE}")
        os.remove(DATABASE)
    
    print(f"Creating new database: {DATABASE}")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    print("Creating users table...")
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            coins INTEGER DEFAULT 100,
            total_lookups INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create lookups table
    print("Creating lookups table...")
    cursor.execute('''
        CREATE TABLE lookups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            serial TEXT NOT NULL,
            config TEXT NOT NULL,
            coins_spent INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for better performance
    print("Creating indexes...")
    cursor.execute('CREATE INDEX idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX idx_lookups_user_id ON lookups(user_id)')
    cursor.execute('CREATE INDEX idx_lookups_serial ON lookups(serial)')
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database setup completed successfully!")
    print(f"📁 Database file: {os.path.abspath(DATABASE)}")
    print("\nDatabase schema:")
    print("  - users: id, email, password_hash, coins (default: 100), total_lookups, created_at")
    print("  - lookups: id, user_id, serial, config, coins_spent, created_at")
    print("\nYou can now run: python backend_app.py")

if __name__ == '__main__':
    setup_database()
