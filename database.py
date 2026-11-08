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


class Database:
    def __init__(self):
        self.db_path = 'database/vault.db'
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)

    @contextmanager
    def _connection(self):
        """открывает/закрывает соединение"""
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

    # ----------------------------------------------РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ------------------------------------------------

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

    def login(self, username, masterpass):
        """Проверяем данные пользователя -> возвращаем user id и encr key"""
        self._check_text(username, 'Имя пользователя')
        self._check_text(masterpass, "Мастер-пароль")
        with self._connection() as con:
            user = con.execute(
                """
                SELECT id, password_hash, salt, encryption_salt
                FROM users
                WHERE username = ?
                """,
                (username.strip(),)
            ).fetchone()

        if user is None:
            return None
        pass_corr = Encryption.verify_pass(masterpass, user['salt'], user['password_hash'])
        if not pass_corr:
            return None
        encr_key = Encryption.derive_key(masterpass, user['encryption_salt'])
        return user['id'], encr_key

    # ----------------------------------------------КАТЕГОРИИ------------------------------------------------

    def add_category(self, user_id, name):
        """Добавление категорий пользователя"""
        self._check_text(name, "Название категории")
        with self._connection() as con:
            try:
                cursor = con.execute(
                    """
                    INSERT INTO categories (user_id, name, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, name.strip(), self._now())
                )
            except sqlite3.IntegrityError:
                raise ValueError("Такая категория уже существует!")

            return cursor.lastrowid

    def get_categories(self, user_id):
        """Возвращение категорий пользователя"""
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT id, name, created_at
                FROM categories
                WHERE user_id = ?
                ORDER BY name
                """,
                (user_id,)
            ).fetchall()

        return [dict(row) for row in rows]

    def rename_category(self, user_id, category_id, new_name):
        """Переименование категорий"""
        self._check_text(new_name, 'Название категории')
        with self._connection() as con:
            try:
                cursor = con.execute(
                    """
                    UPDATE categories
                    SET name = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (new_name.strip(), category_id, user_id)
                )
            except sqlite3.IntegrityError:
                raise ValueError('Такая категория уже существует!')

            if cursor.rowcount == 0:
                raise ValueError('Категория не найдена!')

    def delete_category(self, user_id, category_id):
        """Удаление категории, но пароли внутри нее станут просто без категории"""

        with self._connection() as con:
            cursor = con.execute(
                """
                DELETE FROM categories
                WHERE id = ? AND user_id = ?
                """,
                (category_id, user_id)
            )
            if cursor.rowcount == 0:
                raise ValueError('Категория не найдена!')

    # ----------------------------------------------ПАРОЛИ------------------------------------------------

    def add_pass(self, user_id, category_id, title, login, password, url, encr_key):
        """Добавление зашифрованной записи пароля"""
        self._check_text(title, 'Название')
        self._check_text(login, 'Логин')
        self._check_text(password, 'Пароль')

        if category_id is not None:
            with self._connection() as con:
                category = con.execute(
                    """
                    SELECT id
                    FROM categories
                    WHERE id = ? AND user_id = ?
                    """,
                    (category_id, user_id)
                ).fetchone()

            if category is None:
                raise ValueError("Выбранная категория не найдена!")

        encr_pass, nonce = Encryption.encrypt(password, encr_key)
        now = self._now()
        with self._connection() as con:
            cursor = con.execute(
                """
                INSERT INTO passwords (
                    user_id,
                    category_id,
                    title,
                    login,
                    encrypted_password,
                    nonce,
                    url,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, category_id, title.strip(), login.strip(), encr_pass, nonce, url.strip(), now, now)
            )

            return cursor.lastrowid

    def get_pass(self, user_id, encr_key):
        """Получение записи и расшифровка паролей"""
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT
                     p.id,
                     p.category_id,
                     p.title,
                     p.login,
                     p.encrypted_password,
                     p.nonce,
                     p.url,
                     p.created_at,
                     p.updated_at,
                     c.name AS category_name
                 FROM passwords AS p
                 LEFT JOIN categories AS c
                     ON p.category_id = c.id
                 WHERE p.user_id = ?
                 ORDER BY p.title
                 """,
                (user_id,)
            ).fetchall()

        res = []
        for row in rows:
            decr_pass = Encryption.decrypt(row["encrypted_password"], row["nonce"], encr_key)
            res.append({
                "id": row["id"],
                "category_id": row["category_id"],
                'category_name': row['category_name'],
                'title': row['title'],
                'login': row['login'],
                'password': decr_pass,
                'url': row['url'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        return res

    def update_pass(self, user_id, password_id, category_id, title, login, password, url, encr_key):
        """Обновление пароля"""
        self._check_text(title, 'Название')
        self._check_text(login, 'Логин')
        self._check_text(password, 'Пароль')

        if category_id is not None:
            with self._connection() as con:
                category = con.execute(
                    """
                    SELECT id
                    FROM categories
                    WHERE id = ? AND user_id = ?
                    """,
                    (category_id, user_id)
                ).fetchone()
            if category is None:
                raise ValueError('Выбранная категория не существует!')

        encr_pass, nonce = Encryption.encrypt(password, encr_key)

        with self._connection() as con:
            cursor = con.execute(
                """
                UPDATE passwords
                SET
                    category_id = ?,
                    title = ?,
                    login = ?,
                    encrypted_password = ?,
                    nonce = ?,
                    url = ?,
                    updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (category_id, title.strip(), login.strip(), encr_pass, nonce, url.strip(), self._now(), password_id,
                 user_id)
            )

            if cursor.rowcount == 0:
                raise ValueError('Запись пароля не найдена!')

    def delete_pass(self, user_id, pass_id):
        """Стирает запись пароля"""
        with self._connection() as con:
            cursor = con.execute(
                """
                DELETE FROM passwords
                WHERE id = ? AND user_id = ?
                """,
                (pass_id, user_id)
            )

            if cursor.rowcount == 0:
                raise ValueError('Запись пароля не найдена!')

    # ----------------------------------------------ЗАМЕТКИ------------------------------------------------

    def add_note(self, user_id, title, content, encr_key):
        """Добавление заметки"""
        self._check_text(title, "Название заметки")
        self._check_text(content, 'Содержимое заметки')

        encr_content, nonce = Encryption.encrypt(content, encr_key)
        now = self._now()
        with self._connection() as con:
            cursor = con.execute(
                """
                INSERT INTO notes (
                    user_id,
                    title,
                    encrypted_content,
                    nonce,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, title.strip(), encr_content, nonce, now, now)
            )
            return cursor.lastrowid

    def get_notes(self, user_id, encr_key):
        """Получение и расшифровка заметок"""

        with self._connection() as con:
            rows = con.execute(
                """
                SELECT
                    id,
                    title,
                    encrypted_content,
                    nonce,
                    created_at,
                    updated_at
                FROM notes
                WHERE user_id = ?
                ORDER BY title
                """,
                (user_id,)
            ).fetchall()

        res = []

        for row in rows:
            content = Encryption.decrypt(row['encrypted_content'], row['nonce'], encr_key)
            res.append({
                "id": row["id"],
                'title': row['title'],
                'content': content,
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })

        return res

    def update_note(self, user_id, note_id, title, content, encr_key):
        """Изменение заметки"""

        self._check_text(title, 'Название заметки')
        self._check_text(content, 'Содержимое заметки')

        encr_content, nonce = Encryption.encrypt(content, encr_key)
        with self._connection() as con:
            cursor = con.execute(
                """
                UPDATE notes
                SET
                    title = ?,
                    encrypted_content = ?,
                    nonce = ?,
                    updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (title.strip(), encr_content, nonce, self._now(), note_id, user_id)
            )
            if cursor.rowcount == 0:
                raise ValueError('Заметка не найдена!')

    def delete_note(self, user_id, note_id):
        """Удаление заметки"""
        with self._connection() as con:
            cursor = con.execute(
                """
                DELETE FROM notes
                WHERE id = ? AND user_id = ?
                """,
                (note_id, user_id)
            )
            if cursor.rowcount == 0:
                raise ValueError('Заметка не найдена!')


if __name__ == "__main__":
    init_database()
    print("Все четко")
