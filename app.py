from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
from openai import OpenAI

# OpenAI client initialization

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
DATABASE = 'app.db'


def add_sample_data():
    """Insert sample data for testing purposes."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    sample_data = [
        ('testtest', 'Food', 400, 'Expense', '2025-01-01'),
        ('testtest', 'Entertainment', 150, 'Expense', '2025-01-05'),
        ('testtest', 'Rent', 1200, 'Expense', '2025-01-10'),
        ('testtest', 'Salary', 3000, 'Income', '2025-01-01'),
        ('testtest', 'Freelance', 500, 'Income', '2025-01-15'),
    ]

    cursor.executemany('''
        INSERT INTO budgets (username, category, amount, type, date)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_data)
    conn.commit()
    conn.close()

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
            date TEXT NOT NULL
        )
    ''')

    # Add description column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE budgets ADD COLUMN description TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()


@app.route('/')
def index():
    """Render the main dashboard with balance and records."""
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch budgets
    cursor.execute('SELECT type, SUM(amount) FROM budgets WHERE username = ? GROUP BY type', (username,))
    budget_data = cursor.fetchall()
    income = sum(amount for t, amount in budget_data if t == 'Income')
    expense = sum(amount for t, amount in budget_data if t == 'Expense')
    balance = income - expense

    # Fetch all records for the calendar
    cursor.execute('SELECT type, category, amount, description, date FROM budgets WHERE username = ?', (username,))
    records = [
        {
            "type": row[0],
            "category": row[1],
            "amount": row[2],
            "description": row[3],
            "date": row[4]
        } for row in cursor.fetchall()
    ]

    conn.close()
    return render_template('index.html', balance=balance, income=income, expense=expense, records=records, username=username)


@app.route('/chat', methods=['POST'])
def chat():
    """Chatbot endpoint to generate budget recommendations or respond to greetings."""
    if not request.json or 'message' not in request.json:
        return jsonify({"error": "Invalid request"}), 400

    user_message = request.json['message'].strip().lower()
    username = session.get('username', 'User')

    # Greeting keywords
    greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]

    # Check if the user's message is a greeting
    if any(greet in user_message for greet in greetings):
        reply = f"Hello, {username}! How can I assist you with your budget today?"
        return jsonify({"reply": reply})

    # Fetch historical budget data for the user
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, SUM(amount) AS total, type
        FROM budgets
        WHERE username = ?
        GROUP BY category, type
    ''', (username,))
    budget_data = cursor.fetchall()
    conn.close()

    if not budget_data:
        return jsonify({"reply": "I couldn't find any historical budget data for you. Please add some records first!"})

    # Format budget data for AI
    formatted_budget_data = "\n".join(
        [f"{category} - {type_}: ${total:.2f}" for category, total, type_ in budget_data]
    )

    # Prompt for GPT-3.5
    prompt = (
        f"Here is the user's historical budget data:\n"
        f"{formatted_budget_data}\n\n"
        "Based on this data, recommend a plan for better budget management. List only 3 "
        "Suggest areas to reduce spending and how to optimize their budget for saving more."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial assistant helping users manage their budget effectively."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(e)
        reply = "Sorry, I am having trouble processing your request at the moment."

    return jsonify({"reply": reply})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login without password hashing."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration without password hashing."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')



@app.route('/logout')
def logout():
    """Log out the user."""
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/add_record', methods=['POST'])
def add_record():
    """Add a new record to the database."""
    if not session.get('username'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.json
    username = session['username']
    record_type = data.get('type')
    category = data.get('category')
    amount = data.get('amount')
    description = data.get('description', '')
    date = data.get('date')

    if not (record_type and category and amount and date):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budgets (username, category, amount, type, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, category, amount, record_type, description, date))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Record added successfully"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to add record"}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
