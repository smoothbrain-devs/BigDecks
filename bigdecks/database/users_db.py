#"""Users database maintenance"""

#testing

import sqlite3
import os
#from . import get_db_connection

sqlite3.connect(r"C:\Users\Jimmy\Documents\BigDecks_Project\BigDecks\bigdecks\instance\users.db")
print(f"Trying to connect to: {db_path}")
#print(os.path.join(os.getcwd(), '..', 'instance', 'users.db'))
#conn = sqlite3.connect(os.path.join(os.getcwd(), '..', 'instance', 'users.db'))
#cursor = conn.cursor()
#cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#print(cursor.fetchall())
#conn.close()

#user = db.execute(
#    'SELECT * FROM user WHERE username = ?', (username,)
#).fetchone()


#g.user = get_db_connection("users").execute(
#    'SELECT * FROM user WHERE id = ?', (user_id,)
#).fetchone()


#db.execute(
#    "INSERT INTO user (username, password) VALUES (?, ?)",
#    (username, generate_password_hash(password)),
#)
#db.commit()
