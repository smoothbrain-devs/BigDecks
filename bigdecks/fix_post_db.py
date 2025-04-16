"""
Script to initialize the post table in post.db

Run this script from your project root directory with:
python fix_post_db.py
"""

import os
import sqlite3
from flask import Flask

# Create a minimal Flask app to use the instance path
app = Flask(__name__, instance_relative_config=True)

def init_post_table():
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Path to post.db
    db_path = os.path.join(app.instance_path, "post.db")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Create the post table schema
    print(f"Creating post table in {db_path}")
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS post (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Post table created successfully!")
    return True

if __name__ == "__main__":
    init_post_table()