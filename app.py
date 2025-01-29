from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
import os

app = Flask(__name__)

# Sicherheitsschlüssel (verwende eine Umgebungsvariable in Produktion)
app.secret_key = os.getenv('SECRET_KEY', 'mein_geheimer_schlüssel')

bcrypt = Bcrypt(app)

# Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# **Datenbankverbindung (lokal & online)**
def get_db_connection():
    database_url = os.getenv('DATABASE_URL', 'postgresql://quentin:05Que06$@localhost:5432/trainingsdb')

    # Falls die Datenbank auf Render läuft, SSL aktivieren
    if 'render.com' in database_url:
        database_url += '?sslmode=require'
    
    return psycopg2.connect(database_url)

# User-Klasse für Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

# Route: Verbindung zur Datenbank testen
@app.route('/test_db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return f"Database Connection Successful: {result}"
    except Exception as e:
        return f"Database Connection Failed: {str(e)}"

# Route: Startseite
@app.route('/')
def home():
    return render_template('index.html')

# Route: Trainingspläne
@app.route('/training')
def training():
    return render_template('training.html')

# Route: Ernährungspläne
@app.route('/nutrition')
def nutrition():
    return render_template('nutrition.html')

# Route: Fortschritte anzeigen (geschützt)
@app.route('/progress')
@login_required
def progress():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT ts.id, p.name, ts.date
        FROM training_sessions ts
        JOIN plans p ON ts.plan_id = p.id
        WHERE ts.user_id = %s
        ORDER BY ts.date DESC;
    ''', (current_user.id,))
    sessions = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('progress.html', sessions=sessions)

# Route: Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
            conn.commit()
            flash('Registrierung erfolgreich. Bitte melde dich an.', 'success')
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Benutzername existiert bereits.', 'danger')
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route: Anmeldung
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, password FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            login_user(User(user[0], user[1], user[2]))
            flash('Anmeldung erfolgreich.', 'success')
            return redirect(url_for('progress'))
        else:
            flash('Ungültige Anmeldedaten.', 'danger')

    return render_template('login.html')

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich abgemeldet.', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')




 

