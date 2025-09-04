import bcrypt, random, uuid, datetime
from faker import Faker
from app.db.connection import query

fake = Faker()

def hash_password(plain_password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_admin_user():
    sql = """
    INSERT INTO users (id, username, email, password, birthday, avg_accuracy, avg_rt_ms, total_cpp, avatar_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    query(sql, (
        "6664a0be-4540-4a97-8756-8a5c3b6e30ba",
        "admin",
        "admin@gmail.com",
        hash_password("admin"),
        fake.date_of_birth(minimum_age=25, maximum_age=50),
        100.0,
        300.0,
        0.0,
        None
    ))
    print("Admin user created successfully.")
    print("Admin id: 6664a0be-4540-4a97-8756-8a5c3b6e30ba")

def seed_fake_users(n):
    sql = """
    INSERT INTO users (username, email, password, birthday, avg_accuracy, avg_rt_ms, total_cpp, avatar_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    for _ in range(n):
        query(sql, (
            fake.user_name(),
            fake.email(),
            hash_password("password123"),
            fake.date_of_birth(minimum_age=18, maximum_age=60),
            round(random.uniform(50, 100), 2),
            round(random.uniform(200, 1000), 2),
            round(random.uniform(0, 1000), 2),
            fake.image_url()
        ))
    print(f"{n} fake users inserted successfully.")

def seed_fake_games():
    base_games = [
        ("Stroop Test", "Measures attention, executive function, and rapid decision making.", "attention,executive,decision", True),
        ("Memory Grid", "Tests memory and visual recognition through grid-based tasks.", "memory,visual", True),
        ("Attention Math", "Mathematical problem-solving game that trains logical thinking and learning.", "math,problem-solving,attention", True),
        ("Task Switching", "Trains cognitive flexibility and executive control by switching between tasks.", "flexibility,executive,attention", True),
        ("Mental Rotation Task", "Tests spatial perception and visualization through mental object rotation.", "spatial,visual,attention", True),
    ]

    for name, description, tags, is_active in base_games:
        query("""
            INSERT INTO games (name, description, tags, is_active) 
            VALUES (%s, %s, %s, %s)
        """, (name, description, tags, is_active))

    print("Games inserted successfully.")
      

def seed_fake_runs_and_trials(max_trials_per_run):
    users = query("SELECT id FROM users")
    games = query("SELECT id FROM games")

    if not users or not games:
        print("No users or games found. Run fake users/games first.")
        return []

    trial_ids = []

    sql_run = """
    INSERT INTO runs (user_id, game_id, accuracy, rt_mean, cpp_score)
    VALUES (%s, %s, %s, %s, %s) RETURNING id
    """
    sql_trial = """
    INSERT INTO trials (run_id, trial_number, is_correct, accuracy, rt_ms, cpp_score)
    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """

    for user in users:
        user_id = user[0]
        for game in games:
            game_id = game[0]
            acc = round(random.uniform(50, 100), 2)
            rt = round(random.uniform(200, 1000), 2)
            cpp = round(random.uniform(0, 1000), 2)

            run_id = query(sql_run, (user_id, game_id, acc, rt, cpp))[0][0]

            num_trials = random.randint(1, max_trials_per_run)
            for t in range(1, num_trials + 1):
                is_correct = random.choice([True, False])
                trial_acc = round(random.uniform(50, 100), 2)
                rt_ms = round(random.uniform(200, 1000), 2)
                cpp_score = round(random.uniform(0, 1000), 2)

                trial_id = query(sql_trial, (run_id, t, is_correct, trial_acc, rt_ms, cpp_score))[0][0]
                trial_ids.append((trial_id, user_id, game_id))

    print(f"Runs and trials seeded successfully. Total trials: {len(trial_ids)}")
    return trial_ids

def seed_fake_leaderboard(trial_ids):
    if not trial_ids:
        print("No trials to seed leaderboard.")
        return

    for trial_id, user_id, game_id in trial_ids:
        game_row = query("SELECT name FROM games WHERE id = %s", (game_id,))
        if not game_row:
            continue
        game_name = game_row[0][0]
        accuracy = round(random.uniform(50, 100), 2)
        rt_mean = round(random.uniform(200, 1000), 2)
        cpp_score = random.randint(0, 1000)

        sql = """
        INSERT INTO leaderboard (user_id, game_name, trial_id, accuracy, rt_mean, cpp_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        query(sql, (user_id, game_name, trial_id, accuracy, rt_mean, cpp_score))
    print("Leaderboard seeded successfully.")

def seed_database():
    seed_admin_user()
    seed_fake_users(3)

    seed_fake_games()
    trial_ids = seed_fake_runs_and_trials(max_trials_per_run=2)
    seed_fake_leaderboard(trial_ids)

    print("Database seeded successfully.")
