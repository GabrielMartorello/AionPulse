# SPDX-License-Identifier: GPL-3.0-only
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
destination = Path(sys.argv[1])
destination.parent.mkdir(parents=True, exist_ok=True)
files = set()
for pattern in ("*.py", "*.ps1", "*.cs", "*.cmd", "*.md", "*.toml", "requirements*.txt"):
    files.update(root.glob(pattern))
files.update(root / name for name in ("LICENSE", ".gitignore", ".gitattributes"))
for folder, extensions in {
    "assets": {".png", ".ico"},
    "docs": {".md"},
    "tests": {".py"},
    "installer": {".iss", ".terms", ".txt"},
    ".github": {".yml", ".yaml"},
}.items():
    files.update(
        path for path in (root / folder).rglob("*") if path.is_file() and path.suffix in extensions
    )
with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, "AionPulse/" + path.relative_to(root).as_posix())
