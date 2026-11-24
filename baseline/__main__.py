import argparse
import tempfile
from pathlib import Path

from . import create_app, instance_directory


def main():
    parser = argparse.ArgumentParser(description="Run the local Baseline Lab Demo website.")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--fresh", action="store_true", help="Start with a separate empty database.")
    options = parser.parse_args()

    directory = instance_directory()
    if options.fresh:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="demo-", dir=directory))
    app = create_app(directory)
    print(f"Baseline database: {app.config['DATABASE']}", flush=True)
    app.run(host="127.0.0.1", port=options.port, debug=False, load_dotenv=False)


if __name__ == "__main__":
    main()
