from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
DATABASE = 'app.db'
def add_sample_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Sample historical usage for user 'testtest'
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

# Uncomment the following line to populate the database with sample data when running the app
# add_sample_data()

add_sample_data()