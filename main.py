import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QFrame
from database import Database, init_database

acc = "#245BFF"
back = "#101A46"
style = f"""
    QWidget {{
        background-color: {back};
        color: #FFFFFF;
        font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
        font-size: 14px;
    }}

    QLabel#title {{
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #FFFFFF;
    }}

    QLabel#subtitle {{
        font-size: 13px;
        color: rgba(255, 255, 255, 0.55);
    }}

    QLineEdit {{
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 12px 14px;
        color: #FFFFFF;
        selection-background-color: {acc};
    }}

    QLineEdit:hover {{
        border: 1px solid rgba(255, 255, 255, 0.25);
    }}

    QLineEdit:focus {{
        border: 1px solid {acc};
        background-color: rgba(36, 91, 255, 0.10);
    }}

    QPushButton {{
        border-radius: 10px;
        padding: 12px;
        font-weight: 600;
    }}

    QPushButton#primary {{
        background-color: {acc};
        color: #FFFFFF;
        border: none;
    }}

    QPushButton#primary:hover {{
        background-color: #3D6FFF;
    }}

    QPushButton#primary:pressed {{
        background-color: #1B49D6;
    }}

    QPushButton#secondary {{
        background-color: transparent;
        color: {acc};
        border: 1px solid {acc};
    }}

    QPushButton#secondary:hover {{
        background-color: rgba(36, 91, 255, 0.15);
    }}

    QPushButton#secondary:pressed {{
        background-color: rgba(36, 91, 255, 0.25);
    }}

    QMessageBox {{
        background-color: {back};
    }}
"""
main_style = f"""
    QWidget {{
        background-color: {back};
        color: #FFFFFF;
        font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
        font-size: 14px;
    }}

    QLabel {{
        background: transparent;
    }}

    QLabel#welcome {{
        font-size: 28px;
        font-weight: 700;
    }}

    QLabel#hint {{
        font-size: 13px;
        color: rgba(255, 255, 255, 0.55);
    }}

    QFrame#card {{
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
    }}

    QLabel#card_caption {{
        font-size: 12px;
        color: rgba(255, 255, 255, 0.55);
    }}

    QLabel#card_value {{
        font-size: 18px;
        font-weight: 600;
        color: {acc};
    }}
"""


class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setWindowTitle("VaultPy — вход")
        self.setFixedSize(380, 460)
        self.setStyleSheet(style)

        self.title_label = QLabel("VaultPy")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("Ваш надёжный менеджер паролей")
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Мастер-пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.setObjectName("primary")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.setObjectName("secondary")
        self.register_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(24)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(12)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        layout.addStretch()

        self.setLayout(layout)

    def login(self):
        """Вход"""
        username = self.username_input.text().strip()
        master_pass = self.password_input.text()

        try:
            res = self.db.login(username, master_pass)
            if res is None:
                QMessageBox.warning(self, "Ошибка входа!", "Неверное имя пользователя или пароль!")
                return

            user_id, encr_key = res
            self.open_main_window(user_id, encr_key)
        except ValueError as er:
            QMessageBox(self, "Ошибка", str(er))

    def register(self):
        """Регистрация"""
        username = self.username_input.text().strip()
        master_pass = self.password_input.text()
        try:
            user_id, encr_key = self.db.register(username, master_pass)
            QMessageBox.information(self, 'Регистрация', 'Аккаунт успешно создан!')
            self.open_main_window(user_id, encr_key)

        except ValueError as er:
            QMessageBox.warning(self, 'Ошибка регистрации!', str(er))

    def open_main_window(self, user_id, encr_key):
        """Открытие главного окна приложения"""

        self.main_window = MainWindow(user_id, encr_key)
        self.main_window.show()
        self.close()


class MainWindow(QWidget):
    def __init__(self, user_id, encr_key):
        super().__init__()
        self.user_id = user_id
        self.encr_key = encr_key

        self.setWindowTitle("VaultPy")
        self.resize(800, 600)
        self.setStyleSheet(main_style)
        welcome_label = QLabel("Добро пожаловать!")
        welcome_label.setObjectName("welcome")
        hint_label = QLabel("Ваше хранилище паролей готово к работе")
        hint_label.setObjectName("hint")
        card = QFrame()
        card.setObjectName("card")
        caption_label = QLabel("ID пользователя")
        caption_label.setObjectName("card_caption")
        value_label = QLabel(str(self.user_id))
        value_label.setObjectName("card_value")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(4)
        card_layout.addWidget(caption_label)
        card_layout.addWidget(value_label)
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(8)
        layout.addWidget(welcome_label)
        layout.addWidget(hint_label)
        layout.addSpacing(24)
        layout.addWidget(card)
        layout.addStretch()
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    init_database()
    db = Database()
    login_window = LoginWindow(db)
    login_window.show()
    sys.exit(app.exec())
