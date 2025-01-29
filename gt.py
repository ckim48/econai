from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
DATABASE = 'app.db'
def add_sample_data():
    """Insert realistic sample data for student finance tracking (Dec 2024 - Jan 2025)."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    sample_data = [
        # Income Data (Part-time Job, Scholarship, Allowance)
        ('testtest', 'Part-time Job', 800, 'Income', '2024-12-01'),
        ('testtest', 'Scholarship', 1500, 'Income', '2024-12-15'),
        ('testtest', 'Allowance', 300, 'Income', '2024-12-20'),
        ('testtest', 'Part-time Job', 900, 'Income', '2025-01-01'),
        ('testtest', 'Scholarship', 1400, 'Income', '2025-01-10'),
        ('testtest', 'Allowance', 350, 'Income', '2025-01-20'),

        # Expense Data - Books & Stationery
        ('testtest', 'Books & Supplies', 150, 'Expense', '2024-12-05'),
        ('testtest', 'Books & Supplies', 200, 'Expense', '2025-01-12'),

        # Expense Data - Food
        ('testtest', 'Food', 300, 'Expense', '2024-12-03'),
        ('testtest', 'Food', 250, 'Expense', '2024-12-18'),
        ('testtest', 'Food', 280, 'Expense', '2025-01-05'),
        ('testtest', 'Food', 320, 'Expense', '2025-01-20'),

        # Expense Data - Transportation
        ('testtest', 'Transportation', 100, 'Expense', '2024-12-10'),
        ('testtest', 'Transportation', 120, 'Expense', '2025-01-08'),

        # Expense Data - Rent & Utilities
        ('testtest', 'Rent', 1200, 'Expense', '2024-12-01'),
        ('testtest', 'Rent', 1200, 'Expense', '2025-01-01'),
        ('testtest', 'Utilities', 150, 'Expense', '2024-12-07'),
        ('testtest', 'Utilities', 160, 'Expense', '2025-01-10'),

        # Expense Data - Entertainment
        ('testtest', 'Entertainment', 100, 'Expense', '2024-12-14'),
        ('testtest', 'Entertainment', 150, 'Expense', '2025-01-15'),

        # Expense Data - Shopping
        ('testtest', 'Shopping', 200, 'Expense', '2024-12-22'),
        ('testtest', 'Shopping', 180, 'Expense', '2025-01-25'),

        # Expense Data - Subscription Services
        ('testtest', 'Subscriptions', 50, 'Expense', '2024-12-05'),
        ('testtest', 'Subscriptions', 50, 'Expense', '2025-01-05'),

        # Expense Data - Healthcare
        ('testtest', 'Healthcare', 100, 'Expense', '2024-12-28'),
        ('testtest', 'Healthcare', 120, 'Expense', '2025-01-18'),
    ]

    cursor.executemany('''
        INSERT INTO budgets (username, category, amount, type, date)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_data)
    conn.commit()
    conn.close()

# Uncomment the line below to populate the database with updated sample data
# add_sample_data()


# Uncomment the following line to populate the database with sample data when running the app
# add_sample_data()

add_sample_data()