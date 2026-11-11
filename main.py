import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QDialog, \
    QFormLayout, QDialogButtonBox, QCheckBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView, \
    QAbstractItemView
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

        self.main_window = MainWindow(self.db, user_id, encryption_key)
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.setLayout(layout)

        if pass_data:
            self.title_input.setText(pass_data['title'])
            self.login_input.setText(pass_data['login'])
            self.pass_input.setText(pass_data['password'])
            self.url_input.setText(pass_data['url'])

    def toggle_pass_vis(self, checked):
        """Переключение видимости пароля"""

        if checked:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

    def get_data(self):
        """Возвращение введенных данных"""
        return {
            "title": self.title_input.text().strip(),
            "login": self.login_input.text().strip(),
            "password": self.pass_input.text(),
            "url": self.url_input.text()
        }


class MainWindow(QWidget):
    def __init__(self, db, user_id, encr_key):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.encr_key = encr_key
        self.passwords = []
        self.setWindowTitle("VaultPy - менеджер паролей")
        self.resize(900, 600)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Название', 'Логин', 'Сайт'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Изменить")
        self.delete_btn = QPushButton("Удалить")
        self.refresh_btn = QPushButton("Обновить")

        self.add_btn.clicked.connect(self.add_pass)
        self.edit_btn.clicked.connect(self.edit_pass)
        self.delete_btn.clicked.connect(self.delete_pass)
        self.refresh_btn.clicked.connect(self.load_pass)

        btns_layout = QHBoxLayout()
        btns_layout.addWidget(self.add_btn)
        btns_layout.addWidget(self.edit_btn)
        btns_layout.addWidget(self.delete_btn)
        btns_layout.addWidget(self.refresh_btn)

        layout = QVBoxLayout()
        layout.addLayout(btns_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_pass()

    def load_pass(self):
        """Загрузка записей из бд"""
        try:
            self.passwords = self.db.get_pass(self.user_id, self.encr_key)
            self.table.setRowCount(len(self.passwords))
            for row, pass_data in enumerate(self.passwords):
                title_item = QTableWidgetItem(pass_data['title'])
                login_item = QTableWidgetItem(pass_data['login'])
                url_item = QTableWidgetItem(pass_data['url'])
                self.table.setItem(row, 0, title_item)
                self.table.setItem(row, 1, login_item)
                self.table.setItem(row, 2, url_item)
        except Exception:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить записи из базы данных!")

    def add_pass(self):
        """Окно добавления записи"""
        dialog = PassDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            self.db.add_pass(user_id=self.user_id, category_id=None, title=data['title'], login=data['login'],
                             password=data['password'], url=data['url'], encr_key=self.encr_key)
            self.load_pass()
            QMessageBox.information(self, "Успешно", "Запись добавлена!")
        except ValueError as er:
            QMessageBox.warning(self, "Ошибка", str(er))

    def edit_pass(self):
        """Редактирование выбранной записи"""
        sel_row = self.table.currentRow()
        if sel_row < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите запись для изменения!")
            return
        pass_data = self.passwords[sel_row]
        dialog = PassDialog(self, pass_data=pass_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_data = dialog.get_data()
        try:
            self.db.update_pass(user_id=self.user_id, password_id=pass_data['id'], category_id=pass_data['category_id'],
                                title=new_data['title'], login=new_data['login'], password=new_data['password'],
                                url=new_data['url'], encr_key=self.encr_key)
            self.load_pass()
            QMessageBox.information(self, "Успешно", "Запись изменена!")
        except ValueError as er:
            QMessageBox.warning(self, "Ошибка", str(er))

    def delete_pass(self):
        """Удаление выбраной записи"""
        sel_row = self.table.currentRow()
        if sel_row < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите запись для удаления!")
            return
        pass_data = self.passwords[sel_row]
        ans = QMessageBox.question(self, "Подтверждение", f"Удалить запись <<{pass_data['title']}>>?",
                                   QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.delete_pass(self.user_id, pass_data['id'])
            self.load_pass()
            QMessageBox.information(self, 'Успешно', "Запись удалена!")
        except ValueError as er:
            QMessageBox.warning(self, "Ошибка", str(er))


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.excepthook = except_hook
    init_database()
    db = Database()
    login_window = LoginWindow(db)
    login_window.show()
    sys.exit(app.exec())
