@echo off
setlocal

set "SRC=%~dp0"
set "SKILL_DEST=%USERPROFILE%\.claude\skills\wechat-agent-report"
set "CONFIG_DIR=%USERPROFILE%\.claude\wechat-agent-report"

if not exist "%SKILL_DEST%\scripts" mkdir "%SKILL_DEST%\scripts"
if not exist "%CONFIG_DIR%\references" mkdir "%CONFIG_DIR%\references"

copy /Y "%SRC%SKILL.md" "%SKILL_DEST%\SKILL.md" >nul
copy /Y "%SRC%README.md" "%SKILL_DEST%\README.md" >nul
copy /Y "%SRC%config.example.json" "%SKILL_DEST%\config.example.json" >nul
copy /Y "%SRC%scripts\send_report.py" "%SKILL_DEST%\scripts\send_report.py" >nul
copy /Y "%SRC%scripts\send_ui_macos.sh" "%SKILL_DEST%\scripts\send_ui_macos.sh" >nul
copy /Y "%SRC%scripts\find_and_click.swift" "%SKILL_DEST%\scripts\find_and_click.swift" >nul
copy /Y "%SRC%references\*" "%CONFIG_DIR%\references\" >nul

if not exist "%CONFIG_DIR%\config.json" (
    copy /Y "%SRC%config.example.json" "%CONFIG_DIR%\config.json" >nul
    echo Created config: %CONFIG_DIR%\config.json
) else (
    echo Config exists, kept: %CONFIG_DIR%\config.json
)

echo Installed to %SKILL_DEST%
echo 1. Edit %CONFIG_DIR%\config.json and fill in wechat_name
echo 2. If needed: python -m pip install winsdk pillow
echo 3. List agents: python "%SKILL_DEST%\scripts\send_report.py" --list
echo 4. Preview: python "%SKILL_DEST%\scripts\send_report.py" --agent daily-summary --project "PROJECT" --title "TITLE" --background "PROJECT BACKGROUND" --summary "SUMMARY" --check
echo 5. Send: run the same command without --check

endlocal
