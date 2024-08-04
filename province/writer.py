import mysql.connector
from mysql.connector import Error


def mysql_writer(name, data):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='document',
            user='root',
            password='ztw1016..',  # 替换为你的 MySQL 密码
            connect_timeout=20
        )

        if connection.is_connected():
            print(f"成功连接到数据库{name}")
            cursor = connection.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            sql = f"INSERT IGNORE INTO {name} ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(data.values()))
            connection.commit()
            print(f"数据已成功插入到表 {name}")

    except Error as e:
        print(f"发生错误: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭")
