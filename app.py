from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_bcrypt import Bcrypt
from datetime import date
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
import os

app = Flask(__name__)

# Sicherheitsschlüssel (verwende eine Umgebungsvariable für Produktion)
app.secret_key = os.getenv('SECRET_KEY', 'mein_geheimer_schlüssel')

bcrypt = Bcrypt(app)

# Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# **Datenbankverbindung mit psycopg2 (Render oder Lokal)**


def get_db_connection():
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        raise RuntimeError("❌ Fehler: `DATABASE_URL` ist nicht gesetzt. Überprüfe die Render-Umgebungsvariablen!")

    print(f"DEBUG: Verbindung zu PostgreSQL: {db_url}")  # Debugging

    conn = psycopg2.connect(db_url, sslmode="require")
    conn.cursor().execute("SET search_path TO public;")  # Falls das Schema nicht standardmäßig genutzt wird
    return conn



# Flask-Login User-Klasse
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

# **Route: Datenbankverbindung testen**
@app.route('/test_db')
def test_db():
    try:
        conn = get_db_connection()
        conn.close()
        return "Database Connection Successful!"
    except Exception as e:
        return f"Database Connection Failed: {str(e)}"
        
        


# **Route: Datei-Download ohne .html-Probleme**
@app.route('/downloads/<filename>')
def download_file(filename):
    file_path = os.path.join("downloads", filename)

    if not os.path.exists(file_path):
        return "Datei nicht gefunden", 404

    return send_file(file_path, as_attachment=True)

    
    
#Logik Kalorienrechner

def calculate_tdee(gender, age, weight, height, job_activity, sport_frequency):
    """Berechnet den Gesamtumsatz (TDEE) basierend auf verschiedenen Faktoren."""
    
    # Grundumsatz (BMR) nach Mifflin-St Jeor Formel
    if gender == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    # Aktivitätsfaktoren für verschiedene Berufsgruppen
    activity_factors = {
        "sedentary": 1.2,  # Bürojob, kaum Bewegung
        "lightly_active": 1.375,  # Leichte Bewegung (z. B. Lehrer, Verkäufer)
        "moderately_active": 1.55,  # Handwerker, Kellner
        "very_active": 1.725,  # Bauarbeiter, Landwirt
        "extremely_active": 1.9,  # Leistungssportler, Schwerstarbeit
    }

    # Sportkalorien basierend auf der Trainingshäufigkeit
    sport_calories = {
        "none": 0,
        "light": 200,
        "moderate": 400,
        "heavy": 600,
        "extreme": 800,
    }

    # Berechnung des Gesamtumsatzes
    if job_activity not in activity_factors or sport_frequency not in sport_calories:
        return None  # Falls falsche Eingaben gemacht wurden

    tdee = bmr * activity_factors[job_activity] + sport_calories[sport_frequency]

    # Berechnung für Bulk (+300 kcal) und Diät (-300 kcal)
    bulk_calories = tdee + 300
    diet_calories = tdee - 300

    # Makronährstoffverteilung (30% Eiweiß, 25% Fett, 45% Kohlenhydrate)
    def calculate_macros(calories):
        protein = (calories * 0.25) / 4  # Eiweiß: 4 kcal/g
        fat = (calories * 0.3) / 9  # Fett: 9 kcal/g
        carbs = (calories * 0.45) / 4  # Kohlenhydrate: 4 kcal/g
        return round(protein, 1), round(fat, 1), round(carbs, 1)

    maintain_macros = calculate_macros(tdee)
    bulk_macros = calculate_macros(bulk_calories)
    diet_macros = calculate_macros(diet_calories)

    return {
        "tdee": round(tdee, 2),
        "bulk_calories": round(bulk_calories, 2),
        "diet_calories": round(diet_calories, 2),
        "maintain_macros": maintain_macros,
        "bulk_macros": bulk_macros,
        "diet_macros": diet_macros
    }


#Route: Kalorienrechner
@app.route('/Kalorien', methods=['GET', 'POST'])
def Kalorien():
    result = None
    if request.method == 'POST':
        try:
            gender = request.form['gender']
            age = int(request.form['age'])
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            job_activity = request.form['job_activity']
            sport_frequency = request.form['sport_frequency']

            # Berechnung des Kalorienbedarfs
            result = calculate_tdee(gender, age, weight, height, job_activity, sport_frequency)

        except ValueError:
            result = "Ungültige Eingabe, bitte überprüfe deine Werte."

    return render_template('Kalorien.html', result=result)

 
 
# **Route: Startseite**
@app.route('/')
def home():
    return render_template('index.html')
    

    
# **Route: add**
@app.route('/add')
def add():
    return render_template('add.html')



# **Route: Trainingspläne**
@app.route('/training')
@login_required
def training():
    return render_template('training.html')
    
    

# **Route: Ernährungspläne**
@app.route('/nutrition')
def nutrition():
    return render_template('nutrition.html')
    
    

# **Route: GKAnfänger**
@app.route('/gk_anfaenger')
def gk_anfaenger():
    return render_template('gk_anfaenger.html')
    
# **Route: GKFortgeschrittenr**
@app.route('/gk_fortgeschrittene')
def gk_fortgeschrittene():
    return render_template('gk_fortgeschrittene.html')
    
    
# **Route: OKUKAnfänger**
@app.route('/okuk_anfaenger')
def okuk_anfaenger():
    return render_template('okuk_anfaenger.html')
    
    
# **Route: OKUKFortgeschritten**
@app.route('/okuk_fortgeschrittene')
def okuk_fortgeschrittene():
    return render_template('okuk_fortgeschrittene.html')
    
# **Route: PPL**
@app.route('/ppl_anfaenger')
def ppl_anfaenger():
    return render_template('ppl_anfaenger.html')

    
#Route: Plan auswählen
@app.route('/select_plan', methods=['GET', 'POST'])
@login_required
def select_plan():
    conn = get_db_connection()
    cur = conn.cursor()

    # Trainingspläne aus der Datenbank abrufen
    cur.execute('SELECT id, name FROM plans;')
    plans = cur.fetchall()

    cur.close()
    conn.close()

    if request.method == 'POST':
        selected_plan_id = request.form['plan_id']
        return redirect(url_for('track_plan', plan_id=selected_plan_id))

    return render_template('select_plan.html', plans=[{'id': p[0], 'name': p[1]} for p in plans])
    
    


# **Route: Fortschritte anzeigen (geschützt)**
@app.route('/progress', methods=['GET'])
@login_required
def progress():
    conn = get_db_connection()
    cur = conn.cursor()

    # Trainingssessions des aktuellen Benutzers abrufen
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

    
    

#Training tracken
@app.route('/track_plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def track_plan(plan_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Übungen für den Plan abrufen
    cur.execute('SELECT id, exercise_name FROM exercises WHERE plan_id = %s;', (plan_id,))
    exercises = cur.fetchall()

    if request.method == 'POST':
        date = request.form['date']

        # Trainingssession speichern
        cur.execute(
            'INSERT INTO training_sessions (user_id, plan_id, date) VALUES (%s, %s, %s) RETURNING id;',
            (current_user.id, plan_id, date)
        )
        session_id = cur.fetchone()[0]

        # Trainingsdetails für jede Übung speichern
        for exercise in exercises:
            exercise_id = exercise[0]
            sets = request.form.get(f'sets_{exercise_id}')
            reps = request.form.get(f'reps_{exercise_id}')
            weight = request.form.get(f'weight_{exercise_id}')

            cur.execute(
                'INSERT INTO progress (session_id, exercise_id, sets, reps, weight) VALUES (%s, %s, %s, %s, %s);',
                (session_id, exercise_id, sets, reps, weight)
            )

        conn.commit()  # WICHTIG: Speichert die Änderungen in der Datenbank
        cur.close()
        conn.close()

        flash('Training erfolgreich abgeschlossen!', 'success')

        # ✅ Benutzer zur `progress`-Seite weiterleiten
        return redirect(url_for('progress'))

    cur.close()
    conn.close()
    return render_template('track_plan.html', exercises=exercises, plan_id=plan_id)


#Session details bei progress
@app.route('/session/<int:session_id>')
@login_required
def session_details(session_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Informationen zur Trainingssession abrufen
    cur.execute('''
        SELECT ts.date, p.name
        FROM training_sessions ts
        JOIN plans p ON ts.plan_id = p.id
        WHERE ts.id = %s AND ts.user_id = %s;
    ''', (session_id, current_user.id))
    session_info = cur.fetchone()

    if not session_info:
        flash('Keine Details für diese Session gefunden oder unberechtigter Zugriff.', 'danger')
        return redirect(url_for('progress'))

    # Übungen und Fortschritte für diese Session abrufen
    cur.execute('''
        SELECT e.exercise_name, pr.sets, pr.reps, pr.weight
        FROM progress pr
        JOIN exercises e ON pr.exercise_id = e.id
        WHERE pr.session_id = %s;
    ''', (session_id,))
    progress = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('session_details.html', session=session_info, progress=progress)



# **Route: Registrierung**
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Benutzername und Passwort dürfen nicht leer sein.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id', (username, hashed_password))
            user_id = cur.fetchone()[0]
            conn.commit()
            flash(f'Registrierung erfolgreich für {username}. Bitte melde dich an.', 'success')
            print(f"DEBUG: Benutzer {username} mit ID {user_id} registriert")  # Debug-Ausgabe
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Benutzername existiert bereits.', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Datenbankfehler: {str(e)}', 'danger')
            print(f"DEBUG: Fehler bei Registrierung - {str(e)}")  # Debug-Ausgabe
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# **Route: Anmeldung**
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

        if user:
            print(f"DEBUG: Benutzer {user[1]} gefunden mit ID {user[0]}")  # Debug-Ausgabe

            if bcrypt.check_password_hash(user[2], password):
                login_user(User(user[0], user[1], user[2]))
                flash('Anmeldung erfolgreich.', 'success')
                return redirect(url_for('progress'))
            else:
                flash('Falsches Passwort.', 'danger')
                print("DEBUG: Passwort stimmt nicht überein!")  # Debug-Ausgabe
        else:
            flash('Benutzer existiert nicht.', 'danger')
            print("DEBUG: Benutzer nicht gefunden!")  # Debug-Ausgabe

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







 

