"""Retain installed dependency notices and identify exact build dependencies."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys

out = Path(sys.argv[1]) / "licenses"
out.mkdir(exist_ok=True)
inventory = []
for dist in metadata.distributions():
    name = dist.metadata["Name"]
    record = {"name": name, "version": dist.version, "license": dist.metadata.get("License-Expression") or dist.metadata.get("License"), "notice_files": []}
    for entry in dist.files or []:
        label = str(entry).lower()
        if ("license" in label or "notice" in label or "copying" in label) and not label.endswith((".py", ".pyc")) and ".." not in entry.parts:
            source = Path(dist.locate_file(entry))
            if source.is_file():
                target = out / name / str(entry)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                record["notice_files"].append(str(target.relative_to(out)))
    inventory.append(record)
for path in [Path(sys.base_prefix)/"LICENSE.txt", *Path(sys.base_prefix).glob("tcl/*/license*")]:
    if path.is_file():
        target = out/"python-tcl-tk"/path.parent.name/path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
(out/"inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
assert inventory, "No dependency inventory collected"
