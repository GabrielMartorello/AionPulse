# SPDX-License-Identifier: GPL-3.0-only
import importlib.metadata
import shutil
import sys
from pathlib import Path

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if not python_license.exists():
    python_license = Path(sys.base_prefix) / "LICENSE"
if not python_license.exists():
    raise SystemExit("Python license not found")
shutil.copy2(python_license, destination / "Python-LICENSE.txt")
for package in ("lz4", "pyinstaller"):
    distribution = importlib.metadata.distribution(package)
    found = False
    for entry in distribution.files or ():
        if "license" in entry.name.lower() or "copying" in entry.name.lower():
            source = Path(distribution.locate_file(entry))
            if source.is_file():
                shutil.copy2(source, destination / f"{package}-{source.name}")
                found = True
    if not found:
        raise SystemExit(f"License not found: {package}")
for folder in ("tcl8.6", "tk8.6"):
    for source in (Path(sys.base_prefix) / "tcl" / folder, Path(sys.base_prefix) / "lib" / folder):
        for name in ("license.terms", "LICENSE"):
            if (source / name).exists():
                shutil.copy2(source / name, destination / f"{folder}-{name}")
if not (destination / "tcl8.6-license.terms").exists():
    shutil.copy2(
        Path(__file__).resolve().parent / "installer" / "licenses" / "tcl-license.terms",
        destination / "tcl8.6-license.terms",
    )
