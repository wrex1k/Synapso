from app.db.connection import get_connection, close_connection

def create_tables():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME DEFAULT NULL,
                    active BOOLEAN DEFAULT FALSE,
                    last_logout DATETIME DEFAULT NULL,
                    avatar_url TEXT DEFAULT NULL
                );
            """)
    finally:
        close_connection(conn)
