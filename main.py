from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'the_super_secret_key'  # Set a strong secret key

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://college-chatbot-99f9e-default-rtdb.firebaseio.com/'
})

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

        users_ref = db.reference('users')
        users = users_ref.get()
        user = None if isinstance(
            users, str) else users_ref.child(username).get()

        if user and user["password"] == password:
            session['username'] = user["username"]  # Store username in session
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

    users_ref = db.reference('users')
    users = users_ref.get()
    existing_user = None if isinstance(users, str) else users_ref.child(
        username).get()

    if existing_user:
        return "User with this username already exists", 400
    db.reference('users').child(username).set({
        "username": username,
        "password": password
    })

    return redirect(url_for('chat'))


@app.route('/chat')
def chat():
    if 'username' not in session:
        # Redirect to login if not authenticated
        return redirect(url_for('login'))

    users_ref = db.reference('users')
    users = users_ref.get()
    user = None if isinstance(users, str) else users_ref.child(
        session['username']).get()
    if not user:
        return redirect(url_for('login'))

    messages = user["messages"] if "messages" in user else {}

    placeholder_text = "Enter your questions here..."
    if "first_name" not in user or not user["first_name"]:
        placeholder_text = "Enter your first name here..."
    elif "last_name" not in user or not user["last_name"]:
        placeholder_text = "Enter your last name here..."
    elif "email" not in user or not user["email"]:
        placeholder_text = "Enter your email here..."

    processed_messages = [
        {
            "message": msg,
            "show_user_details": not (msg.lower().startswith("sorry") or msg.lower().startswith("please"))
        }
        for _, msg in messages.items()
    ]

    return render_template('chat.html', user=user, placeholder_text=placeholder_text, messages=processed_messages)


@ app.route('/chat', methods=['POST'])
def post_message():
    if 'username' not in session:
        return redirect(url_for('login'))

    message = request.form['message']
    normalized_message = message.strip().lower()

    users_ref = db.reference('users')
    users = users_ref.get()
    user = None if isinstance(users, str) else users_ref.child(
        session['username']).get()
    if not user:
        return redirect(url_for('login'))

    index = questions.index(
        normalized_message) if normalized_message in questions else -1

    if ("first_name" not in user or not user["first_name"] or "last_name" not in user or not user["last_name"] or "email" not in user or not user["email"]) and index != -1:
        users_ref.child(user["username"]).child("messages").push("Please, enter the requested information first."
                                                                 )
        return redirect(url_for('chat'))
    if "first_name" not in user or not user["first_name"]:
        db.reference('users/' + user["username"]).update({
            "first_name": message
        })
        return redirect(url_for('chat'))
    if "last_name" not in user or not user["last_name"]:
        db.reference('users/' + user["username"]).update({
            "last_name": message
        })
        return redirect(url_for('chat'))
    if "email" not in user or not user["email"]:
        db.reference('users/' + user["username"]).update({
            "email": message
        })
        return redirect(url_for('chat'))
    if index == -1:
        users_ref.child(user["username"]).child('messages').push("Sorry, I don't understand. You can ask me questions like: 'does the college have a football team?', 'does it offer a computer science major?', 'what is the in-state tuition?', 'does it provide on-campus housing?'"
                                                                 )
        return redirect(url_for('chat'))

    users_ref.child(user["username"]).child('messages').push(answers[index])

    return redirect(url_for('chat'))


if __name__ == '__main__':
    app.run(debug=True)
