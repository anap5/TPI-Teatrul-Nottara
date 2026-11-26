from pathlib import Path
import subprocess
import sys

project_folder = Path(__file__).resolve().parent

def update_data():
    subprocess.run(
        [sys.executable, str(project_folder / "data_extract.py")],
        check=True,
        cwd=project_folder
    )

    subprocess.run(
        [sys.executable, str(project_folder / "database.py")],
        check=True,
        cwd=project_folder
    )

if __name__ == "__main__":
    update_data()