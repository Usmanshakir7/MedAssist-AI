import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "medassist.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- Users ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- Reports ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        report_type TEXT,
        hospital_name TEXT,
        report_date TEXT,
        file_path TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # ---------------- Test Results ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER,
        test_name TEXT,
        value REAL,
        unit TEXT,
        reference_low REAL,
        reference_high REAL,
        status TEXT,
        FOREIGN KEY(report_id) REFERENCES reports(report_id)
    )
    """)

    # ---------------- AI Insights ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_insights(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER,
        summary TEXT,
        recommendation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(report_id) REFERENCES reports(report_id)
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database created successfully!")