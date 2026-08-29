import bcrypt
from database.database import get_connection


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_user(full_name, email, password):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            return False, "Email already registered."
        conn.execute("INSERT INTO users(full_name,email,password) VALUES(?,?,?)", (full_name, email, hash_password(password)))
        conn.commit()
        return True, "User registered successfully."
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection(); row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone(); conn.close(); return row


def login_user(email, password):
    user = get_user_by_email(email)
    if user is None:
        return False, "User not found."
    try:
        ok = verify_password(password, user["password"])
    except Exception:
        ok = False
    return (True, user) if ok else (False, "Incorrect password.")


def get_user_by_id(user_id):
    conn = get_connection(); row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone(); conn.close(); return row


def update_password(user_id, current_password, new_password):
    user = get_user_by_id(user_id)
    if user is None:
        return False, "User not found."
    if not verify_password(current_password, user["password"]):
        return False, "Current password is incorrect."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    conn = get_connection(); conn.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), user_id)); conn.commit(); conn.close()
    return True, "Password updated successfully."


def update_full_name(user_id, new_name):
    new_name=(new_name or "").strip()
    if not new_name:
        return False, "Name cannot be empty."
    conn=get_connection(); conn.execute("UPDATE users SET full_name=? WHERE id=?", (new_name,user_id)); conn.commit(); conn.close()
    return True, "Name updated successfully."
