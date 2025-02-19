from flask import Blueprint, request, render_template, redirect, url_for, session
from database import get_db
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

def verify_login(email, password):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE email=?', (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        return user[0]  # Return user ID
    return None

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        user_id = verify_login(request.form['email'], request.form['password'])
        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('main_page'))
        else:
            message = "Invalid credentials"
    return render_template('login.html', message=message)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))