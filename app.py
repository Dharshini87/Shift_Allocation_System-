from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3, os
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_PATH = os.path.join("database", "users.db")

# ---------------------- ROLES ----------------------
ROLES = [
    "Body Shop",
    "PTCFD Shop",
    "Paint Shop",
    "Assembly",
    "End of Line"
]

SUB_ROLES = {
    "Assembly": [
        "Pre-Assembly",
        "Under Body",
        "Floor Conveyor (1-5)",
        "Floor Conveyor (6-12)",
        "Sub Assembly"
    ],
    "End of Line": [
        "Shift 1",
        "Shift 2"
    ]
}

# ---------------------- STATIONS ----------------------
role_stations = {
    "Body Shop": ["Station 1", "Station 2", "Station 3"],
    "PTCFD Shop": ["Station 4", "Station 5"],
    "Paint Shop": ["Paint Booth", "Inspection", "Polish"]
}

subrole_stations = {
    "Assembly": {
        "Pre-Assembly": ["Pre Line 1", "Pre Line 2"],
        "Under Body": ["UB Line 1", "UB Line 2"],
        "Floor Conveyor (1-5)": ["FC1", "FC2", "FC3", "FC4", "FC5"],
        "Floor Conveyor (6-12)": ["FC6", "FC7", "FC8", "FC9", "FC10", "FC11", "FC12"],
        "Sub Assembly": ["Sub Line 1", "Sub Line 2"]
    },
    "End of Line": {
        "Shift 1": ["EOL Test Bay 1", "EOL Test Bay 2"],
        "Shift 2": ["EOL Test Bay 3", "EOL Test Bay 4"]
    }
}

# ---------------------- OPERATORS ----------------------
role_operators = {
    "Body Shop": ["Worker 101 (101)", "Worker 102 (102)", "Worker 103 (103)"],
    "PTCFD Shop": ["Worker 201 (201)", "Worker 202 (202)"],
    "Paint Shop": ["Worker 301 (301)", "Worker 302 (302)"]
}

subrole_operators = {
    "Assembly": {
        "Pre-Assembly": ["Worker A1 (401)", "Worker A2 (402)"],
        "Under Body": ["Worker B1 (403)", "Worker B2 (404)"],
        "Floor Conveyor (1-5)": ["Worker C1 (405)", "Worker C2 (406)", "Worker C3 (407)"],
        "Floor Conveyor (6-12)": ["Worker D1 (408)", "Worker D2 (409)", "Worker D3 (410)"],
        "Sub Assembly": ["Worker E1 (411)", "Worker E2 (412)"]
    },
    "End of Line": {
        "Shift 1": ["Worker F1 (501)", "Worker F2 (502)"],
        "Shift 2": ["Worker G1 (503)", "Worker G2 (504)"]
    }
}

# ---------------------- DATABASE INIT ----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            sub_role TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS allocations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            shift TEXT,
            shift_time TEXT,
            alloc_time TEXT,
            allocated_by TEXT,
            role TEXT,
            sub_role TEXT,
            station TEXT,
            operator TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.before_request
def before_request():
    init_db()

# ---------------------- ROUTES ----------------------
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/achievements')
def achievements():
    return render_template("achievements.html")

# ---------------------- REGISTER ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        sub_role = request.form.get('sub_role') if role in SUB_ROLES else None

        if password != confirm:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))

        if not email.endswith('@company.com'):
            flash("Only company email allowed!", "error")
            return redirect(url_for('register'))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (name, email, password, role, sub_role) VALUES (?, ?, ?, ?, ?)",
                (name, email, password, role, sub_role)
            )
            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered!", "error")
        finally:
            conn.close()

    return render_template('register.html', ROLES=ROLES, SUB_ROLES=SUB_ROLES)

# ---------------------- LOGIN ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, password, role))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'role': user[4],
                'sub_role': user[5]
            }
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials!", "error")

    return render_template('login.html', ROLES=ROLES, SUB_ROLES=SUB_ROLES)

# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

# ---------------------- FORM STEP 1 ----------------------
@app.route('/form_step1', methods=['GET', 'POST'])
def form_step1():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        shift_time = request.form['shift_time'] + " " + request.form['shift_period']
        alloc_time = request.form['alloc_time'] + " " + request.form['alloc_period']

        session['form1'] = {
            'date': request.form['date'],
            'shift': request.form['shift'],
            'shift_time': shift_time,
            'alloc_time': alloc_time,
            'allocated_by': session['user']['name']
        }

        return redirect(url_for('form_step2'))

    return render_template('form_step1.html', user=session['user'], form1=session.get('form1'))

# ---------------------- FORM STEP 2 ----------------------
@app.route('/form_step2', methods=['GET', 'POST'])
def form_step2():
    if 'user' not in session:
        return redirect(url_for('login'))
    if 'form1' not in session:
        flash("⚠ Please complete step 1 first.", "error")
        return redirect(url_for('form_step1'))

    user = session['user']
    role = user['role']
    sub_role = user['sub_role']

    stations = subrole_stations.get(role, {}).get(sub_role, role_stations.get(role, []))
    operators = subrole_operators.get(role, {}).get(sub_role, role_operators.get(role, []))

    if request.method == 'POST':
        form1 = session['form1']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO allocations (date, shift, shift_time, alloc_time, allocated_by, role, sub_role, station, operator)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            form1['date'], form1['shift'], form1['shift_time'], form1['alloc_time'],
            form1['allocated_by'], user['role'], user['sub_role'],
            request.form['station'], request.form['operator']
        ))
        conn.commit()
        conn.close()

        session.pop('form1', None)
        return redirect(url_for('download_choice'))

    return render_template('form_step2.html', stations=stations, operators=operators, form1=session.get('form1'))

# ---------------------- DOWNLOAD CHOICE PAGE ----------------------
@app.route('/download_choice')
def download_choice():
    return render_template('download_choice.html')

# ---------------------- DOWNLOAD DATA ----------------------
@app.route('/download/<period>')
def download(period):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM allocations", conn)
    conn.close()

    if df.empty:
        flash("No data available!", "error")
        return redirect(url_for('dashboard'))

    df['date'] = pd.to_datetime(df['date'])
    today = datetime.now()

    if period == "daily":
        df = df[df['date'].dt.date == today.date()]
        filename = "Daily_Allocations.xlsx"
    elif period == "weekly":
        df = df[df['date'] >= today - timedelta(days=7)]
        filename = "Weekly_Allocations.xlsx"
    else:
        df = df[df['date'] >= today - timedelta(days=30)]
        filename = "Monthly_Allocations.xlsx"

    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", filename)
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

# ---------------------- LOGOUT ----------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    os.makedirs("database", exist_ok=True)
    app.run(debug=True)



