from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "dist" / "baseline-web.zip"
ROOT_FILES = (".gitignore", "package.json", "requirements.txt", "README.md")
SOURCE_DIRS = ("baseline", "docs", "scripts", "tests")
SOURCE_TYPES = {".py", ".sql", ".html", ".css", ".js", ".mjs", ".png", ".md", ".json"}


def main():
    files = [ROOT / name for name in ROOT_FILES]
    for source in SOURCE_DIRS:
        files.extend(
            path for path in (ROOT / source).rglob("*")
            if path.is_file() and path.suffix in SOURCE_TYPES and not path.name.startswith(".")
        )

    EXPORT.parent.mkdir(exist_ok=True)
    with ZipFile(EXPORT, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, arcname=path.relative_to(ROOT))
    print(EXPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
