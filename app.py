from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Sicherheitsschlüssel (verwende eine Umgebungsvariable für Produktion)
app.secret_key = os.getenv('SECRET_KEY', 'mein_geheimer_schlüssel')

# **Datenbankkonfiguration (Render oder Lokal)**
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://quentin:05Que06$@localhost:5432/trainingsdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Flask-Migrate für Migrationen aktivieren
bcrypt = Bcrypt(app)

# Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# **User-Modell für Flask-Login**
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# **Route: Datenbankverbindung testen**
@app.route('/test_db')
def test_db():
    try:
        conn = db.engine.connect()
        conn.close()
        return "Database Connection Successful!"
    except Exception as e:
        return f"Database Connection Failed: {str(e)}"

# **Route: Startseite**
@app.route('/')
def home():
    return render_template('index.html')

# **Route: Trainingspläne**
@app.route('/training')
def training():
    return render_template('training.html')

# **Route: Ernährungspläne**
@app.route('/nutrition')
def nutrition():
    return render_template('nutrition.html')

# **Route: Fortschritte anzeigen (geschützt)**
@app.route('/progress')
@login_required
def progress():
    return render_template('progress.html')

# **Route: Registrierung**
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'Registrierung erfolgreich für {username}.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Benutzername existiert bereits.', 'danger')

    return render_template('register.html')

# **Route: Anmeldung**
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Anmeldung erfolgreich.', 'success')
            return redirect(url_for('progress'))
        else:
            flash('Ungültige Anmeldedaten.', 'danger')

    return render_template('login.html')

# **Route: Logout**
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich abgemeldet.', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')





 

