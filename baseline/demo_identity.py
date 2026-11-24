from werkzeug.security import check_password_hash, generate_password_hash

from .accounts import normalize_email

STAFF_EMAIL = "staff@example.test"
STAFF_PASSWORD = "BaselineStaffDemo-27!"
PREPARED_EMAIL = "casey.harper@example.test"
PREPARED_PASSWORD = "BaselineCaseyDemo-27!"


def initialize_staff(db):
    if db.execute("SELECT 1 FROM staff_users WHERE email = ?", (STAFF_EMAIL,)).fetchone() is None:
        db.execute(
            "INSERT INTO staff_users (email, password_hash) VALUES (?, ?)",
            (STAFF_EMAIL, generate_password_hash(STAFF_PASSWORD)),
        )


def authenticate_staff(db, email, password):
    if not 1 <= len(password) <= 128:
        return None
    staff = db.execute(
        "SELECT id, password_hash FROM staff_users WHERE email = ?", (normalize_email(email),)
    ).fetchone()
    if staff is not None and check_password_hash(staff["password_hash"], password):
        return staff["id"]
    return None
