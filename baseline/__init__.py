import os
import secrets
import tempfile
from datetime import timedelta
from pathlib import Path

from flask import Flask

from . import db

DEFAULT_INSTANCE = Path(__file__).resolve().parent.parent / "instance"


def instance_directory():
    return Path(os.environ.get("BASELINE_INSTANCE_DIR", DEFAULT_INSTANCE)).resolve()


def session_key(directory):
    path = directory / ".session-key"
    if not path.exists():
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as temporary:
            temporary.write(secrets.token_bytes(32))
        draft = Path(temporary.name)
        try:
            os.link(draft, path)
        except FileExistsError:
            # Another process initialized this instance first.
            pass
        finally:
            draft.unlink()
    return path.read_bytes()


def create_app(instance_path=None):
    directory = Path(instance_path or instance_directory()).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    app = Flask(__name__, instance_path=str(directory), static_folder=None)
    app.config.from_mapping(
        DATABASE=directory / "baseline.sqlite3",
        SECRET_KEY=session_key(directory),
        SESSION_COOKIE_NAME="baseline_member",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        MAX_CONTENT_LENGTH=16 * 1024,
        TRUSTED_HOSTS=["127.0.0.1", "localhost", "[::1]"],
    )

    from .web import web
    from .web.staff import staff
    from .api import api
    from .schedule import visit_time

    app.register_blueprint(web)
    app.register_blueprint(staff)
    app.register_blueprint(api)
    app.add_template_filter(visit_time, "visit_time")
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.initialize()
    return app
