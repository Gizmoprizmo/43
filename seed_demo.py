
from pathlib import Path
from import_service import initialize_db, import_all_default_files

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "app.db"

if __name__ == "__main__":
    initialize_db(DB_PATH)
    report = import_all_default_files(DB_PATH, BASE_DIR)
    print("Импорт завершён:")
    for item in report:
        print(item)
