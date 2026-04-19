"""
Expense Tracker - Main Flask Application
Handles all routes, authentication, and database operations
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'expense_tracker_secret_key_2024'  # Change in production!

DATABASE = 'expense_tracker.db'

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    """Connect to SQLite database"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Makes rows behave like dicts
    return conn

def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Transactions table (stores both income and expenses)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password):
    """Simple SHA-256 password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

# ─────────────────────────────────────────────
# AUTH DECORATOR
# ─────────────────────────────────────────────

def login_required(f):
    """Redirect to login if user not in session"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hash_password(password))
            )
            conn.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db()

    # Total income, expenses, balance
    totals = conn.execute('''
        SELECT
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expenses
        FROM transactions WHERE user_id = ?
    ''', (user_id,)).fetchone()

    total_income = totals['total_income'] or 0
    total_expenses = totals['total_expenses'] or 0
    balance = total_income - total_expenses

    # Recent 5 transactions
    recent = conn.execute('''
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('dashboard.html',
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        recent=recent,
        username=session['username']
    )

# ─────────────────────────────────────────────
# TRANSACTIONS CRUD
# ─────────────────────────────────────────────

@app.route('/transactions', methods=['GET'])
@login_required
def transactions():
    user_id = session['user_id']
    # Get filters from query string
    filter_type = request.args.get('type', 'all')
    filter_category = request.args.get('category', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conn = get_db()

    # Build dynamic SQL query with filters
    query = 'SELECT * FROM transactions WHERE user_id = ?'
    params = [user_id]

    if filter_type != 'all':
        query += ' AND type = ?'
        params.append(filter_type)

    if filter_category != 'all':
        query += ' AND category = ?'
        params.append(filter_category)

    if date_from:
        query += ' AND date >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND date <= ?'
        params.append(date_to)

    query += ' ORDER BY date DESC, created_at DESC'

    txns = conn.execute(query, params).fetchall()

    # Get all unique categories for filter dropdown
    categories = conn.execute(
        'SELECT DISTINCT category FROM transactions WHERE user_id = ? ORDER BY category',
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template('transactions.html',
        transactions=txns,
        categories=categories,
        filter_type=filter_type,
        filter_category=filter_category,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        user_id = session['user_id']
        txn_type = request.form['type']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form.get('description', '')
        date = request.form['date']

        conn = get_db()
        conn.execute('''
            INSERT INTO transactions (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, txn_type, amount, category, description, date))
        conn.commit()
        conn.close()

        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions'))

    # Pre-fill today's date
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('add_transaction.html', today=today)

@app.route('/delete_transaction/<int:txn_id>', methods=['POST'])
@login_required
def delete_transaction(txn_id):
    conn = get_db()
    # Only delete if it belongs to the logged-in user
    conn.execute(
        'DELETE FROM transactions WHERE id = ? AND user_id = ?',
        (txn_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    flash('Transaction deleted.', 'success')
    return redirect(url_for('transactions'))

# ─────────────────────────────────────────────
# INSIGHTS PAGE
# ─────────────────────────────────────────────

@app.route('/insights')
@login_required
def insights():
    return render_template('insights.html', username=session['username'])

# ─────────────────────────────────────────────
# API ENDPOINTS (used by Chart.js via JS fetch)
# ─────────────────────────────────────────────

@app.route('/api/category_spending')
@login_required
def api_category_spending():
    """Returns expense totals grouped by category"""
    user_id = session['user_id']
    conn = get_db()
    rows = conn.execute('''
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ? AND type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id,)).fetchall()
    conn.close()

    data = {
        'labels': [r['category'] for r in rows],
        'values': [r['total'] for r in rows]
    }
    return jsonify(data)

@app.route('/api/monthly_trends')
@login_required
def api_monthly_trends():
    """Returns monthly income vs expense for last 6 months"""
    user_id = session['user_id']
    conn = get_db()

    rows = conn.execute('''
        SELECT
            strftime('%Y-%m', date) AS month,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
        FROM transactions
        WHERE user_id = ?
          AND date >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    ''', (user_id,)).fetchall()
    conn.close()

    data = {
        'labels': [r['month'] for r in rows],
        'income': [r['income'] for r in rows],
        'expense': [r['expense'] for r in rows]
    }
    return jsonify(data)

@app.route('/api/insights_data')
@login_required
def api_insights_data():
    """Returns smart insights: percentages, top category, etc."""
    user_id = session['user_id']
    conn = get_db()

    # Total expenses
    total_expense = conn.execute(
        "SELECT SUM(amount) AS t FROM transactions WHERE user_id=? AND type='expense'",
        (user_id,)
    ).fetchone()['t'] or 0

    # Category breakdown
    cats = conn.execute('''
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ? AND type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id,)).fetchall()

    insights = []
    if total_expense > 0:
        for cat in cats:
            pct = round((cat['total'] / total_expense) * 100, 1)
            insights.append({
                'category': cat['category'],
                'amount': cat['total'],
                'percentage': pct
            })

    # This month vs last month
    this_month = conn.execute('''
        SELECT SUM(amount) AS t FROM transactions
        WHERE user_id=? AND type='expense'
          AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    ''', (user_id,)).fetchone()['t'] or 0

    last_month = conn.execute('''
        SELECT SUM(amount) AS t FROM transactions
        WHERE user_id=? AND type='expense'
          AND strftime('%Y-%m', date) = strftime('%Y-%m', date('now', '-1 month'))
    ''', (user_id,)).fetchone()['t'] or 0

    conn.close()

    return jsonify({
        'insights': insights,
        'this_month': this_month,
        'last_month': last_month,
        'total_expense': total_expense
    })

# ─────────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
