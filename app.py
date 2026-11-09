import os
import sqlite3
import csv
import io
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, Response, g

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-for-production")
DATABASE = os.environ.get("DATABASE_PATH", "smartspend.db")

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Education", "Entertainment", "Other"]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
                category TEXT NOT NULL,
                txn_date TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
        """)
        db.commit()

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, today=date.today().isoformat())

@app.get("/api/transactions")
def list_transactions():
    rows = get_db().execute(
        "SELECT * FROM transactions ORDER BY txn_date DESC, id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/transactions")
def add_transaction():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    kind = data.get("kind")
    category = data.get("category", "Other")
    txn_date = data.get("txn_date")
    note = str(data.get("note", "")).strip()
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify(error="Enter a valid amount."), 400
    if not title or kind not in ("income", "expense") or amount <= 0 or not txn_date:
        return jsonify(error="Please provide a title, positive amount, type and date."), 400
    try:
        datetime.strptime(txn_date, "%Y-%m-%d")
    except ValueError:
        return jsonify(error="Date must use YYYY-MM-DD format."), 400
    if category not in CATEGORIES:
        category = "Other"
    cur = get_db().execute(
        "INSERT INTO transactions(title, amount, kind, category, txn_date, note) VALUES (?, ?, ?, ?, ?, ?)",
        (title, amount, kind, category, txn_date, note)
    )
    get_db().commit()
    row = get_db().execute("SELECT * FROM transactions WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.put("/api/transactions/<int:txn_id>")
def update_transaction(txn_id):
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    kind = data.get("kind")
    category = data.get("category", "Other")
    txn_date = data.get("txn_date")
    note = str(data.get("note", "")).strip()
    try:
        amount = float(data.get("amount", 0))
        datetime.strptime(txn_date, "%Y-%m-%d")
    except (TypeError, ValueError):
        return jsonify(error="Enter a valid amount and date."), 400
    if not title or kind not in ("income", "expense") or amount <= 0:
        return jsonify(error="Please complete all required fields."), 400
    if category not in CATEGORIES:
        category = "Other"
    cur = get_db().execute(
        """UPDATE transactions SET title=?, amount=?, kind=?, category=?, txn_date=?, note=?
           WHERE id=?""",
        (title, amount, kind, category, txn_date, note, txn_id)
    )
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify(error="Transaction not found."), 404
    row = get_db().execute("SELECT * FROM transactions WHERE id=?", (txn_id,)).fetchone()
    return jsonify(dict(row))

@app.delete("/api/transactions/<int:txn_id>")
def delete_transaction(txn_id):
    cur = get_db().execute("DELETE FROM transactions WHERE id=?", (txn_id,))
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify(error="Transaction not found."), 404
    return jsonify(ok=True)

@app.get("/api/summary")
def summary():
    rows = get_db().execute("SELECT kind, amount, category, txn_date FROM transactions").fetchall()
    income = sum(r["amount"] for r in rows if r["kind"] == "income")
    expenses = sum(r["amount"] for r in rows if r["kind"] == "expense")
    month = date.today().strftime("%Y-%m")
    month_expenses = sum(r["amount"] for r in rows if r["kind"] == "expense" and r["txn_date"].startswith(month))
    by_category = {}
    for r in rows:
        if r["kind"] == "expense":
            by_category[r["category"]] = by_category.get(r["category"], 0) + r["amount"]
    return jsonify(income=income, expenses=expenses, balance=income-expenses,
                   month_expenses=month_expenses, by_category=by_category)

@app.get("/api/insights")
def insights():
    rows = get_db().execute(
        "SELECT amount, category, txn_date FROM transactions WHERE kind='expense'"
    ).fetchall()
    if not rows:
        return jsonify(["Add a few expenses to receive spending insights."])
    total = sum(r["amount"] for r in rows)
    by_cat = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["amount"]
    top_cat, top_amount = max(by_cat.items(), key=lambda item: item[1])
    insights_list = [f"{top_cat} is your highest-spending category at ₹{top_amount:,.2f} ({top_amount/total:.0%} of recorded expenses)."]
    month = date.today().strftime("%Y-%m")
    this_month = sum(r["amount"] for r in rows if r["txn_date"].startswith(month))
    if this_month:
        insights_list.append(f"You have recorded ₹{this_month:,.2f} in expenses this month.")
    if len(rows) >= 5:
        average = total / len(rows)
        insights_list.append(f"Your average recorded expense is ₹{average:,.2f}.")
    if top_amount / total >= 0.5:
        insights_list.append(f"More than half of your spending is in {top_cat}. Review this category for possible savings.")
    else:
        insights_list.append("Your spending is spread across multiple categories. Set category-wise limits to stay on track.")
    return jsonify(insights_list)

@app.get("/export.csv")
def export_csv():
    rows = get_db().execute(
        "SELECT txn_date, title, kind, category, amount, note FROM transactions ORDER BY txn_date DESC"
    ).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Title", "Type", "Category", "Amount_INR", "Note"])
    for row in rows:
        writer.writerow(list(row))
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=smartspend-transactions.csv"})

init_db()

if __name__ == "__main__":
    app.run(debug=True)
