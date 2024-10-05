from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'the_super_secret_key'  # Set a strong secret key

# SQLite setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "app.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.commit()
        conn.close()

        if user and user[2] == password: 
            session['username'] = user[1]  # Store username in session
            return redirect(url_for('profile'))
        else:
            return "Invalid username or password", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    firstname = request.form['firstName']
    lastname = request.form['lastName']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, first_name, last_name, email) VALUES (?, ?, ?, ?, ?)",
              (username, password, firstname, lastname, email))
    conn.commit()
    conn.close()

    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)