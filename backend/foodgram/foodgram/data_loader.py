import csv
import os
from dotenv import load_dotenv
import psycopg2

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение данных для подключения к базе данных из переменных окружения
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
csv_file = 'data/ingredients.csv'
table_name = 'recipes_ingredient'


def load_data_from_csv():
    connection = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password,
        options="-c client_encoding=utf8"
    )

    try:
        cursor = connection.cursor()
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                cursor.execute(
                    f"INSERT INTO {table_name} (name, measurement_unit) VALUES (%s, %s)",
                    (row[0], row[1])
                )
        connection.commit()

        print("Данные успешно загружены в таблицу.")

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при загрузке данных в таблицу:", error)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == '__main__':
    load_data_from_csv()
