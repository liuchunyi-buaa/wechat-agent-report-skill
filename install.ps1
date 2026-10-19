$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDest = Join-Path $env:USERPROFILE ".claude\skills\wechat-agent-report"
$ConfigDir = Join-Path $env:USERPROFILE ".claude\wechat-agent-report"

New-Item -ItemType Directory -Force -Path (Join-Path $SkillDest "scripts"), $ConfigDir | Out-Null
Copy-Item (Join-Path $Src "SKILL.md") (Join-Path $SkillDest "SKILL.md") -Force
Copy-Item (Join-Path $Src "scripts\send_report.py") (Join-Path $SkillDest "scripts\send_report.py") -Force

$Config = Join-Path $ConfigDir "config.json"
if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $Src "config.example.json") $Config -Force
    Write-Host "已创建配置：$Config"
} else {
    Write-Host "配置已存在，未覆盖：$Config"
}

Write-Host "安装完成。"
Write-Host "1. 编辑 $Config，把 clawbot_dir 改成 Windows 上的 ClawBot 目录"
Write-Host "2. 确认已安装依赖：python -m pip install requests cryptography"
Write-Host "3. 运行：python `"$SkillDest\scripts\send_report.py`" --list"
