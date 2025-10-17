import mysql.connector
from mysql.connector import Error
import datetime
from typing import Optional, Dict
from config.settings import VPN_SERVER_IP

class UserDatabaseMySQL:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self._connect()

    def _connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port="3308",
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            self._create_table_if_not_exists()
        except Error as e:
            print(f"Ошибка подключения к MySQL: {e}")

    def _create_table_if_not_exists(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            vpn_uuid VARCHAR(255),
            vpn_config TEXT,
            active BOOLEAN,
            expiry_time BIGINT,
            created_at DATETIME
        )
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        cursor.close()

    def add_user(self, user_id: int, username: str, vpn_uuid: str, vpn_config: str, expiry_time: int):
        try:
            query = """
                    INSERT INTO users (user_id, username, vpn_uuid, vpn_config, active, expiry_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      username=VALUES(username),
                      vpn_uuid=VALUES(vpn_uuid),
                      vpn_config=VALUES(vpn_config),
                      active=VALUES(active),
                      expiry_time=VALUES(expiry_time),
                      created_at=VALUES(created_at)
                    """
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, (
                    user_id,
                    username,
                    vpn_uuid,
                    vpn_config,
                    True,
                    expiry_time,
                    datetime.datetime.now()
                ))
                self.connection.commit()
                cursor.close()
                print("[MySQL] Пользователь добавлен/обновлен")
            except Exception as e:
                print(f"[MySQL] Ошибка добавления пользователя: {e}")
        except Exception as e:
            print('DB error:', e)


    def get_user(self, user_id: int) -> Optional[Dict]:
        query = "SELECT user_id, username, vpn_uuid, vpn_config, active, expiry_time, created_at FROM users WHERE user_id = %s"
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result
        return None


    def deactivate_user(self, user_id: int):
        query = "UPDATE users SET active = FALSE WHERE user_id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (user_id,))
        cursor.close()
