import sqlite3

def init_db():
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_name TEXT,
        language TEXT,
        original_text TEXT,
        translated_text TEXT,
        severity TEXT,
        action TEXT,
        reported_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()