import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)''')

    hashed_password = generate_password_hash("admin123", method='pbkdf2:sha256')
    c.execute('INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)',
              ('admin@example.com', hashed_password))
    
    conn.commit()
    conn.close()