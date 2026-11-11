import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QDialog, \
    QFormLayout, QDialogButtonBox, QCheckBox
from database import Database, init_database


class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setWindowTitle("VaultPy — вход")
        self.setFixedSize(350, 300)

        self.title_label = QLabel("VaultPy")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Мастер-пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.register_button = QPushButton("Зарегистрироваться")

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def login(self):
        """Вход"""

        username = self.username_input.text().strip()
        master_password = self.password_input.text()
        try:
            result = self.db.login(username, master_password)
            if result is None:
                QMessageBox.warning(self, "Ошибка входа", "Неверное имя пользователя или мастер-пароль.")
                return

            user_id, encryption_key = result
            self.open_main_window(user_id, encryption_key)

        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))

    def register(self):
        """Регистрация"""

        username = self.username_input.text().strip()
        master_password = self.password_input.text()

        try:
            user_id, encryption_key = self.db.register(username, master_password)
            QMessageBox.information(self, "Регистрация", "Аккаунт успешно создан!")
            self.open_main_window(user_id, encryption_key)

        except ValueError as error:
            QMessageBox.warning(self, "Ошибка регистрации", str(error))

    def open_main_window(self, user_id, encryption_key):
        """Начальное окно"""

        self.main_window = MainWindow(user_id, encryption_key)
        self.main_window.show()
        self.close()


class PassDialog(QDialog):
    def __init__(self, parent=None, pass_data=None):
        super().__init__(parent)

        self.setWindowTitle("Изменение записи" if pass_data else "Новая запись")
        self.setFixedSize(400, 300)

        self.title_input = QLineEdit()
        self.login_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.url_input = QLineEdit()

        self.title_input.setPlaceholderText("Например, GitHub")
        self.login_input.setPlaceholderText("Имя пользователя или почта")
        self.pass_input.setPlaceholderText("Пароль")
        self.url_input.setPlaceholderText("https://example.com")

        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_pass_chb = QCheckBox("Показать пароль")
        self.show_pass_chb.toggled.connect(self.toggle_pass_vis)

        layout = QFormLayout()
        layout.addRow("Название:", self.title_input)
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль", self.pass_input)
        layout.addRow("", self.show_pass_chb)
        layout.addRow("Сайт:", self.url_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save, QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.setLayout(layout)

        if pass_data:
            self.title_input.setText(pass_data['title'])
            self.login_input.setText(pass_data['login'])
            self.pass_input.setText(pass_data['password'])
            self.url_input.setText(pass_data['url'])

class MainWindow(QWidget):
    def __init__(self, user_id, encryption_key):
        super().__init__()

        self.user_id = user_id
        self.encryption_key = encryption_key
        self.setWindowTitle("VaultPy")
        self.resize(800, 600)
        label = QLabel(f"Добро пожаловать в VaultPy!\n"f"ID пользователя: {self.user_id}")
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    init_database()
    db = Database()
    login_window = LoginWindow(db)
    login_window.show()
    sys.exit(app.exec())
