import sqlite3
import os


def init_database():
    """Создаём базы данных и таблицы"""

    os.makedirs("database", exist_ok=True)

    con = sqlite3.connect("database/vault.db")
    cur = con.cursor()

    cur.execute("PRAGMA foreign_keys = ON")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        salt BLOB NOT NULL,
        encryption_salt BLOB NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id)
            ON DELETE CASCADE,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, name)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id)
            ON DELETE CASCADE,
        category_id INTEGER REFERENCES categories(id)
            ON DELETE SET NULL,
        title TEXT NOT NULL,
        login TEXT NOT NULL,
        encrypted_password BLOB NOT NULL,
        nonce BLOB NOT NULL,
        url TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id)
            ON DELETE CASCADE,
        title TEXT NOT NULL,
        encrypted_content BLOB NOT NULL,
        nonce BLOB NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    con.commit()
    con.close()


if __name__ == "__main__":
    init_database()
    print("Все четко")
