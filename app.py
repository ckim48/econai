from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
from openai import OpenAI
from datetime import datetime
from calendar import monthrange

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
    return render_template('landing.html')
@app.route('/main')
def main():
    """Render the main dashboard with balance and records."""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT fullname FROM users WHERE username = ?', (username,))
    user_data = cursor.fetchone()
    fullname = user_data[0] if user_data else username  # Default to username if full name is not found

    # Fetch budgets
    cursor.execute('SELECT type, SUM(amount) FROM budgets WHERE username = ? GROUP BY type', (username,))
    budget_data = cursor.fetchall()
    income = sum(amount for t, amount in budget_data if t == 'Income')
    expense = sum(amount for t, amount in budget_data if t == 'Expense')
    balance = income - expense

    # Fix datetime usage
    today = datetime.today().strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT SUM(amount) FROM budgets
        WHERE username = ? AND type = 'Expense' AND strftime('%Y-%m', date) = strftime('%Y-%m', ?)
    ''', (username, today))
    monthly_expense = cursor.fetchone()[0] or 0
    monthly_remaining = balance - monthly_expense

    cursor.execute('''
        SELECT SUM(amount) FROM budgets
        WHERE username = ? AND type = 'Expense' AND date BETWEEN date(?, '-7 days') AND ?
    ''', (username, today, today))
    weekly_expense = cursor.fetchone()[0] or 0
    weekly_remaining = balance - weekly_expense

    # Calculate daily spending and remaining days in the month
    cursor.execute('''
        SELECT SUM(amount) FROM budgets
        WHERE username = ? AND type = 'Expense' AND strftime('%Y-%m-%d', date) = ?
    ''', (username, today))
    daily_expense = cursor.fetchone()[0] or 0

    current_day = int(datetime.today().strftime('%d'))
    days_in_month = monthrange(datetime.today().year, datetime.today().month)[1]
    days_left = days_in_month - current_day
    avg_daily_spending = round(monthly_expense / current_day, 2) if current_day > 0 else 0

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
    return render_template(
        'index.html',
        balance=balance,
        income=income,
        expense=expense,
        records=records,
        username=username,
        goal_amount=500,  # Example goal
        fullname=fullname,
        progress_percentage=min(int((balance / 500) * 100), 100),
        monthly_remaining=monthly_remaining,
        weekly_remaining=weekly_remaining,
        avg_daily_spending=avg_daily_spending,
        days_left=days_left
    )


@app.route('/set_goal', methods=['POST'])
def set_goal():
    """Update the user's goal amount and return progress."""
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.json
    new_goal = data.get('goal_amount')

    if not new_goal or float(new_goal) <= 0:
        return jsonify({"status": "error", "message": "Invalid goal amount"}), 400

    new_goal = float(new_goal)

    # Fetch user balance
    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT type, SUM(amount) FROM budgets WHERE username = ? GROUP BY type', (username,))
    budget_data = cursor.fetchall()
    conn.close()

    income = sum(amount for t, amount in budget_data if t == 'Income')
    expense = sum(amount for t, amount in budget_data if t == 'Expense')
    balance = income - expense

    # Calculate new progress percentage
    progress_percentage = min(int((balance / new_goal) * 100), 100)

    return jsonify({"status": "success", "goal_amount": new_goal, "progress_percentage": progress_percentage})


@app.route('/get_budget_data')
def get_budget_data():
    """Fetch financial data for the dashboard charts."""
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch income & expense totals
    cursor.execute('SELECT type, SUM(amount) FROM budgets WHERE username = ? GROUP BY type', (username,))
    budget_data = cursor.fetchall()

    income = sum(amount for t, amount in budget_data if t == 'Income')
    expense = sum(amount for t, amount in budget_data if t == 'Expense')
    balance = income - expense
    goal_amount = 500  # Example goal

    # Fetch category-wise expenses
    cursor.execute(
        'SELECT category, SUM(amount) FROM budgets WHERE username = ? AND type = "Expense" GROUP BY category',
        (username,))
    category_data = cursor.fetchall()

    categories = [row[0] for row in category_data]
    category_expenses = [row[1] for row in category_data]

    # Fetch monthly expense trend
    cursor.execute(
        'SELECT strftime("%Y-%m", date) AS month, SUM(amount) FROM budgets WHERE username = ? AND type = "Expense" GROUP BY month ORDER BY month',
        (username,))
    monthly_data = cursor.fetchall()
    monthly_expenses = {row[0]: row[1] for row in monthly_data}

    # Fetch all budget records for transactions table
    cursor.execute('SELECT type, category, amount, description, date FROM budgets WHERE username = ?', (username,))
    records = [
        {
            "type": row[0],
            "category": row[1],
            "amount": row[2],
            "description": row[3] if row[3] else "No description",
            "date": row[4]
        } for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify({
        "status": "success",
        "income": income,
        "expense": expense,
        "balance": balance,
        "goal_amount": goal_amount,
        "categories": categories,
        "category_expenses": category_expenses,
        "monthly_expenses": monthly_expenses,
        "records": records  # ✅ This was missing before
    })


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
        f"{user_message}\n"
        f"if {user_message} is asking that some thing like am i doing good/well?. Then response it based on {formatted_budget_data} with only maximum 3 sentences. Do not start with based on.\n\n"
        "Otherwise on {formatted_budget_data}, recommend a plan for better budget management. List only 3. For this case you can start with based on "
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
            return redirect(url_for('main'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration without password hashing."""
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        password = request.form['password']


        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, fullname,password) VALUES (?, ?)', (username, password,fullname))
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
    # init_db()
    app.run(debug=True)
