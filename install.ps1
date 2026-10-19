$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDest = Join-Path $env:USERPROFILE ".claude\skills\wechat-agent-report"
$ConfigDir = Join-Path $env:USERPROFILE ".claude\wechat-agent-report"

New-Item -ItemType Directory -Force -Path (Join-Path $SkillDest "scripts"), (Join-Path $ConfigDir "references") | Out-Null
Copy-Item (Join-Path $Src "SKILL.md") (Join-Path $SkillDest "SKILL.md") -Force
Copy-Item (Join-Path $Src "scripts\send_report.py") (Join-Path $SkillDest "scripts\send_report.py") -Force
Copy-Item (Join-Path $Src "scripts\send_ui_macos.sh") (Join-Path $SkillDest "scripts\send_ui_macos.sh") -Force
Copy-Item (Join-Path $Src "scripts\send_ui_windows.ps1") (Join-Path $SkillDest "scripts\send_ui_windows.ps1") -Force
Copy-Item (Join-Path $Src "references\*") (Join-Path $ConfigDir "references") -Force

$Config = Join-Path $ConfigDir "config.json"
if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $Src "config.example.json") $Config -Force
    Write-Host "已创建配置：$Config"
} else {
    Write-Host "配置已存在，未覆盖：$Config"
}

Write-Host "安装完成。"
Write-Host "1. 编辑 $Config，填写 wechat_name（微信里显示的对话名）"
Write-Host "2. 运行：python `"$SkillDest\scripts\send_report.py`" --list"
Write-Host "3. 发送：python `"$SkillDest\scripts\send_report.py`" --agent daily-summary --title `"标题`" --summary `"完成内容`""
