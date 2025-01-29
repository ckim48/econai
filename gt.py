from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
DATABASE = 'app.db'
def add_sample_data():
    """Insert extended sample data for high school student finance tracking (Jan - Dec 2024)."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    sample_data = [
        # ✅ Income Data - Allowance, Part-time Jobs, Gifts
        ('testtest', 'Allowance', 50, 'Income', '2024-01-05'),
        ('testtest', 'Part-time Job', 150, 'Income', '2024-02-10'),
        ('testtest', 'Allowance', 60, 'Income', '2024-03-05'),
        ('testtest', 'Birthday Gift', 100, 'Income', '2024-04-20'),
        ('testtest', 'Part-time Job', 200, 'Income', '2024-05-15'),
        ('testtest', 'Allowance', 70, 'Income', '2024-06-05'),
        ('testtest', 'Freelance Tutoring', 100, 'Income', '2024-07-12'),
        ('testtest', 'Allowance', 80, 'Income', '2024-08-05'),
        ('testtest', 'Summer Job', 250, 'Income', '2024-09-01'),
        ('testtest', 'Allowance', 90, 'Income', '2024-10-05'),
        ('testtest', 'Holiday Gift', 150, 'Income', '2024-11-25'),
        ('testtest', 'Allowance', 100, 'Income', '2024-12-05'),

        # ✅ Food Expenses - Fast Food, Snacks, School Lunch
        ('testtest', 'Fast Food', 15, 'Expense', '2024-01-15'),
        ('testtest', 'Snacks', 5, 'Expense', '2024-02-18'),
        ('testtest', 'School Lunch', 25, 'Expense', '2024-03-12'),
        ('testtest', 'Fast Food', 20, 'Expense', '2024-04-08'),
        ('testtest', 'Boba Tea', 10, 'Expense', '2024-05-22'),
        ('testtest', 'Fast Food', 18, 'Expense', '2024-06-30'),
        ('testtest', 'Snacks', 8, 'Expense', '2024-07-14'),
        ('testtest', 'School Lunch', 30, 'Expense', '2024-08-10'),
        ('testtest', 'Fast Food', 22, 'Expense', '2024-09-25'),
        ('testtest', 'Boba Tea', 12, 'Expense', '2024-10-16'),
        ('testtest', 'Snacks', 6, 'Expense', '2024-11-28'),
        ('testtest', 'Fast Food', 25, 'Expense', '2024-12-09'),

        # ✅ School Supplies - Books, Stationery
        ('testtest', 'Books', 50, 'Expense', '2024-01-10'),
        ('testtest', 'Notebooks', 20, 'Expense', '2024-02-05'),
        ('testtest', 'Pens & Pencils', 10, 'Expense', '2024-03-08'),
        ('testtest', 'Backpack', 70, 'Expense', '2024-04-02'),
        ('testtest', 'Calculator', 40, 'Expense', '2024-05-18'),
        ('testtest', 'Folders & Binders', 15, 'Expense', '2024-06-25'),
        ('testtest', 'Books', 55, 'Expense', '2024-07-09'),
        ('testtest', 'Stationery', 30, 'Expense', '2024-08-14'),
        ('testtest', 'Art Supplies', 20, 'Expense', '2024-09-30'),
        ('testtest', 'Notebooks', 25, 'Expense', '2024-10-22'),
        ('testtest', 'Backpack', 75, 'Expense', '2024-11-11'),
        ('testtest', 'Pens & Pencils', 12, 'Expense', '2024-12-20'),

        # ✅ Entertainment - Video Games, Movies, Subscriptions
        ('testtest', 'Movie Ticket', 15, 'Expense', '2024-01-20'),
        ('testtest', 'Gaming Subscription', 10, 'Expense', '2024-02-22'),
        ('testtest', 'Concert Ticket', 50, 'Expense', '2024-03-19'),
        ('testtest', 'Music Subscription', 10, 'Expense', '2024-04-25'),
        ('testtest', 'Movie Night', 20, 'Expense', '2024-05-29'),
        ('testtest', 'Gaming Console', 300, 'Expense', '2024-06-05'),
        ('testtest', 'Concert Ticket', 60, 'Expense', '2024-07-17'),
        ('testtest', 'Music Subscription', 10, 'Expense', '2024-08-21'),
        ('testtest', 'Movie Night', 25, 'Expense', '2024-09-10'),
        ('testtest', 'Gaming Subscription', 15, 'Expense', '2024-10-07'),
        ('testtest', 'Music Subscription', 10, 'Expense', '2024-11-18'),
        ('testtest', 'Concert Ticket', 70, 'Expense', '2024-12-23'),

        # ✅ Transportation - Bus, Uber
        ('testtest', 'Bus Fare', 10, 'Expense', '2024-01-08'),
        ('testtest', 'Uber Ride', 15, 'Expense', '2024-02-15'),
        ('testtest', 'Bus Pass', 30, 'Expense', '2024-03-20'),
        ('testtest', 'Bike Repair', 20, 'Expense', '2024-04-10'),
        ('testtest', 'Uber Ride', 18, 'Expense', '2024-05-14'),
        ('testtest', 'Bus Fare', 12, 'Expense', '2024-06-26'),
        ('testtest', 'Bus Pass', 35, 'Expense', '2024-07-11'),
        ('testtest', 'Uber Ride', 20, 'Expense', '2024-08-19'),
        ('testtest', 'Bike Maintenance', 25, 'Expense', '2024-09-04'),
        ('testtest', 'Bus Fare', 15, 'Expense', '2024-10-12'),
        ('testtest', 'Bus Pass', 40, 'Expense', '2024-11-30'),
        ('testtest', 'Uber Ride', 22, 'Expense', '2024-12-27'),

        # ✅ Miscellaneous - Gifts, Donations, Gym
        ('testtest', 'Gift for Friend', 25, 'Expense', '2024-01-30'),
        ('testtest', 'Donation', 10, 'Expense', '2024-02-24'),
        ('testtest', 'Gym Membership', 50, 'Expense', '2024-03-28'),
        ('testtest', 'Gift for Parent', 30, 'Expense', '2024-04-15'),
        ('testtest', 'Donation', 12, 'Expense', '2024-05-09'),
        ('testtest', 'Gym Membership', 55, 'Expense', '2024-06-13'),
        ('testtest', 'Gift for Friend', 20, 'Expense', '2024-07-26'),
        ('testtest', 'Donation', 15, 'Expense', '2024-08-31'),
        ('testtest', 'Gym Membership', 60, 'Expense', '2024-09-07'),
        ('testtest', 'Gift for Parent', 40, 'Expense', '2024-10-29'),
        ('testtest', 'Donation', 20, 'Expense', '2024-11-21'),
        ('testtest', 'Gym Membership', 65, 'Expense', '2024-12-14'),
    ]

    cursor.executemany('''
        INSERT INTO budgets (username, category, amount, type, date)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_data)
    conn.commit()
    conn.close()


add_sample_data()