from dotenv import load_dotenv
import os
import pymysql
from pymysql.cursors import DictCursor

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        cursorclass=DictCursor,
        autocommit=True
    )

def close_connection(connection):
    if connection:
        connection.close()