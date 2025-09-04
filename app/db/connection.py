import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def query(sql, params=None):
    connection = None
    try:
        with psycopg2.connect(
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
            port=os.getenv("port"),
            dbname=os.getenv("dbname")
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                
                if cursor.description:  
                    result = cursor.fetchall()
                    return result
                else:
                    connection.commit()
                    return None
    except psycopg2.Error as e:
        print(f"Query failed: {e}\nQuery: {sql}\nParams: {params}")
        if connection:
            connection.rollback()
        return None
    finally:
        if connection:
            connection.close()
