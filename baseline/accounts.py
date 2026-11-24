import re
from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash

from .catalog import CONSENT_TEXT, CONSENT_VERSION, INTAKE_QUESTIONS, PLAN

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class Signup:
    email: str
    name: str
    password: str
    goal: str
    prior_testing: str
    draw_time: str


class EmailInUse(Exception):
    pass


def normalize_email(value):
    return value.strip().lower()


def validate_signup(fields):
    name = " ".join(fields.get("name", "").split())
    email = normalize_email(fields.get("email", ""))
    password = fields.get("password", "")
    errors = {}

    if len(email) > 254 or not EMAIL.fullmatch(email):
        errors["email"] = "Enter a valid demo email address."
    if not 1 <= len(name) <= 100:
        errors["name"] = "Enter a name of up to 100 characters."
    if not 10 <= len(password) <= 128:
        errors["password"] = "Use between 10 and 128 characters for your password."
    for key, (question, choices) in INTAKE_QUESTIONS.items():
        if fields.get(key) not in choices:
            errors[key] = f"Choose an answer for “{question}”"
    if fields.get("consent") != "yes":
        errors["consent"] = "Confirm demo consent to place your order."
    if errors:
        return None, errors
    return Signup(
        email, name, password, fields["goal"], fields["prior_testing"], fields["draw_time"]
    ), {}


def authenticate_member(db, email, password):
    if not 1 <= len(password) <= 128:
        return None
    member = db.execute(
        "SELECT id, password_hash FROM members WHERE email = ?", (normalize_email(email),)
    ).fetchone()
    if member is not None and check_password_hash(member["password_hash"], password):
        return member["id"]
    return None


def create_member(db, signup, checkout_key):
    password_hash = generate_password_hash(signup.password)
    with db:
        # Serialize the retry lookup and all five writes, including concurrent POSTs.
        db.execute("BEGIN IMMEDIATE")
        prior = db.execute(
            """SELECT m.id, m.email, m.password_hash
               FROM purchases p JOIN members m ON m.id = p.member_id
               WHERE p.checkout_key = ?""",
            (checkout_key,),
        ).fetchone()
        if prior is not None:
            if prior["email"] == signup.email and check_password_hash(
                prior["password_hash"], signup.password
            ):
                return prior["id"]
            raise EmailInUse
        if db.execute("SELECT 1 FROM members WHERE email = ?", (signup.email,)).fetchone():
            raise EmailInUse

        member_id = db.execute(
            "INSERT INTO members (name, email, password_hash) VALUES (?, ?, ?)",
            (signup.name, signup.email, password_hash),
        ).lastrowid
        db.execute(
            """INSERT INTO intakes (member_id, goal, prior_testing, draw_time)
               VALUES (?, ?, ?, ?)""",
            (member_id, signup.goal, signup.prior_testing, signup.draw_time),
        )
        db.execute(
            "INSERT INTO consents (member_id, version, consent_text) VALUES (?, ?, ?)",
            (member_id, CONSENT_VERSION, CONSENT_TEXT),
        )
        purchase_id = db.execute(
            """INSERT INTO purchases (member_id, checkout_key, plan_code, amount_cents)
               VALUES (?, ?, ?, ?)""",
            (member_id, checkout_key, PLAN.code, PLAN.amount_cents),
        ).lastrowid
        db.execute(
            """INSERT INTO orders (member_id, purchase_id, kind, draw_center_id)
               VALUES (?, ?, 'baseline', (SELECT id FROM draw_centers WHERE code = ?))""",
            (member_id, purchase_id, PLAN.draw_center_code),
        )
    return member_id
