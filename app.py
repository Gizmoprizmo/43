
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from import_service import initialize_db, import_all_default_files

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = "unified-mvp-secret"

@app.route("/")
def index():
    conn = get_conn()
    counts = {}
    for table in [
        "plants", "customers", "products", "techcards",
        "portfolio_headers", "portfolio_loading", "portfolio_fact",
        "plans", "labor_fact", "warehouse_stock"
    ]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    latest = conn.execute("SELECT * FROM import_log ORDER BY imported_at DESC, id DESC LIMIT 20").fetchall()
    conn.close()
    return render_template("index.html", counts=counts, latest=latest)

@app.route("/import", methods=["GET", "POST"])
def import_data():
    if request.method == "POST":
        source_dir = request.form.get("source_dir", "").strip()
        if not source_dir:
            flash("Укажи папку с Excel-файлами.", "danger")
            return redirect(url_for("import_data"))
        try:
            initialize_db(DB_PATH)
            report = import_all_default_files(DB_PATH, Path(source_dir))
            flash("Импорт завершён.", "success")
            return render_template("import_result.html", report=report, source_dir=source_dir)
        except Exception as e:
            flash(f"Ошибка импорта: {e}", "danger")
            return redirect(url_for("import_data"))
    return render_template("import.html", db_path=str(DB_PATH))

@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM products
            WHERE sap LIKE ? OR name LIKE ? OR idx LIKE ? OR plant_code LIKE ?
            ORDER BY name
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY name LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Изделия", rows=rows, q=q)

@app.route("/techcards")
def techcards():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM techcards
            WHERE material LIKE ? OR material_name LIKE ? OR idx LIKE ? OR work_center_name LIKE ?
            ORDER BY material_name
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM techcards ORDER BY material_name LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Техкарты", rows=rows, q=q)

@app.route("/portfolio")
def portfolio():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM portfolio_headers
            WHERE order_no LIKE ? OR material LIKE ? OR material_name LIKE ? OR customer_name LIKE ?
            ORDER BY reg_date DESC
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM portfolio_headers ORDER BY reg_date DESC LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Портфель заказов", rows=rows, q=q)

@app.route("/plans")
def plans():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM plans
            WHERE order_no LIKE ? OR material LIKE ? OR material_name LIKE ?
            ORDER BY year_num DESC, month_num DESC
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM plans ORDER BY year_num DESC, month_num DESC LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Планирование", rows=rows, q=q)

@app.route("/labor")
def labor():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM labor_fact
            WHERE order_no LIKE ? OR material LIKE ? OR material_name LIKE ? OR work_center_name LIKE ?
            ORDER BY year_num DESC, month_num DESC
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM labor_fact ORDER BY year_num DESC, month_num DESC LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Факт / труд", rows=rows, q=q)

@app.route("/warehouse")
def warehouse():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    if q:
        rows = conn.execute("""
            SELECT * FROM warehouse_stock
            WHERE material LIKE ? OR material_name LIKE ? OR plant_code LIKE ? OR warehouse LIKE ?
            ORDER BY material_name
            LIMIT 500
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM warehouse_stock ORDER BY material_name LIMIT 500").fetchall()
    conn.close()
    return render_template("table.html", title="Склады", rows=rows, q=q)

if __name__ == "__main__":
    initialize_db(DB_PATH)
    app.run(debug=True)
