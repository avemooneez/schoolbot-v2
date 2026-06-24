import psycopg2
from psycopg2 import Error as Psycopg2Error
from utils.tokens import db_user, db_host, db_passwd
import logging
import os


class Database:
    def __init__(self):
        """
        Инициализирует класс, подключается к БД.
        """
        try:
            # Параметры подключения
            connect_params = {
                'user': db_user,
                'password': db_passwd,
                'host': db_host,
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'schoolproject'),
            }
            
            # Добавляем SSL параметры, если они указаны
            if os.getenv('DB_SSL_MODE'):
                connect_params['sslmode'] = os.getenv('DB_SSL_MODE')
            
            # Параметры для работы через SSH туннель или с проблемами подключения
            connect_params['connect_timeout'] = int(os.getenv('DB_CONNECT_TIMEOUT', '10'))
            
            self.conn = psycopg2.connect(**connect_params)
            self.cur = self.conn.cursor()
            self.conn.autocommit = True
            logging.info(f"Успешно подключено к базе данных {connect_params['host']}:{connect_params['port']}")
        except Psycopg2Error as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            logging.error(f"Проверьте настройки подключения в .env файле")
            logging.error(f"Или используйте SSH туннель: ./scripts/setup_ssh_tunnel.sh")
            raise

    def start(self):
        """
        Создаёт таблицу users, если таковой не существует.
        """
        try:
            self.create_tables()
            user_count = self.get_user_count()
            logging.info(
                f"База данных инициализирована. Пользователей в базе: {user_count}"
            )
        except Psycopg2Error as e:
            logging.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def create_tables(self):
        """Создает необходимые таблицы в базе данных."""
        try:
            self.cur.execute(
                """
CREATE TABLE IF NOT EXISTS users(
    user_id BIGINT PRIMARY KEY UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    grade INTEGER,
    letter TEXT
);
"""
            )
        except Psycopg2Error as e:
            logging.error(f"Ошибка при создании таблиц: {e}")
            raise

    def get_user_count(self):
        """Возвращает количество пользователей в базе данных."""
        try:
            self.cur.execute("SELECT COUNT(*) FROM users;")
            return self.cur.fetchone()[0]
        except Psycopg2Error as e:
            logging.error(f"Ошибка при подсчете пользователей: {e}")
            return 0

    def get_users(self):
        """
        Получает список всех пользователей из базы данных.

        Возвращает:
        list: Список кортежей, где каждый кортеж содержит идентификатор пользователя (user_id).

        Примечание:
        Если в базе данных нет пользователей, возвращается пустой список.
        """
        try:
            self.cur.execute("SELECT user_id FROM users;")
            return self.cur.fetchall()
        except Psycopg2Error as e:
            logging.error(f"Ошибка при получении списка пользователей: {e}")
            return []

    def user_exists(self, user_id: int):
        """
        Проверяет, существует ли пользователь в базе данных по заданному идентификатору.

        Параметры:
        user_id (int): Идентификатор пользователя, который необходимо проверить.

        Возвращает:
        bool: True, если пользователь с указанным user_id существует в базе данных, иначе False.
        """
        try:
            self.cur.execute(
                "SELECT user_id FROM users WHERE user_id = %s;", (user_id,)
            )
            return self.cur.fetchone() is not None
        except Psycopg2Error as e:
            logging.error(
                f"Ошибка при проверке существования пользователя {user_id}: {e}"
            )
            return False

    def add_user(self, user_id: int, grade: int, letter: str):
        """
        Добавляет нового пользователя в базу данных по заданному идентификатору.

        Параметры:
        - user_id (int): Идентификатор пользователя, который необходимо добавить в базу данных.
        - grade (int): Значение для поля grade.
        - letter (str): Значение для поля letter.
        """
        try:
            self.cur.execute(
                "INSERT INTO users (grade, letter, user_id) VALUES (%s, %s, %s);",
                (grade, letter, user_id),
            )
        except Psycopg2Error as e:
            logging.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            raise

    def get_admins(self):
        """
        Получает список всех администраторов из базы данных.

        Возвращает:
        list: Список кортежей, где каждый кортеж содержит user_id администратора.
        """
        try:
            self.cur.execute("SELECT user_id FROM users WHERE is_admin = TRUE;")
            return self.cur.fetchall()
        except Psycopg2Error as e:
            logging.error(f"Ошибка при получении списка администраторов: {e}")
            return []

    def update_user(self, user_id: int, grade: int, letter: str):
        """
        Обновляет данные о пользователе в базе данных по заданному идентификатору.

        Параметры:
        - user_id (int): Идентификатор пользователя, для которого необходимо изменить данные.
        - grade (int): Новое значение для поля grade.
        - letter (str): Новое значение для поля letter.
        """
        try:
            self.cur.execute(
                "UPDATE users SET grade = %s, letter = %s WHERE user_id = %s;",
                (grade, letter, user_id),
            )
        except Psycopg2Error as e:
            logging.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            raise

    def get_user(self, user_id: int):
        """
        Получает данные о пользователе из базы данных по заданному идентификатору.

        Параметры:
        - user_id (int): Идентификатор пользователя, для которого необходимо получить данные.

        Возвращает:
        - tuple: Кортеж, содержащий данные о пользователе из таблицы users.

        Примечание:
        - Если пользователь с указанным user_id не найден, возвращается None.
        """
        try:
            self.cur.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
            return self.cur.fetchone()
        except Psycopg2Error as e:
            logging.error(f"Ошибка при получении данных пользователя {user_id}: {e}")
            return None

    def get_grade(self, user_id: int):
        """
        Получает класс и букву класса пользователя.

        Параметры:
        - user_id (int): Идентификатор пользователя.

        Возвращает:
        - tuple: Кортеж (grade, letter) или None, если пользователь не найден.
        """
        try:
            self.cur.execute(
                "SELECT grade, letter FROM users WHERE user_id = %s;", (user_id,)
            )
            return self.cur.fetchone()
        except Psycopg2Error as e:
            logging.error(f"Ошибка при получении класса пользователя {user_id}: {e}")
            return None

    def get_active_users(self):
        """
        Получает список всех активных пользователей.

        Возвращает:
        list: Список кортежей (user_id, grade, letter) для всех активных пользователей.
        """
        try:
            self.cur.execute(
                "SELECT user_id, grade, letter FROM users WHERE is_active = TRUE;"
            )
            return self.cur.fetchall()
        except Psycopg2Error as e:
            logging.error(f"Ошибка при получении списка активных пользователей: {e}")
            return []

    def get_user_for_schedule(self, user_id: int):
        """
        Получает данные пользователя для отправки расписания.

        Параметры:
        - user_id (int): Идентификатор пользователя.

        Возвращает:
        - tuple: Кортеж (user_id, grade, letter) или None, если пользователь не найден или неактивен.
        """
        try:
            self.cur.execute(
                "SELECT user_id, grade, letter FROM users WHERE user_id = %s AND is_active = TRUE;",
                (user_id,),
            )
            return self.cur.fetchone()
        except Psycopg2Error as e:
            logging.error(
                f"Ошибка при получении данных пользователя {user_id} для расписания: {e}"
            )
            return None

    def close(self):
        """Закрывает соединение с базой данных."""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
            logging.info("Соединение с базой данных закрыто")
        except Exception as e:
            logging.error(f"Ошибка при закрытии соединения с БД: {e}")
