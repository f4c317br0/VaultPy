import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from encryption import Encryption


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


class Database:
    def __init__(self):
        self.db_path = 'database/vault.db'
        os.makedirs(os.path.dirname('database/vault.db') or '.', exist_ok=True)

    @contextmanager
    def _connection(self):
        """открывает/закрывет соединение"""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")

        try:
            with con:
                yield con
        finally:
            con.close()

    @staticmethod
    def _now():
        """возвращает текущее время"""
        return datetime.now().isoformat(timespec='seconds')

    @staticmethod
    def _check_text(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Поле {field_name} пустое!")

    def register(self, username, masterpass):
        """Создает пользователя"""
        self._check_text(username, "Имя пользователя")
        self._check_text(masterpass, "Мастер-пароль")
        pass_hash, salt = Encryption.hash_pass(masterpass)
        encr_salt = os.urandom(16)
        encr_key = Encryption.derive_key(masterpass, encr_salt)
        with self._connection() as con:
            try:
                cursor = con.execute(
                    """
                    INSERT INTO users (
                        username,
                        password_hash,
                        salt,
                        encryption_salt,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        username.strip(),
                        pass_hash,
                        salt,
                        encr_salt,
                        self._now()
                    )
                )
            except sqlite3.IntegrityError:
                raise ValueError("Такой юзернейм уже занят")
            user_id = cursor.lastrowid

        return user_id, encr_key
