from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from datetime import date, datetime
import os
from dotenv import load_dotenv

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)



load_dotenv()  # Load variables from .env

# Create DB config from env variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ---------- Utility ----------
def compute_aging_bucket(due_date, today=date.today()):
    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    if due_date >= today:
        return "Current"
    days = (today - due_date).days
    if 0 <= days <= 30:
        return "0-30"
    elif 31 <= days <= 60:
        return "31-60"
    elif 61 <= days <= 90:
        return "61-90"
    else:
        return "90+"

# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("index.html")

# Get customers for filter dropdown
@app.route("/customers")
def customers():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT customer_id, name FROM customers ORDER BY name;")
    rows = cur.fetchall()
    cur.close(); db.close()
    return jsonify(rows)

# Invoices with totals, outstanding and aging; supports filters
@app.route("/invoices")
def invoices():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("start_date")
    end_date   = request.args.get("end_date")

    filters = []
    params = []
    if customer_id:
        filters.append("i.customer_id = %s")
        params.append(customer_id)
    if start_date:
        filters.append("i.invoice_date >= %s")
        params.append(start_date)
    if end_date:
        filters.append("i.invoice_date <= %s")
        params.append(end_date)

    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f'''
    SELECT i.invoice_id,
           c.name AS customer_name,
           i.amount,
           IFNULL(SUM(p.amount), 0) AS total_paid,
           GREATEST(i.amount - IFNULL(SUM(p.amount), 0), 0) AS outstanding,
           i.invoice_date,
           i.due_date
    FROM invoices i
    JOIN customers c ON i.customer_id = c.customer_id
    LEFT JOIN payments p ON i.invoice_id = p.invoice_id
    {where_clause}
    GROUP BY i.invoice_id, c.name, i.amount, i.invoice_date, i.due_date
    ORDER BY i.invoice_date DESC, i.invoice_id DESC;
    '''

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    # compute aging on server to ensure correctness
    today = date.today()
    for r in rows:
        r["aging_bucket"] = compute_aging_bucket(r["due_date"], today) if r["outstanding"] > 0 else "Current"
    cur.close(); db.close()
    return jsonify(rows)

# KPI summary
@app.route("/kpis")
def kpis():
    # optional same filters
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("start_date")
    end_date   = request.args.get("end_date")

    filters = []
    params = []
    if customer_id:
        filters.append("i.customer_id = %s"); params.append(customer_id)
    if start_date:
        filters.append("i.invoice_date >= %s"); params.append(start_date)
    if end_date:
        filters.append("i.invoice_date <= %s"); params.append(end_date)
    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Total invoiced
    cur.execute(f"SELECT IFNULL(SUM(i.amount),0) AS total_invoiced FROM invoices i {where_clause};", params)
    total_invoiced = cur.fetchone()["total_invoiced"]

    # Total received
    cur.execute(f'''
        SELECT IFNULL(SUM(p.amount),0) AS total_received
        FROM payments p
        JOIN invoices i ON i.invoice_id = p.invoice_id
        {where_clause};
    ''', params)
    total_received = cur.fetchone()["total_received"]

    # Total outstanding (sum per invoice of (amount - paid), floored at 0)
    cur.execute(f'''
        SELECT IFNULL(SUM(GREATEST(i.amount - IFNULL(tp.total_paid,0),0)),0) AS total_outstanding
        FROM invoices i
        LEFT JOIN (
            SELECT invoice_id, SUM(amount) AS total_paid
            FROM payments GROUP BY invoice_id
        ) tp ON tp.invoice_id = i.invoice_id
        {where_clause};
    ''', params)
    total_outstanding = cur.fetchone()["total_outstanding"]

    # Overdue outstanding only (unpaid portion where due_date < today)
    cur.execute(f'''
        SELECT IFNULL(SUM(
            CASE WHEN i.due_date < CURDATE() THEN GREATEST(i.amount - IFNULL(tp.total_paid,0),0) ELSE 0 END
        ),0) AS overdue_outstanding
        FROM invoices i
        LEFT JOIN (
            SELECT invoice_id, SUM(amount) AS total_paid
            FROM payments GROUP BY invoice_id
        ) tp ON tp.invoice_id = i.invoice_id
        {where_clause};
    ''', params)
    overdue_outstanding = cur.fetchone()["overdue_outstanding"]

    percent_overdue = (float(overdue_outstanding) / float(total_outstanding) * 100.0) if float(total_outstanding) > 0 else 0.0

    cur.close(); db.close()
    return jsonify(dict(
        total_invoiced=float(total_invoiced),
        total_received=float(total_received),
        total_outstanding=float(total_outstanding),
        overdue_outstanding=float(overdue_outstanding),
        percent_overdue=round(percent_overdue,2)
    ))

# Record a payment (parameterized)
@app.route("/payments", methods=["POST"])
def add_payment():
    data = request.get_json(force=True)
    invoice_id = data.get("invoice_id")
    payment_date = data.get("payment_date")
    amount = data.get("amount")

    if not all([invoice_id, payment_date, amount]):
        return jsonify({"error":"invoice_id, payment_date, amount required"}), 400

    db = get_db()
    cur = db.cursor()

    # Optional: Basic guard to prevent overpayment (can be removed if not desired)
    cur.execute('''
        SELECT i.amount - IFNULL(SUM(p.amount),0) AS outstanding
        FROM invoices i LEFT JOIN payments p ON i.invoice_id = p.invoice_id
        WHERE i.invoice_id = %s GROUP BY i.invoice_id;
    ''', (invoice_id,))
    row = cur.fetchone()
    if row is None:
        cur.close(); db.close()
        return jsonify({"error":"Invoice not found"}), 404
    outstanding = float(row[0])
    if float(amount) <= 0:
        cur.close(); db.close()
        return jsonify({"error":"Amount must be > 0"}), 400

    cur.execute("INSERT INTO payments (invoice_id, payment_date, amount) VALUES (%s,%s,%s)",
                (invoice_id, payment_date, amount))
    db.commit()
    cur.close(); db.close()
    return jsonify({"message":"Payment recorded"})

# Top 5 customers by total outstanding
@app.route("/top5")
def top5():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute('''
        SELECT c.customer_id, c.name,
               SUM(GREATEST(i.amount - IFNULL(tp.total_paid,0),0)) AS total_outstanding
        FROM customers c
        JOIN invoices i ON c.customer_id = i.customer_id
        LEFT JOIN (
            SELECT invoice_id, SUM(amount) AS total_paid
            FROM payments GROUP BY invoice_id
        ) tp ON tp.invoice_id = i.invoice_id
        GROUP BY c.customer_id, c.name
        ORDER BY total_outstanding DESC
        LIMIT 5;
    ''')
    rows = cur.fetchall()
    cur.close(); db.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
