import sqlite3
from pathlib import Path

from flask import current_app, g

from .catalog import PLAN

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
    db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA.read_text(encoding="utf-8") + "\nCOMMIT;")
    with db:
        db.execute(
            "INSERT OR IGNORE INTO draw_centers (code, name) VALUES (?, ?)",
            (PLAN.draw_center_code, PLAN.draw_center),
        )
