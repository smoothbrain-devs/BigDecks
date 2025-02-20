"""Users database maintenance"""

#testing

from . import get_db_connection


user = db.execute(
    'SELECT * FROM user WHERE username = ?', (username,)
).fetchone()


g.user = get_db_connection("users").execute(
    'SELECT * FROM user WHERE id = ?', (user_id,)
).fetchone()


db.execute(
    "INSERT INTO user (username, password) VALUES (?, ?)",
    (username, generate_password_hash(password)),
)
db.commit()
