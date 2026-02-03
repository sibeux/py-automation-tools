import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
README_PATH = BASE_DIR / "README.md"

EXCLUDE_DIRS = {".git", "__pycache__"}
EXCLUDE_FILES = {"generate_readme.py"}

def get_docstring(py_file):
    try:
        with open(py_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines and lines[0].startswith(('"""', "'''")):
                return lines[1].strip()
    except Exception:
        pass
    return None

def generate_tools_section():
    lines = ["## 🛠 Tools yang Tersedia\n"]

    for folder in sorted(BASE_DIR.iterdir()):
        if not folder.is_dir() or folder.name in EXCLUDE_DIRS:
            continue

        py_files = [
            f for f in folder.iterdir()
            if f.suffix == ".py" and f.name not in EXCLUDE_FILES
        ]

        if not py_files:
            continue

        lines.append(f"### {folder.name.capitalize()}")
        for py in sorted(py_files):
            desc = get_docstring(py)
            name = py.stem.replace("_", " ")
            if desc:
                lines.append(f"- **{name}** — {desc}")
            else:
                lines.append(f"- **{name}**")
        lines.append("")

    return "\n".join(lines)

def update_readme():
    content = ""
    if README_PATH.exists():
        content = README_PATH.read_text(encoding="utf-8")

    start = "## 🛠 Tools yang Tersedia"
    if start in content:
        content = content.split(start)[0].rstrip()

    new_content = content + "\n\n" + generate_tools_section()
    README_PATH.write_text(new_content.strip() + "\n", encoding="utf-8")

if __name__ == "__main__":
    update_readme()
    print("README.md updated.")
