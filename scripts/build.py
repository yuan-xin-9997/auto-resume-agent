"""Native PyInstaller bundles. Run on each target OS/architecture."""
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import importlib.metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
# Conda keeps native dependencies such as sqlite3.dll in Library/bin, which is
# not always on PATH when the build starts from a plain shell.
conda_bin = Path(sys.base_prefix) / "Library" / "bin"
if os.name == "nt" and conda_bin.is_dir():
    os.environ["PATH"] = str(conda_bin) + os.pathsep + os.environ.get("PATH", "")
sys.path.insert(0, str(ROOT / "src"))
from auto_resume_agent import __version__

system = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}[platform.system()]
arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
assets = ROOT / "src/auto_resume_agent/assets"
common = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--paths", "src",
          "--collect-data", "auto_resume_agent", "--exclude-module", "PySide6.QtWebEngineCore",
          "--exclude-module", "PySide6.QtQml", "--exclude-module", "PySide6.QtQuick"]
subprocess.run(common + ["--name", "auto-resume-agent", "scripts/cli_entry.py"], check=True)
icon = assets / ("icon.icns" if system == "macos" else "icon.ico" if system == "windows" else "icon.png")
gui = common + ["--name", "AutoResumeAgent", "--windowed", "--icon", str(icon)]
if system == "macos":
    gui += ["--osx-bundle-identifier", "io.github.yuan-xin-9997.auto-resume-agent"]
subprocess.run(gui + ["scripts/gui_entry.py"], check=True)
stage = ROOT / "build" / f"AutoResumeAgent-v{__version__}-{system}-{arch}"
stage.mkdir(parents=True, exist_ok=True)
shutil.copytree(ROOT / "dist/auto-resume-agent", stage / "cli", dirs_exist_ok=True)
if system == "macos":
    subprocess.run(["ditto", str(ROOT / "dist/AutoResumeAgent.app"), str(stage / "AutoResumeAgent.app")], check=True)
else:
    shutil.copytree(ROOT / "dist/AutoResumeAgent", stage / "gui", dirs_exist_ok=True)
for name in ("README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / name, stage / name)
shutil.copytree(ROOT / "packaging" / system, stage, dirs_exist_ok=True)
shutil.copytree(assets, stage / "assets", dirs_exist_ok=True)
licenses = stage / "licenses"
licenses.mkdir(exist_ok=True)
shutil.copytree(ROOT / "licenses", licenses, dirs_exist_ok=True)
for distribution in importlib.metadata.distributions():
    name = distribution.metadata["Name"]
    if name.lower().startswith(("pyside", "shiboken", "pyinstaller")):
        for file in distribution.files or []:
            if "license" in str(file).lower() or "copying" in str(file).lower():
                source = distribution.locate_file(file)
                if source.is_file():
                    dest = licenses / name / Path(str(file)).name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.is_file():
    shutil.copy2(python_license, licenses / "PYTHON-LICENSE.txt")
release = ROOT / "dist/release"
release.mkdir(exist_ok=True)
base = release / stage.name
if system == "windows":
    output = Path(shutil.make_archive(str(base), "zip", stage.parent, stage.name))
else:
    output = Path(shutil.make_archive(str(base), "gztar", stage.parent, stage.name))
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_name(output.name + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
print(output)
