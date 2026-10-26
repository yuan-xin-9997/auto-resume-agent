@echo off
"%~dp0cli\auto-resume-agent.exe" install
if errorlevel 1 (
  echo Installation failed.
  pause
  exit /b 1
)
start "" "%LOCALAPPDATA%\Programs\AutoResumeAgent\gui\AutoResumeAgent.exe"
