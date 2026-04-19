# 💰 FinTrack — Expense Tracker & Insights Dashboard

A full-stack personal finance web application built with Python (Flask), SQLite, Bootstrap 5, and Chart.js.

Video Demo: https://youtu.be/NRKSxGpdSk0


---

## 📁 Project Structure

```
expense_tracker/
├── app.py                    # Main Flask application (routes, DB, logic)
├── requirements.txt          # Python dependencies
├── expense_tracker.db        # SQLite database (auto-created on first run)
├── README.md
└── templates/
    ├── base.html             # Shared layout with sidebar navigation
    ├── login.html            # Login page
    ├── register.html         # Registration page
    ├── dashboard.html        # Main dashboard with charts
    ├── transactions.html     # Transaction list with filters
    ├── add_transaction.html  # Add income/expense form
    └── insights.html        # Smart insights & analytics
```

---

## 🚀 Setup & Run

### 1. Prerequisites
- Python 3.8 or newer
- pip

### 2. Install dependencies
```bash
cd expense_tracker
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

Register a new account and start tracking!

---

## ✅ Features

### Core Features
| Feature | Description |
|---|---|
| User Auth | Register, Login, Logout with SHA-256 password hashing |
| Add Transactions | Income & Expense with categories, amount, date, description |
| Categories | 12 expense + 6 income predefined categories |
| Transaction History | Full list with serial number, date, type, category, amount |
| Filters | Filter by type, category, date range |
| Dashboard Stats | Total Balance, Total Income, Total Expenses |

### Advanced Features
| Feature | Description |
|---|---|
| Category Pie Chart | Doughnut chart showing expense breakdown by category |
| Monthly Bar Chart | Side-by-side income vs expense for last 6 months |
| Expense Trend Line | Monthly expense trend over time (line chart) |
| Smart Insights | Auto-generated tips like "You spent 40% on Food" |
| Month Comparison | This month vs last month spending with % change |
| Spending % Breakdown | Progress bars showing each category's share |
| Filtered Totals | Running income/expense/net totals for filtered view |

---

## 🛠️ Technical Details

### Backend (Flask)
- `Flask` for routing and templating
- `sqlite3` with parameterized queries (SQL injection safe)
- Session-based authentication with `@login_required` decorator
- REST API endpoints (`/api/*`) that return JSON for Chart.js

### Database Schema

**users**
```sql
id, username (UNIQUE), email (UNIQUE), password (SHA-256), created_at
```

**transactions**
```sql
id, user_id (FK), type (income/expense), amount, category, description, date, created_at
```

### Key SQL Queries Used
- `SUM()` + `CASE WHEN` for conditional totals
- `GROUP BY category` for category breakdown
- `strftime('%Y-%m', date)` for monthly grouping
- `WHERE date >= date('now', '-6 months')` for recent data

### Frontend
- Bootstrap 5.3 for responsive grid
- Chart.js 4 for all charts
- Vanilla JavaScript `fetch()` for async API calls
- CSS custom properties (variables) for consistent theming

---

## 🎨 Design

Dark luxury theme with:
- **Fonts**: Playfair Display (headings) + DM Sans (body)
- **Colors**: Deep navy background, warm gold accents, mint green for income, red for expenses
- **Components**: Glass-morphism cards, custom dark tables, sidebar navigation

---

## 📝 Notes

- Database is auto-created on first run
- Password stored as SHA-256 hash (use bcrypt in production)
- `app.secret_key` should be changed to a random value in production
- All transactions are user-scoped (users can only see their own data)

---

## 👨‍💻 Built With

- Python + Flask
- SQLite3
- HTML5 + CSS3 + JavaScript (ES6)
- Bootstrap 5.3
- Chart.js 4
- Bootstrap Icons
- Google Fonts
