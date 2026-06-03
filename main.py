import os
import sys
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QComboBox, QSpinBox, QTextEdit,
    QScrollArea, QFrame, QGridLayout, QHeaderView
)

from db import get_connection


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в систему — ООО «СтройМатериалы»")
        self.setMinimumWidth(420)
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))

        self.login_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Логин:", self.login_edit)
        form.addRow("Пароль:", self.password_edit)

        login_btn = QPushButton("Войти")
        guest_btn = QPushButton("Войти как гость")
        cancel_btn = QPushButton("Отмена")

        login_btn.clicked.connect(self.try_login)
        guest_btn.clicked.connect(self.login_as_guest)
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(login_btn)
        buttons.addWidget(guest_btn)
        buttons.addWidget(cancel_btn)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(buttons)

        self.user_data = None  # (user_id, login, role_name)

    def try_login(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT u.user_id, u.login, r.name as role_name
                FROM users u
                JOIN roles r ON r.role_id = u.role_id
                WHERE u.login = %s AND u.password = %s
            """, (login, password))
            row = cur.fetchone()
            if row:
                self.user_data = (row["user_id"], row["login"], row["role_name"])
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))
        finally:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()

    def login_as_guest(self):
        self.user_data = (None, "Гость", "гость")
        self.accept()


class ProductDialog(QDialog):
    """Диалог добавления/редактирования товара (только для администратора)"""
    def __init__(self, tovar_id=None, parent=None):
        super().__init__(parent)
        self.tovar_id = tovar_id
        self.setWindowTitle("Товар" if tovar_id else "Новый товар")
        self.setMinimumWidth(500)

        self.name_edit = QLineEdit()
        self.article_edit = QLineEdit()
        self.price_spin = QSpinBox()
        self.price_spin.setMaximum(1000000)
        self.discount_spin = QSpinBox()
        self.discount_spin.setMaximum(100)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMaximum(100000)
        self.unit_edit = QLineEdit()
        self.description_edit = QTextEdit()

        form = QFormLayout()
        form.addRow("Наименование:", self.name_edit)
        form.addRow("Артикул:", self.article_edit)
        form.addRow("Цена:", self.price_spin)
        form.addRow("Скидка %:", self.discount_spin)
        form.addRow("Количество:", self.quantity_spin)
        form.addRow("Ед. изм.:", self.unit_edit)
        form.addRow("Описание:", self.description_edit)

        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(btn_layout)

        if tovar_id:
            self.load_data()

    def load_data(self):
        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM tovars WHERE tovar_id = %s", (self.tovar_id,))
            row = cur.fetchone()
            if row:
                self.name_edit.setText(row["name"])
                self.article_edit.setText(str(row["article"]) if row["article"] else "")
                self.price_spin.setValue(int(row["price"]))
                self.discount_spin.setValue(row["discount"])
                self.quantity_spin.setValue(row["quantity"])
                self.unit_edit.setText(row["unit"] or "")
                self.description_edit.setPlainText(row["description"] or "")
        finally:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()

    def save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование товара")
            return

        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            if self.tovar_id is None:
                cur.execute("""
                    INSERT INTO tovars (name, article, price, discount, quantity, unit, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, self.article_edit.text().strip() or None,
                      self.price_spin.value(), self.discount_spin.value(),
                      self.quantity_spin.value(), self.unit_edit.text().strip(),
                      self.description_edit.toPlainText().strip()))
            else:
                cur.execute("""
                    UPDATE tovars SET name=%s, article=%s, price=%s, discount=%s,
                                      quantity=%s, unit=%s, description=%s
                    WHERE tovar_id=%s
                """, (name, self.article_edit.text().strip() or None,
                      self.price_spin.value(), self.discount_spin.value(),
                      self.quantity_spin.value(), self.unit_edit.text().strip(),
                      self.description_edit.toPlainText().strip(), self.tovar_id))
            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  # (user_id, login, role_name)
        self.role = user_data[2].lower() if user_data[2] else "гость"

        self.setWindowTitle("ООО «СтройМатериалы» — Информационная система")
        self.setMinimumSize(1200, 750)
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # === ШАПКА С ЛОГОТИПОМ ===
        header = QHBoxLayout()
        logo_label = QLabel()
        try:
            pix = QPixmap(resource_path("resources/logo.png"))
            logo_label.setPixmap(pix.scaledToHeight(70, Qt.TransformationMode.SmoothTransformation))
        except:
            logo_label.setText("ООО «СтройМатериалы»")
            logo_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #B8860B;")

        header.addWidget(logo_label)
        header.addStretch()

        user_label = QLabel(f"Пользователь: {user_data[1]} | Роль: {user_data[2]}")
        header.addWidget(user_label)

        logout_btn = QPushButton("Выйти")
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)

        root.addLayout(header)

        # === ОСНОВНОЙ КОНТЕНТ ===
        self.content = QVBoxLayout()
        root.addLayout(self.content)

        self.load_interface()

    def load_interface(self):
        for i in reversed(range(self.content.count())):
            widget = self.content.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if self.role == "гость" or self.role == "клиент":
            self.show_products_guest_or_client()
        elif self.role == "менеджер":
            self.show_manager_interface()
        elif self.role == "администратор":
            self.show_admin_interface()
        else:
            self.show_products_guest_or_client()

    def show_products_guest_or_client(self):
        title = QLabel("Каталог товаров (просмотр)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #B8860B;")
        self.content.addWidget(title)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["Наименование", "Артикул", "Цена", "Скидка %", "Остаток", "Ед."])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content.addWidget(self.products_table)

        self.load_products(filtered=False)

    def show_manager_interface(self):
        title = QLabel("Товары (менеджер)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #B8860B;")
        self.content.addWidget(title)

        filter_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по наименованию...")
        self.search_edit.textChanged.connect(self.load_products)

        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(self.search_edit)
        filter_layout.addStretch()
        self.content.addLayout(filter_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["Наименование", "Артикул", "Цена", "Скидка %", "Остаток", "Ед."])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.content.addWidget(self.products_table)

        self.load_products(filtered=True)

        orders_btn = QPushButton("Просмотреть заказы")
        orders_btn.clicked.connect(self.show_orders)
        self.content.addWidget(orders_btn)

    def show_admin_interface(self):
        title = QLabel("Администрирование — Товары и Заказы")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #B8860B;")
        self.content.addWidget(title)

        filter_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по наименованию...")
        self.search_edit.textChanged.connect(self.load_products)

        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(self.search_edit)
        filter_layout.addStretch()

        add_btn = QPushButton("Добавить товар")
        add_btn.clicked.connect(self.add_product)
        filter_layout.addWidget(add_btn)
        self.content.addLayout(filter_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels(["ID", "Наименование", "Цена", "Скидка %", "Остаток", "Редактировать", "Удалить"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.content.addWidget(self.products_table)

        self.load_products(filtered=True, admin_mode=True)

        orders_title = QLabel("Заказы")
        orders_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        self.content.addWidget(orders_title)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Дата", "Клиент", "Статус", "Сумма"])
        self.content.addWidget(self.orders_table)

        self.load_orders()

    def load_products(self, filtered=False, admin_mode=False):
        search_text = self.search_edit.text().strip().lower() if filtered and hasattr(self, 'search_edit') else ""

        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM tovars ORDER BY name")
            rows = cur.fetchall()
        finally:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()

        table = self.products_table
        table.setRowCount(0)

        for row in rows:
            if search_text and search_text not in row["name"].lower():
                continue

            discount = row["discount"] or 0
            row_pos = table.rowCount()
            table.insertRow(row_pos)

            table.setItem(row_pos, 0, QTableWidgetItem(row["name"]))
            table.setItem(row_pos, 1, QTableWidgetItem(str(row["article"]) if row["article"] else ""))
            table.setItem(row_pos, 2, QTableWidgetItem(f"{row['price']:.2f}"))
            table.setItem(row_pos, 3, QTableWidgetItem(str(discount)))

            if discount > 12:
                for col in range(table.columnCount()):
                    item = table.item(row_pos, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.yellow)

            table.setItem(row_pos, 4, QTableWidgetItem(str(row["quantity"])))
            table.setItem(row_pos, 5, QTableWidgetItem(row["unit"] or ""))

            if admin_mode:
                edit_btn = QPushButton("Ред.")
                edit_btn.clicked.connect(lambda _, tid=row["tovar_id"]: self.edit_product(tid))
                table.setCellWidget(row_pos, 6, edit_btn)

                del_btn = QPushButton("Удал.")
                del_btn.clicked.connect(lambda _, tid=row["tovar_id"]: self.delete_product(tid))
                table.setCellWidget(row_pos, 7, del_btn) if table.columnCount() > 7 else None

    def add_product(self):
        dlg = ProductDialog(parent=self)
        if dlg.exec():
            self.load_products(filtered=True, admin_mode=True)

    def edit_product(self, tovar_id):
        dlg = ProductDialog(tovar_id=tovar_id, parent=self)
        if dlg.exec():
            self.load_products(filtered=True, admin_mode=True)

    def delete_product(self, tovar_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить товар?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = None
            cur = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM tovars WHERE tovar_id = %s", (tovar_id,))
                conn.commit()
                self.load_products(filtered=True, admin_mode=True)
            finally:
                if cur: cur.close()
                if conn and conn.is_connected(): conn.close()

    def load_orders(self):
        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT o.order_id, o.order_date, u.full_name as client, o.status, o.total
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                ORDER BY o.order_date DESC
            """)
            rows = cur.fetchall()
        finally:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()

        table = self.orders_table
        table.setRowCount(0)
        for row in rows:
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(str(row["order_id"])))
            table.setItem(r, 1, QTableWidgetItem(str(row["order_date"])))
            table.setItem(r, 2, QTableWidgetItem(row["client"]))
            table.setItem(r, 3, QTableWidgetItem(row["status"]))
            table.setItem(r, 4, QTableWidgetItem(f"{row['total']:.2f}"))

    def show_orders(self):
        QMessageBox.information(self, "Заказы", "Здесь будет подробный просмотр заказов (можно доработать)")

    def logout(self):
        self.close()


def apply_style(app):
    app.setFont(QFont("Calibri", 12))
    app.setStyleSheet("""
        QWidget {
            background: #FFFFFF;
            color: #1a1a1a;
        }
        QPushButton {
            background: #B8860B;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #9A6F0A;
        }
        QLineEdit, QTableWidget, QTextEdit, QSpinBox {
            border: 1px solid #DAA520;
            border-radius: 4px;
            padding: 6px;
            background: white;
        }
        QHeaderView::section {
            background: #DAA520;
            color: white;
            font-weight: bold;
            padding: 6px;
        }
    """)


def main():
    app = QApplication(sys.argv)
    apply_style(app)

    login = LoginDialog()
    if login.exec():
        user_data = login.user_data
        if user_data:
            window = MainWindow(user_data)
            window.show()
            sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()