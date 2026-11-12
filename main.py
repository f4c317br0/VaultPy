import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QDialog, \
    QFormLayout, QDialogButtonBox, QCheckBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView, \
    QAbstractItemView, QComboBox, QListWidget, QTextEdit, QInputDialog, QSpinBox
from database import Database, init_database
import secrets
import string

STYLE = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: Segoe UI;
    font-size: 10pt;
}

QDialog {
    background-color: #1e1e2e;
}

QLabel {
    color: #cdd6f4;
}

QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px;
    selection-background-color: #585b70;
}

QLineEdit:focus, QTextEdit:focus,
QComboBox:focus, QSpinBox:focus {
    border: 1px solid #89b4fa;
}

QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: none;
    border-radius: 6px;
    padding: 9px 14px;
}

QPushButton:hover {
    background-color: #585b70;
}

QPushButton:pressed {
    background-color: #313244;
}

QTableWidget, QListWidget {
    background-color: #181825;
    alternate-background-color: #242436;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #313244;
    selection-background-color: #45475a;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #45475a;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QScrollBar:vertical {
    background-color: #181825;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #585b70;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""


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
    def __init__(self, parent=None, pass_data=None, categories=None):
        super().__init__(parent)

        self.setWindowTitle("Изменение записи" if pass_data else "Новая запись")
        self.setFixedSize(400, 300)
        self.setMinimumSize(400, 300)

        self.title_input = QLineEdit()
        self.login_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.url_input = QLineEdit()

        self.title_input.setPlaceholderText("Например, GitHub")
        self.login_input.setPlaceholderText("Имя пользователя или почта")
        self.pass_input.setPlaceholderText("Пароль")
        self.url_input.setPlaceholderText("https://example.com")

        self.category_combo = QComboBox()
        self.category_combo.addItem("Без категории", None)
        self.categories = categories or []
        for category in self.categories:
            self.category_combo.addItem(category["name"], category["id"])

        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_pass_chb = QCheckBox("Показать пароль")
        self.show_pass_chb.toggled.connect(self.toggle_pass_vis)

        layout = QFormLayout()
        layout.addRow("Название:", self.title_input)
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль", self.pass_input)
        layout.addRow("", self.show_pass_chb)
        layout.addRow("Сайт:", self.url_input)
        layout.addRow("Категория:", self.category_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.setLayout(layout)

        if pass_data:
            category_id = pass_data["category_id"]
            idx = self.category_combo.findData(category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
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
            "url": self.url_input.text(),
            "category_id": self.category_combo.currentData()
        }


class CatDialog(QDialog):
    def __init__(self, db, user_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.setWindowTitle("Управление категорями")
        self.setFixedSize(350, 400)
        self.setMinimumSize(600, 400)
        self.cat_list = QListWidget()

        self.add_btn = QPushButton("Добавить")
        self.rename_btn = QPushButton("Переименовать")
        self.del_btn = QPushButton("Удалить")

        self.add_btn.clicked.connect(self.add_cat)
        self.rename_btn.clicked.connect(self.rename_cat)
        self.del_btn.clicked.connect(self.del_cat)

        layout = QVBoxLayout()
        layout.addWidget(self.cat_list)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.del_btn)

        self.setLayout(layout)
        self.load_cat()

    def load_cat(self):
        """Загрузка категорий пользователя"""

        self.cat_list.clear()
        self.cats = self.db.get_categories(self.user_id)
        for cat in self.cats:
            self.cat_list.addItem(cat["name"])

    def add_cat(self):
        """Создание новой категории"""

        name, accepted = QInputDialog.getText(self, "Новая категория", "Название категории")
        if not accepted:
            return
        try:
            self.db.add_category(self.user_id, name)
            self.load_cat()
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))

    def rename_cat(self):
        """Переименование выбранной категории"""

        row = self.cat_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите категорию!")
            return
        cat = self.cats[row]
        new_name, accepted = QInputDialog.getText(self, "Переименование", "Новое название", text=cat["name"])
        if not accepted:
            return
        try:
            self.db.rename_category(self.user_id, cat['id'], new_name)
            self.load_cat()
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))

    def del_cat(self):
        """Удаление выбраной категории"""

        row = self.cat_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите категорию!")
            return
        cat = self.cats[row]
        ans = QMessageBox.question(self, "Подтверждение", f"Удалить запись <<{cat['name']}>>?",
                                   QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.delete_category(self.user_id, cat['id'])
            self.load_cat()
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))


class NotesDialog(QDialog):
    def __init__(self, db, user_id, encr_key, parent=None):
        super().__init__(parent)

        self.db = db
        self.user_id = user_id
        self.encr_key = encr_key
        self.notes = []
        self.curr_note_id = None

        self.setWindowTitle("Защищенные заметки")
        self.resize(700, 500)
        self.setMinimumSize(400, 300)

        self.notes_list = QListWidget()
        self.notes_list.currentRowChanged.connect(self.sel_note)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название заметки")

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Введите содержимое заметки...")

        self.add_btn = QPushButton("Новая заметка")
        self.save_btn = QPushButton("Сохранить")
        self.del_btn = QPushButton("Удалить")

        self.add_btn.clicked.connect(self.new_note)
        self.save_btn.clicked.connect(self.save_note)
        self.del_btn.clicked.connect(self.del_note)

        l_layout = QVBoxLayout()
        l_layout.addWidget(QLabel('Мои заметки'))
        l_layout.addWidget(self.notes_list)
        l_layout.addWidget(self.add_btn)

        r_layout = QVBoxLayout()
        r_layout.addWidget(QLabel("Название"))
        r_layout.addWidget(self.title_input)
        r_layout.addWidget(QLabel("Содержимое"))
        r_layout.addWidget(self.content_input)
        r_layout.addWidget(self.save_btn)
        r_layout.addWidget(self.del_btn)

        main_layout = QHBoxLayout()
        main_layout.addLayout(l_layout, 1)
        main_layout.addLayout(r_layout, 2)
        self.setLayout(main_layout)
        self.load_notes()

    def load_notes(self):
        """Загрузка заметок из бд"""

        self.notes_list.blockSignals(True)
        self.notes_list.clear()

        try:
            self.notes = self.db.get_notes(self.user_id, self.encr_key)
            for note in self.notes:
                self.notes_list.addItem(note['title'])
        except Exception:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить заметки")

        self.notes_list.blockSignals(False)
        self.new_note()

    def sel_note(self, row):
        """Вывод выбранной заметки"""

        if row < 0 or row >= len(self.notes):
            return
        note = self.notes[row]

        self.curr_note_id = note['id']
        self.title_input.setText(note['title'])
        self.content_input.setPlainText(note['content'])

    def new_note(self):
        """Подготавление нового поля для заметки"""

        self.notes_list.clearSelection()
        self.curr_note_id = None
        self.title_input.clear()
        self.content_input.clear()

    def save_note(self):
        """Добавление новой заметки или изменении существующей"""

        title = self.title_input.text().strip()
        content = self.content_input.toPlainText()

        try:
            if self.curr_note_id is None:
                self.db.add_note(self.user_id, title, content, self.encr_key)
                QMessageBox.information(self, "Успешно", "Заметка создана")
            else:
                self.db.update_note(self.user_id, self.curr_note_id, title, content, self.encr_key)
                QMessageBox.information(self, "Успешно", "Заметка изменена")
            self.load_notes()
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))

    def del_note(self):
        """Удаление выбранной заметки"""

        if self.curr_note_id is None:
            QMessageBox.warning(self, "Внимание", "Сначала выберите заметку")
            return
        ans = QMessageBox.question(self, "Подтверждение", f"Удалить эту заметку?",
                                   QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.delete_note(self.user_id, self.curr_note_id)
            self.load_notes()
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))


class GeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Генератор паролей")
        self.setFixedSize(350, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Длина пароля:"))

        self.len_input = QSpinBox()
        self.len_input.setRange(8, 64)
        self.len_input.setValue(16)

        layout.addWidget(self.len_input)

        self.lowercase = QCheckBox("Строчные буквы (a-z)")
        self.uppercase = QCheckBox("Заглавные буквы (A-Z)")
        self.digits = QCheckBox("Цифры (0-9)")
        self.symbols = QCheckBox("Специальные символы")

        self.lowercase.setChecked(True)
        self.uppercase.setChecked(True)
        self.digits.setChecked(True)
        self.symbols.setChecked(True)

        layout.addWidget(self.lowercase)
        layout.addWidget(self.uppercase)
        layout.addWidget(self.digits)
        layout.addWidget(self.symbols)

        self.res_input = QLineEdit()
        self.res_input.setReadOnly(True)
        layout.addWidget(self.res_input)

        self.gen_btn = QPushButton("Сгенерировать")
        self.copy_btn = QPushButton("Копировать")

        self.gen_btn.clicked.connect(self.gen_pass)
        self.copy_btn.clicked.connect(self.copy_pass)

        layout.addWidget(self.gen_btn)
        layout.addWidget(self.copy_btn)

    def gen_pass(self):
        characters = ''
        req_characters = []

        if self.lowercase.isChecked():
            characters += string.ascii_lowercase
            req_characters.append(secrets.choice(string.ascii_lowercase))

        if self.uppercase.isChecked():
            characters += string.ascii_uppercase
            req_characters.append(secrets.choice(string.ascii_uppercase))

        if self.digits.isChecked():
            characters += string.digits
            req_characters.append(secrets.choice(string.digits))

        if self.symbols.isChecked():
            special = '!@#$%^&*()-_=+'
            characters += special
            req_characters.append(secrets.choice(special))

        if not characters:
            QMessageBox.warning(self, 'Ошибка', "Выберите хотя бы 1 набор символов!")
            return

        length = self.len_input.value()
        if len(req_characters) > length:
            QMessageBox.warning(self, 'Ошибка', "Длина пароля слишком мала для выбранных паролей!")
            return

        password = req_characters.copy()
        for _ in range(length - len(password)):
            password.append(secrets.choice(characters))

        secrets.SystemRandom().shuffle(password)
        self.res_input.setText("".join(password))

    def copy_pass(self):
        password = self.res_input.text()
        if not password:
            QMessageBox.warning(self, 'Ошибка', 'Сначала сгенерируйте пароль!')
            return
        QApplication.clipboard().setText(password)
        QMessageBox.information(self, 'Готово', 'Пароль скопирован!')


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
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
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
        self.cats_btn = QPushButton("Категории")
        self.notes_btn = QPushButton("Заметки")
        self.gen_btn = QPushButton("Генератор паролей")

        self.add_btn.clicked.connect(self.add_pass)
        self.edit_btn.clicked.connect(self.edit_pass)
        self.delete_btn.clicked.connect(self.delete_pass)
        self.refresh_btn.clicked.connect(self.load_pass)
        self.cats_btn.clicked.connect(self.open_cats)
        self.notes_btn.clicked.connect(self.open_notes)
        self.gen_btn.clicked.connect(self.open_gen)

        btns_layout = QHBoxLayout()
        btns_layout.addWidget(self.add_btn)
        btns_layout.addWidget(self.edit_btn)
        btns_layout.addWidget(self.delete_btn)
        btns_layout.addWidget(self.refresh_btn)
        btns_layout.addWidget(self.cats_btn)
        btns_layout.addWidget(self.notes_btn)
        btns_layout.addWidget(self.gen_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию, логину или URL...")
        self.search_input.textChanged.connect(self.filter_pass)

        layout = QVBoxLayout()
        layout.addLayout(btns_layout)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_pass()

    def open_gen(self):
        dialog = GeneratorDialog(self)
        dialog.exec()

    def filter_pass(self, search_text):
        search_text = search_text.casefold()
        self.visible_pass = [
            password
            for password in self.passwords
            if search_text in password['title'].casefold()
               or search_text in password['login'].casefold()
               or search_text in (password['url'] or '').casefold()
        ]
        self.table.setRowCount(0)
        for password in self.visible_pass:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(password['title']))
            self.table.setItem(row, 1, QTableWidgetItem(password['login']))
            self.table.setItem(row, 2, QTableWidgetItem(password['url'] or ""))

    def load_pass(self):
        """Загрузка записей из бд"""
        try:
            self.passwords = self.db.get_pass(self.user_id, self.encr_key)
            self.filter_pass(self.search_input.text())
        except Exception as er:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пароли: {er}")

    def add_pass(self):
        """Окно добавления записи"""

        cats = self.db.get_categories(self.user_id)
        dialog = PassDialog(self, categories=cats)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            self.db.add_pass(user_id=self.user_id, category_id=data['category_id'], title=data['title'],
                             login=data['login'],
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
        pass_data = self.visible_pass[sel_row]
        cats = self.db.get_categories(self.user_id)
        dialog = PassDialog(self, pass_data=pass_data, categories=cats)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_data = dialog.get_data()
        try:
            self.db.update_pass(user_id=self.user_id, password_id=pass_data['id'], category_id=new_data['category_id'],
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
        pass_data = self.visible_pass[sel_row]
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

    def open_cats(self):
        """Открывание управления категорями"""

        dialog = CatDialog(self.db, self.user_id, self)
        dialog.exec()
        self.load_pass()

    def open_notes(self):
        """Открывание окно заметок"""

        dialog = NotesDialog(self.db, self.user_id, self.encr_key, self)
        dialog.exec()


if __name__ == "__main__":
    init_database()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    db = Database()
    login_window = LoginWindow(db)
    login_window.show()
    sys.exit(app.exec())
