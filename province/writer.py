import mysql.connector
from mysql.connector import Error


def create_database(connection, db_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"数据库 {db_name} 创建成功")
    except Error as e:
        print(f"创建数据库时发生错误: {e}")
    finally:
        cursor.close()


def create_table(connection, table_name, schema):
    try:
        cursor = connection.cursor()
        cursor.execute(f"USE {connection.database}")
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        cursor.execute(create_table_sql)
        print(f"表 {table_name} 创建成功")
    except Error as e:
        print(f"创建表时发生错误: {e}")
    finally:
        cursor.close()


def mysql_writer(name, data):
    try:
        with mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='ztw1016..',
            connect_timeout=20
        ) as connection:
            create_database(connection, 'document')
            connection.database = 'document'
            create_table(connection, name, "link VARCHAR(255), title VARCHAR(255) PRIMARY KEY, fileNum VARCHAR(255), "
                                           "columnName VARCHAR(255), classNames VARCHAR(255), "
                                           "createDate DATE, content TEXT")
            if connection.is_connected():
                print(f"成功连接到数据库document")
                try:
                    with connection.cursor() as cursor:
                        all_columns = set().union(*[d.keys() for d in data])
                        columns = ', '.join(all_columns)
                        placeholders = ', '.join(['%s'] * len(all_columns))
                        query = f"INSERT IGNORE INTO {name} ({columns}) VALUES ({placeholders})"
                        prepared_data = [tuple(d[col] for col in all_columns) for d in data]
                        cursor.executemany(query, prepared_data)
                        connection.commit()
                    print(f"数据已成功插入到表 {name}")

                except Exception as e:
                    print(f"插入数据时发生错误: {e}")
                    connection.rollback()

    except Error as e:
        print(f"发生错误: {e}")

    finally:
        pass

