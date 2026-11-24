import argparse
import tempfile
from pathlib import Path

from . import create_app, instance_directory


def main():
    parser = argparse.ArgumentParser(description="Run the local Baseline Lab Demo website.")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--fresh", action="store_true", help="Start with a separate empty database.")
    parser.add_argument("--seed", action="store_true", help="Seed the prepared member without starting the server.")
    options = parser.parse_args()

    directory = instance_directory()
    if options.fresh:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="demo-", dir=directory))
    app = create_app(directory)
    print(f"Baseline database: {app.config['DATABASE']}", flush=True)
    if options.seed:
        from .db import get_db
        from .seed import seed_prepared_member

        with app.app_context():
            member_id = seed_prepared_member(get_db())
        print(f"Prepared case: /staff/members/{member_id}")
        return
    app.run(host="127.0.0.1", port=options.port, debug=False, load_dotenv=False)


if __name__ == "__main__":
    main()
