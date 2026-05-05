import subprocess
import sys
from pathlib import Path


def main():
    requirements = Path(__file__).with_name("requirements.txt")

    if not requirements.exists():
        raise FileNotFoundError(f"Could not find {requirements}")

    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements),
    ])


if __name__ == "__main__":
    main()
