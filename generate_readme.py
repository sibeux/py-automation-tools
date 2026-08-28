import os
from pathlib import Path
from collections import defaultdict

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

    tools_dict = defaultdict(list)

    # Cari semua file .py secara rekursif
    for py_file in BASE_DIR.rglob("*.py"):
        if py_file.name in EXCLUDE_FILES:
            continue
        
        rel_parts = py_file.relative_to(BASE_DIR).parts
        
        # Skip jika ada bagian folder yang masuk dalam EXCLUDE_DIRS
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        
        # Skip jika file .py berada langsung di root directory
        if len(rel_parts) == 1:
            continue
            
        rel_folder = py_file.parent.relative_to(BASE_DIR).as_posix()
        tools_dict[rel_folder].append(py_file)

    # Urutkan berdasarkan path folder
    for folder in sorted(tools_dict.keys()):
        py_files = sorted(tools_dict[folder])
        
        # Format nama folder "folder/subfolder" menjadi "Folder / Subfolder"
        folder_display = " / ".join(p.capitalize() for p in folder.split("/"))
        
        lines.append(f"### {folder_display}")
        for py in py_files:
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
