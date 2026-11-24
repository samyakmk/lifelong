import sqlite3
from pathlib import Path

from flask import current_app, g

from .catalog import PLAN
from .demo_identity import initialize_staff
from .schedule import seed_slots

SCHEMA = Path(__file__).with_name("schema.sql")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize():
    db = get_db()
    with db:
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA.read_text(encoding="utf-8"))
        columns = db.execute("PRAGMA table_info(appointments)").fetchall()
        if not any(column["name"] == "slot_id" for column in columns):
            db.execute("ALTER TABLE appointments ADD COLUMN slot_id INTEGER REFERENCES draw_slots(id)")
        order_columns = db.execute("PRAGMA table_info(orders)").fetchall()
        if not any(column["name"] == "approved_at" for column in order_columns):
            db.execute("ALTER TABLE orders ADD COLUMN approved_at TEXT")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_appointment_per_slot ON appointments(slot_id)")
        db.execute(
            "INSERT OR IGNORE INTO draw_centers (code, name) VALUES (?, ?)",
            (PLAN.draw_center_code, PLAN.draw_center),
        )
        initialize_staff(db)
        seed_slots(db)
