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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) DEFAULT NULL,
    last_name VARCHAR(50) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
c.execute('''CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL REFERENCES users(username),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES chats(id),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()

questions = [
    "does the college have a football team?",
    "does it offer a computer science major?",
    "what is the in-state tuition?",
    "does it provide on-campus housing?"
]

answers = [
    "Yes, the college has a football team. The team competes in the NCAA Division I and has a strong tradition of excellence. The football program is well-supported by the college community, and home games are held at the state-of-the-art stadium on campus. Students have the opportunity to try out for the team, and there are also intramural leagues for those who want to play football recreationally.",
    "Yes, the college offers a computer science major. The program is designed to provide students with a solid foundation in computer science principles, including programming, algorithms, data structures, and software engineering. The curriculum includes both theoretical and practical courses, and students have access to modern computer labs and research facilities. Additionally, the college has partnerships with leading tech companies, providing students with internship and job opportunities.",
    "The in-state tuition is $10,000 per year. This cost covers tuition and fees for full-time undergraduate students. The college also offers various financial aid options, including scholarships, grants, and work-study programs, to help make education more affordable. Students are encouraged to apply for financial aid early to maximize their chances of receiving assistance.",
    "Yes, the college provides on-campus housing. There are several residence halls available, each offering a range of amenities such as furnished rooms, study areas, common lounges, and dining facilities. Living on campus provides students with a convenient and immersive college experience, fostering a sense of community and making it easier to participate in campus activities and events. Housing options include traditional dormitories, suite-style living, and apartment-style accommodations."
]


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
        user = c.execute(
            'SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.commit()
        conn.close()

        if user and user[2] == password:
            session['username'] = user[1]  # Store username in session
            return redirect(url_for('chat'))
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

    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if the user with the given username already exists
    existing_user = c.execute(
        "SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if existing_user:
        return "User with this username already exists", 400
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, password))
    conn.commit()
    conn.close()

    return redirect(url_for('chat'))


@app.route('/chat')
def chat():
    if 'username' not in session:
        # Redirect to login if not authenticated
        return redirect(url_for('login'))

    print("session username", session['username'])
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()
    print("user", user)
    # fetch user's chat
    c.execute("SELECT * FROM chats WHERE username=?", (session['username'],))
    chat = c.fetchone()
    if not chat:
        c.execute("INSERT INTO chats (username) VALUES (?)",
                  (session['username'],))
        conn.commit()
        c.execute("SELECT * FROM chats WHERE username=?",
                  (session['username'],))
        chat = c.fetchone()
    # fetch chat messages
    c.execute("SELECT * FROM messages WHERE chat_id=?", (chat[0],))
    messages = c.fetchall()
    conn.commit()
    conn.close()

    if not user:
        return redirect(url_for('login'))

    placeholder_text = "Enter your questions here..."
    if not user[3]:
        placeholder_text = "Enter your first name here..."
    elif not user[4]:
        placeholder_text = "Enter your last name here..."
    elif not user[5]:
        placeholder_text = "Enter your email here..."

    processed_messages = [
        {
            "message": msg[2],
            "show_user_details": not (msg[2].lower().startswith("sorry") or msg[2].lower().startswith("please"))
        }
        for msg in messages
    ]

    return render_template('chat.html', user=user, placeholder_text=placeholder_text, messages=processed_messages)


@app.route('/chat', methods=['POST'])
def post_message():
    if 'username' not in session:
        return redirect(url_for('login'))

    message = request.form['message']
    normalized_message = message.strip().lower()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()
    c.execute("SELECT * FROM chats WHERE username=?", (session['username'],))
    chat = c.fetchone()

    index = questions.index(
        normalized_message) if normalized_message in questions else -1
    if not user:
        return redirect(url_for('login'))
    # Check if the user has provided their first name, last name, and email
    if (not user[3] or not user[4] or not user[5]) and index != -1:
        c.execute("INSERT INTO messages (chat_id, message) VALUES (?, ?)",
                  (chat[0], "Please, enter the requested information first."))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))
    if not user[3]:
        c.execute("UPDATE users SET first_name = ? WHERE username = ?",
                  (message, session['username']))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))
    if not user[4]:
        c.execute("UPDATE users SET last_name = ? WHERE username = ?",
                  (message, session['username']))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))
    if not user[5]:
        c.execute("UPDATE users SET email = ? WHERE username = ?",
                  (message, session['username']))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))
    if index == -1:
        c.execute("INSERT INTO messages (chat_id, message) VALUES (?, ?)",
                  (chat[0], "Sorry, I don't understand. You can ask me questions like: 'does the college have a football team?', 'does it offer a computer science major?', 'what is the in-state tuition?', 'does it provide on-campus housing?'"))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))

    c.execute("INSERT INTO messages (chat_id, message) VALUES (?, ?)",
              (chat[0], answers[index]))
    conn.commit()
    conn.close()

    return redirect(url_for('chat'))


if __name__ == '__main__':
    app.run(debug=True)
