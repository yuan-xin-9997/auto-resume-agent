"""Per-user Windows deployment, with a stable shortcut target and untouched state."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from . import __version__
from .paths import data_dir
from .protocol import NO_WINDOW, external_environment, external_spawn


def validate_package(source):
    source = Path(source).resolve()
    for name in ("gui/AutoResumeAgent.exe", "cli/auto-resume-agent.exe"):
        if not (source / name).is_file():
            raise ValueError("invalid_windows_package")
    return source


def install():
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise ValueError("install_requires_windows_release_cli")
    source = validate_package(Path(sys.executable).parent.parent)
    programs = (Path(os.environ["LOCALAPPDATA"]) / "Programs").resolve()
    programs.mkdir(parents=True, exist_ok=True)
    target = programs / "AutoResumeAgent"
    # Never move an installation redirected outside its explicitly owned parent.
    if target.resolve().parent != programs or data_dir().resolve().is_relative_to(target.resolve()):
        raise ValueError("unsafe_install_location")
    env = external_environment()
    env["ARA_INSTALL_TARGET"] = str(target)
    if source != target.resolve():
        backup = programs / ("AutoResumeAgent.previous-" + uuid.uuid4().hex[:8])
        assert backup.resolve().parent == programs
        with tempfile.TemporaryDirectory(prefix=".AutoResumeAgent-stage-", dir=programs) as temporary:
            stage = Path(temporary).resolve() / "package"
            assert stage.is_relative_to(programs)
            shutil.copytree(source, stage)
            # Only stop this product under the stable install directory. Other apps are untouched.
            stop = '''$root=$env:ARA_INSTALL_TARGET+[IO.Path]::DirectorySeparatorChar
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -in @('AutoResumeAgent.exe','auto-resume-agent.exe') -and $_.ExecutablePath -and
  $_.ExecutablePath.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -ErrorAction Stop
  Wait-Process -Id $_.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
}
'''
            powershell(stop, env)
            if target.exists():
                target.rename(backup)
            try:
                stage.rename(target)
            except OSError:
                if backup.exists() and not target.exists():
                    backup.rename(target)
                raise
    shortcut_script = '''$ErrorActionPreference='Stop'
$exe=Join-Path $env:ARA_INSTALL_TARGET 'gui/AutoResumeAgent.exe'
$shell=New-Object -ComObject WScript.Shell
$desktop=[Environment]::GetFolderPath('Desktop')
$menu=Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs'
$taskbar=Join-Path $env:APPDATA 'Microsoft/Internet Explorer/Quick Launch/User Pinned/TaskBar'
# Retarget existing product shortcuts, including differently named shortcuts.
foreach($folder in @($desktop,$menu,$taskbar)) {
  if(Test-Path -LiteralPath $folder) {
    Get-ChildItem -LiteralPath $folder -Filter '*.lnk' -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
      $link=$shell.CreateShortcut($_.FullName)
      if([IO.Path]::GetFileName($link.TargetPath) -eq 'AutoResumeAgent.exe') {
        $link.TargetPath=$exe; $link.WorkingDirectory=$env:ARA_INSTALL_TARGET
        $link.IconLocation=$exe+',0'; $link.Save()
      }
    }
  }
}
foreach($folder in @($desktop,$menu)) {
  $link=$shell.CreateShortcut((Join-Path $folder 'Auto Resume Agent.lnk'))
  $link.TargetPath=$exe; $link.WorkingDirectory=$env:ARA_INSTALL_TARGET
  $link.Description='Auto Resume Agent'; $link.IconLocation=$exe+',0'; $link.Save()
}
'''
    powershell(shortcut_script, env)
    manifest = {"version": __version__, "directory": str(target), "state_directory": str(data_dir())}
    (target / "installed.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def powershell(script, env):
    with external_spawn():
        process = subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    try:
        process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise OSError("windows_install_step_timeout") from None
    if process.returncode:
        raise OSError("windows_install_step_failed")
