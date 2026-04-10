
PRAGMA foreign_keys=OFF;

CREATE TABLE IF NOT EXISTS plants(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT,
    location TEXT,
    base_unit TEXT
);

CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    counterparty TEXT,
    location TEXT,
    contacts TEXT
);

CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sap TEXT,
    plant_code TEXT,
    name TEXT,
    purpose TEXT,
    unit TEXT,
    weight_spec REAL,
    weight_coeff REAL,
    weight_drawing REAL,
    price REAL,
    note TEXT,
    prod_type TEXT,
    group_name TEXT,
    psp TEXT,
    idx TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS techcards(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_code TEXT,
    material TEXT,
    material_name TEXT,
    base_unit TEXT,
    work_center TEXT,
    work_center_name TEXT,
    base_qty REAL,
    view_unit TEXT,
    standard_value REAL,
    standard_value_unit TEXT,
    idx TEXT
);

CREATE INDEX IF NOT EXISTS idx_techcards_idx ON techcards(idx);
CREATE INDEX IF NOT EXISTS idx_products_idx ON products(idx);

CREATE TABLE IF NOT EXISTS calendar_days(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_key TEXT,
    month_num INTEGER,
    date_value TEXT,
    year_num INTEGER,
    work_days REAL,
    work_hours REAL,
    non_working TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_headers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_code TEXT,
    customer_name TEXT,
    order_no TEXT,
    reg_no TEXT,
    reg_date TEXT,
    planning_variant TEXT,
    input_date TEXT,
    material TEXT,
    material_name TEXT,
    qty_plan REAL,
    plan_hours REAL,
    extra_info TEXT,
    due_variant TEXT,
    due_plan TEXT,
    due_fact TEXT,
    status TEXT,
    shipped REAL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_loading(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_code TEXT,
    customer_name TEXT,
    material TEXT,
    planning_variant TEXT,
    material_name TEXT,
    basis TEXT,
    qty REAL,
    need_date TEXT,
    order_no TEXT,
    input_date TEXT,
    year_num INTEGER,
    agreed_date TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_fact(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_value TEXT,
    plant_code TEXT,
    order_no TEXT,
    reg_no TEXT,
    material TEXT,
    material_name TEXT,
    qty_fact REAL,
    hours_fact REAL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS plans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_num INTEGER,
    month_num INTEGER,
    order_no TEXT,
    plant_code TEXT,
    material TEXT,
    material_name TEXT,
    unit TEXT,
    plan_qty REAL,
    plan_mod REAL,
    fact_qty REAL,
    work_center_name TEXT,
    norm_accounting TEXT,
    work_center_no TEXT,
    mod_hours REAL,
    fact_hours REAL
);

CREATE TABLE IF NOT EXISTS labor_fact(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT,
    planner TEXT,
    material TEXT,
    material_name TEXT,
    plant_code TEXT,
    start_date TEXT,
    end_date TEXT,
    planned_qty REAL,
    base_unit TEXT,
    workshop_name TEXT,
    work_center TEXT,
    work_center_name TEXT,
    fact_hours REAL,
    year_num INTEGER,
    month_num INTEGER,
    source_tag TEXT
);

CREATE TABLE IF NOT EXISTS warehouse_stock(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_code TEXT,
    warehouse TEXT,
    material TEXT,
    material_name TEXT,
    location TEXT,
    atz_batch TEXT,
    base_unit TEXT,
    free_stock REAL,
    free_stock_value REAL,
    valuation_type TEXT,
    batch TEXT,
    cost_center TEXT,
    cost_center_name TEXT,
    special_stock_no TEXT,
    special_stock TEXT
);

CREATE TABLE IF NOT EXISTS import_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    source_sheet TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    status TEXT,
    note TEXT
);
