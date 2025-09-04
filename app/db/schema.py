from app.db.connection import query
from app.db.seed import seed_database

def drop_tables():
    query("DROP TABLE IF EXISTS leaderboard;")
    query("DROP TABLE IF EXISTS trials;")
    query("DROP TABLE IF EXISTS runs;")
    query("DROP TABLE IF EXISTS games;")
    query("DROP TABLE IF EXISTS users;")
    print("Tables dropped successfully.")

def create_extension_pgcrypto():
    query("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

def create_users_table():
    query("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            birthday DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT NULL,
            last_active TIMESTAMP DEFAULT NULL,
            avatar_url TEXT DEFAULT NULL,
            avg_accuracy FLOAT DEFAULT 0,
            avg_rt_ms FLOAT DEFAULT 0,
            total_cpp FLOAT DEFAULT 0
        );
    """)
    print("Users table created successfully.")

def create_games_table():
    query("""
        CREATE TABLE IF NOT EXISTS games (
            id SERIAL PRIMARY KEY,
            name VARCHAR(20) NOT NULL,
            description TEXT DEFAULT NULL,
            tags VARCHAR(255) DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Games table created successfully.")

def create_runs_table():
    query("""
        CREATE TABLE runs (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            game_id INT NOT NULL,
            accuracy FLOAT NOT NULL,
            rt_mean FLOAT NOT NULL,
            cpp_score FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
        );
    """)
    print("Runs table created successfully.")

def create_trials_table():
    query("""
        CREATE TABLE trials (
            id SERIAL PRIMARY KEY,
            run_id INT NOT NULL,
            trial_number INT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            accuracy FLOAT NOT NULL,
            rt_ms FLOAT NOT NULL,
            cpp_score FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
        );
    """)
    print("Trials table created successfully.")

def create_leaderboard_table():
    query("""
        CREATE TABLE leaderboard (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            game_name VARCHAR(100) NOT NULL,
            trial_id INT NOT NULL,
            accuracy FLOAT NOT NULL,
            rt_mean FLOAT NOT NULL,
            cpp_score INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (trial_id) REFERENCES trials(id) ON DELETE CASCADE
        );
    """)
    print("Leaderboard table created successfully.")

def initialize_database():
    drop_tables()
    create_extension_pgcrypto()
    create_users_table()
    create_games_table()
    create_runs_table()
    create_trials_table()
    create_leaderboard_table()

    seed_database()

    print("Database initialized successfully.")
