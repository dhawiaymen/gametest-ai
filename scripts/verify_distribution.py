"""Build an archive, extract it elsewhere, then execute that exact packaged app."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

source, executable, slug = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
assets = Path("release-assets")
assets.mkdir(exist_ok=True)
archive = assets / f"{slug}-0.1.0-windows-x64.zip"
shutil.make_archive(str(archive.with_suffix("")), "zip", source.parent, source.name)
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None, "Corrupt ZIP member"
    assert len(zipped.namelist()) == len(set(zipped.namelist())), "Duplicate ZIP entries"
    assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in zipped.namelist())
    assert any(n.endswith("licenses/inventory.json") for n in zipped.namelist())
    with tempfile.TemporaryDirectory(prefix="release extraction with spaces ") as temporary:
        target = Path(temporary)
        zipped.extractall(target)
        report_path = target / "smoke.json"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.pop("GAMETEST_BROWSER_PATH", None)
        result = subprocess.run([str(target / executable / (executable + ".exe")), "--smoke-test", str(report_path)], cwd=target, env=env, timeout=180)
        assert result.returncode == 0, f"Executable failed: {result.returncode}"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == "passed", report
        report["archive"] = archive.name
        report["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        report["commit"] = os.environ.get("GITHUB_SHA", "local build")
        (assets / "windows-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
lines = []
for path in sorted(assets.iterdir()):
    if path.is_file() and path.name != "SHA256SUMS.txt":
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        lines.append(f"{digest}  {path.name}")
(assets / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
