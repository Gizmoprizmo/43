
from __future__ import annotations
import sqlite3, math, subprocess, os, shutil
from pathlib import Path
import datetime as dt
import openpyxl

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"

def initialize_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def _conn(db_path: Path):
    return sqlite3.connect(db_path)

def to_text(v):
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.isoformat(sep=" ")
    if isinstance(v, dt.date):
        return dt.datetime.combine(v, dt.time()).isoformat(sep=" ")
    if isinstance(v, float) and math.isnan(v):
        return None
    return str(v)

def as_number(v):
    if v is None:
        return None
    try:
        if isinstance(v, str):
            v = v.replace(",", ".").strip()
            if v == "":
                return None
        return float(v)
    except Exception:
        return None

def wb_rows(path: Path, sheet: str):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    return list(ws.iter_rows(values_only=True))

def convert_xls_if_needed(path: Path) -> Path:
    if path.suffix.lower() != ".xls":
        return path
    outdir = BASE_DIR / "instance" / "converted"
    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / (path.stem + ".xlsx")
    if target.exists():
        return target
    profile = BASE_DIR / "instance" / "lo_profile"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        "soffice",
        f"-env:UserInstallation=file://{profile}",
        "--headless",
        "--convert-to",
        "xlsx",
        "--outdir",
        str(outdir),
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return target

def log(conn, source_file, source_sheet, row_count, status="ok", note=None):
    conn.execute(
        "INSERT INTO import_log(source_file, source_sheet, row_count, status, note) VALUES(?,?,?,?,?)",
        (source_file, source_sheet, row_count, status, note),
    )

def clear_core(conn):
    for table in [
        "plants","customers","products","techcards","calendar_days",
        "portfolio_headers","portfolio_loading","portfolio_fact",
        "plans","labor_fact","warehouse_stock"
    ]:
        conn.execute(f"DELETE FROM {table}")

def import_reference_data(conn, source_dir: Path):
    path = source_dir / "ДанныеПроизводства.xlsm"
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл {path.name}")

    rows = wb_rows(path, "заводы")
    for r in rows[1:]:
        code, name, location = r[0], r[1], r[2]
        base_unit = r[8] if len(r) > 8 else None
        if code is None and name is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO plants(code,name,location,base_unit) VALUES(?,?,?,?)",
            (to_text(code), to_text(name), to_text(location), to_text(base_unit)),
        )
    log(conn, path.name, "заводы", len(rows)-1)

    rows = wb_rows(path, "заказчики")
    for r in rows[1:]:
        name, counterparty, location, contacts = r[:4]
        if name is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO customers(name,counterparty,location,contacts) VALUES(?,?,?,?)",
            (to_text(name), to_text(counterparty), to_text(location), to_text(contacts)),
        )
    log(conn, path.name, "заказчики", len(rows)-1)

    rows = wb_rows(path, "Изделия")
    for r in rows[1:]:
        if r[0] is None:
            continue
        sap, name, purpose, unit, plant, wspec, wcoef, wdraw, price, note, ptype, group_name, psp, idx = r[:14]
        conn.execute("""
            INSERT OR IGNORE INTO products
            (sap,plant_code,name,purpose,unit,weight_spec,weight_coeff,weight_drawing,price,note,prod_type,group_name,psp,idx)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            to_text(sap), to_text(plant), to_text(name), to_text(purpose), to_text(unit),
            as_number(wspec), as_number(wcoef), as_number(wdraw), as_number(price),
            to_text(note), to_text(ptype), to_text(group_name), to_text(psp), to_text(idx)
        ))
    log(conn, path.name, "Изделия", len(rows)-1)

    rows = wb_rows(path, "техкарты")
    for r in rows[1:]:
        if r[0] is None:
            continue
        plant, material, material_name, base_unit, wc, wc_name, bqty, vunit, std, stdunit, idx = r[:11]
        conn.execute("""
            INSERT INTO techcards
            (plant_code,material,material_name,base_unit,work_center,work_center_name,base_qty,view_unit,standard_value,standard_value_unit,idx)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            to_text(plant), to_text(material), to_text(material_name), to_text(base_unit),
            to_text(wc), to_text(wc_name), as_number(bqty), to_text(vunit),
            as_number(std), to_text(stdunit), to_text(idx)
        ))
    log(conn, path.name, "техкарты", len(rows)-1)

    rows = wb_rows(path, "календарь")
    for r in rows[1:]:
        if all(v is None for v in r[:7]):
            continue
        period_key, month_num, date_value, year_num, work_days, work_hours, non_working = r[:7]
        conn.execute("""
            INSERT INTO calendar_days(period_key,month_num,date_value,year_num,work_days,work_hours,non_working)
            VALUES(?,?,?,?,?,?,?)
        """, (
            to_text(period_key),
            int(month_num) if month_num is not None else None,
            to_text(date_value),
            int(year_num) if year_num is not None else None,
            as_number(work_days),
            as_number(work_hours),
            to_text(non_working)
        ))
    log(conn, path.name, "календарь", len(rows)-1)

def import_portfolio(conn, source_dir: Path):
    path = source_dir / "ПОРТФЕЛЬ ЗАКАЗОВ 3.2.xlsm"
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл {path.name}")

    rows = wb_rows(path, "Заголовки")
    for r in rows[1:]:
        if r[0] is None and r[1] is None:
            continue
        vals = list(r[:18]) + [None] * max(0, 18-len(r[:18]))
        conn.execute("""
            INSERT INTO portfolio_headers
            (plant_code,customer_name,order_no,reg_no,reg_date,planning_variant,input_date,material,material_name,qty_plan,plan_hours,extra_info,due_variant,due_plan,due_fact,status,shipped,note)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            to_text(vals[0]), to_text(vals[1]), to_text(vals[2]), to_text(vals[3]), to_text(vals[4]),
            to_text(vals[5]), to_text(vals[6]), to_text(vals[7]), to_text(vals[8]),
            as_number(vals[9]), as_number(vals[10]), to_text(vals[11]), to_text(vals[12]),
            to_text(vals[13]), to_text(vals[14]), to_text(vals[15]), as_number(vals[16]), to_text(vals[17])
        ))
    log(conn, path.name, "Заголовки", len(rows)-1)

    rows = wb_rows(path, "загрузка")
    for r in rows[3:]:
        if len(r) < 13 or (r[1] is None and r[2] is None):
            continue
        plant, customer, material, variant, mname, basis, qty, need_date, order_no, input_date, year_num, agreed_date = r[1:13]
        conn.execute("""
            INSERT INTO portfolio_loading
            (plant_code,customer_name,material,planning_variant,material_name,basis,qty,need_date,order_no,input_date,year_num,agreed_date)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            to_text(plant), to_text(customer), to_text(material), to_text(variant),
            to_text(mname), to_text(basis), as_number(qty), to_text(need_date),
            to_text(order_no), to_text(input_date),
            int(year_num) if year_num is not None and str(year_num).isdigit() else None,
            to_text(agreed_date)
        ))
    log(conn, path.name, "загрузка", len(rows)-3)

    rows = wb_rows(path, "факт")
    for r in rows[4:]:
        if len(r) < 10 or (r[1] is None and r[2] is None):
            continue
        date_val, plant, order_no, reg_no, material, mname, qty, hours, note = r[1:10]
        conn.execute("""
            INSERT INTO portfolio_fact
            (date_value,plant_code,order_no,reg_no,material,material_name,qty_fact,hours_fact,note)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            to_text(date_val), to_text(plant), to_text(order_no), to_text(reg_no),
            to_text(material), to_text(mname), as_number(qty), as_number(hours), to_text(note)
        ))
    log(conn, path.name, "факт", len(rows)-4)

def import_plans(conn, source_dir: Path):
    path = source_dir / "Планирование производства ПМЗv4.4.xlsm"
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл {path.name}")

    rows = wb_rows(path, "план")
    for r in rows[1:]:
        if r[0] is None:
            continue
        vals = list(r[:15]) + [None] * max(0, 15-len(r[:15]))
        conn.execute("""
            INSERT INTO plans
            (year_num,month_num,order_no,plant_code,material,material_name,unit,plan_qty,plan_mod,fact_qty,work_center_name,norm_accounting,work_center_no,mod_hours,fact_hours)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            int(vals[0]) if vals[0] is not None else None,
            int(vals[1]) if vals[1] is not None else None,
            to_text(vals[2]), to_text(vals[3]), to_text(vals[4]), to_text(vals[5]), to_text(vals[6]),
            as_number(vals[7]), as_number(vals[8]), as_number(vals[9]), to_text(vals[10]), to_text(vals[11]), to_text(vals[12]),
            as_number(vals[13]), as_number(vals[14])
        ))
    log(conn, path.name, "план", len(rows)-1)

def import_labor(conn, source_dir: Path):
    # факт_труд.xlsx
    path = source_dir / "факт_труд.xlsx"
    if path.exists():
        rows = wb_rows(path, "Sheet1")
        for r in rows[1:]:
            if r[0] is None:
                continue
            vals = list(r[:15]) + [None] * max(0, 15-len(r[:15]))
            conn.execute("""
                INSERT INTO labor_fact
                (order_no,planner,material,material_name,plant_code,start_date,end_date,planned_qty,base_unit,workshop_name,work_center,work_center_name,fact_hours,year_num,month_num,source_tag)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                to_text(vals[0]), to_text(vals[1]), to_text(vals[2]), to_text(vals[3]), to_text(vals[4]),
                to_text(vals[5]), to_text(vals[6]), as_number(vals[7]), to_text(vals[8]), to_text(vals[9]),
                to_text(vals[10]), to_text(vals[11]), as_number(vals[12]),
                int(vals[13]) if vals[13] is not None else None,
                int(vals[14]) if vals[14] is not None else None,
                "факт_труд"
            ))
        log(conn, path.name, "Sheet1", len(rows)-1)

    # факт_31032026.XLS -> try convert
    path = source_dir / "факт_31032026.XLS"
    if path.exists():
        xlsx = convert_xls_if_needed(path)
        rows = wb_rows(xlsx, "Sheet1")
        for r in rows[1:]:
            if r[0] is None:
                continue
            conn.execute("""
                INSERT INTO labor_fact
                (order_no,planner,material,material_name,plant_code,start_date,end_date,planned_qty,base_unit,workshop_name,work_center,work_center_name,fact_hours,source_tag)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                to_text(r[0]), to_text(r[1]), to_text(r[2]), to_text(r[3]), to_text(r[4]),
                to_text(r[5]), to_text(r[6]), as_number(r[7]), to_text(r[8]), to_text(r[9]), to_text(r[10]),
                to_text(r[11]), as_number(r[12]), "факт_31032026"
            ))
        log(conn, path.name, "Sheet1", len(rows)-1)

def import_warehouse(conn, source_dir: Path):
    path = source_dir / "склады.XLS"
    if not path.exists():
        return
    xlsx = convert_xls_if_needed(path)
    rows = wb_rows(xlsx, "Sheet1")
    for r in rows[1:]:
        if r[0] is None:
            continue
        vals = list(r[:15]) + [None] * max(0, 15-len(r[:15]))
        conn.execute("""
            INSERT INTO warehouse_stock
            (plant_code,warehouse,material,material_name,location,atz_batch,base_unit,free_stock,free_stock_value,valuation_type,batch,cost_center,cost_center_name,special_stock_no,special_stock)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            to_text(vals[0]), to_text(vals[1]), to_text(vals[2]), to_text(vals[3]), to_text(vals[4]), to_text(vals[5]),
            to_text(vals[6]), as_number(vals[7]), as_number(vals[8]), to_text(vals[9]), to_text(vals[10]),
            to_text(vals[11]), to_text(vals[12]), to_text(vals[13]), to_text(vals[14])
        ))
    log(conn, path.name, "Sheet1", len(rows)-1)

def import_all_default_files(db_path: Path, source_dir: Path):
    conn = _conn(db_path)
    report = []
    try:
        clear_core(conn)
        import_reference_data(conn, source_dir)
        import_portfolio(conn, source_dir)
        import_plans(conn, source_dir)
        import_labor(conn, source_dir)
        import_warehouse(conn, source_dir)
        conn.commit()
        for table in ["plants","customers","products","techcards","calendar_days","portfolio_headers","portfolio_loading","portfolio_fact","plans","labor_fact","warehouse_stock"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            report.append((table, count))
        return report
    finally:
        conn.close()
