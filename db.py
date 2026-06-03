import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "stroymaterialy_demo",
    "use_unicode": True,
    "charset": "utf8mb4",
    "use_pure": True,
}


def get_connection():
    """Возвращает подключение к базе данных"""
    return mysql.connector.connect(**DB_CONFIG)