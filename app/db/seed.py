import bcrypt
from app.db.connection import get_connection, close_connection

def seed_initial_data():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", ("admin",))
            if not cursor.fetchone():
                hashed_pw = bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    ("admin", "admin@admin.com", hashed_pw)
                )
    finally:
        close_connection(conn)
