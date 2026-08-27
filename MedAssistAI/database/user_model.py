import bcrypt
from database.database import get_connection


# -----------------------------
# Hash Password
# -----------------------------
def hash_password(password):
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# -----------------------------
# Verify Password
# -----------------------------
def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# -----------------------------
# Create User
# -----------------------------
def create_user(full_name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    if cursor.fetchone():
        conn.close()
        return False, "Email already registered."

    hashed_password = hash_password(password)

    cursor.execute("""
        INSERT INTO users(full_name, email, password)
        VALUES (?, ?, ?)
    """, (full_name, email, hashed_password))

    conn.commit()
    conn.close()

    return True, "User registered successfully."


# -----------------------------
# Get User by Email
# -----------------------------
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    return user


# -----------------------------
# Login User
# -----------------------------
def login_user(email, password):

    user = get_user_by_email(email)

    if user is None:
        return False, "User not found."

    if verify_password(password, user["password"]):
        return True, user

    return False, "Incorrect password."


# -----------------------------
# Get User by ID
# -----------------------------
def get_user_by_id(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return user
