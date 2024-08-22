import argparse

from pathlib import Path

from .app import run_app


def validate_file(file: str) -> Path:
    if (path := Path(file)).is_file():
        return path
    else:
        raise FileNotFoundError(file)


def main():
    parser = argparse.ArgumentParser(description="Launches the JingleBox!")
    parser.add_argument(
        "jingles_path",
        nargs="?",
        metavar="FILE",
        type=validate_file,
        default=None,
        help="path to jingles' configuration",
    )
    args = parser.parse_args()

    run_app(jingles_path=args.jingles_path)


if __name__ == "__main__":
    main()
