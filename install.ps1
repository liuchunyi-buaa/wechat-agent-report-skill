$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDest = Join-Path $env:USERPROFILE ".claude\skills\wechat-agent-report"
$ConfigDir = Join-Path $env:USERPROFILE ".claude\wechat-agent-report"

New-Item -ItemType Directory -Force -Path (Join-Path $SkillDest "scripts"), (Join-Path $ConfigDir "references") | Out-Null
Copy-Item (Join-Path $Src "SKILL.md") (Join-Path $SkillDest "SKILL.md") -Force
Copy-Item (Join-Path $Src "scripts\send_report.py") (Join-Path $SkillDest "scripts\send_report.py") -Force
Copy-Item (Join-Path $Src "scripts\send_ui_macos.sh") (Join-Path $SkillDest "scripts\send_ui_macos.sh") -Force
Copy-Item (Join-Path $Src "references\*") (Join-Path $ConfigDir "references") -Force

$Config = Join-Path $ConfigDir "config.json"
if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $Src "config.example.json") $Config -Force
    Write-Host "已创建配置：$Config"
} else {
    Write-Host "配置已存在，未覆盖：$Config"
}

Write-Host "安装完成。"
Write-Host "1. 若未安装 OCR 依赖，请运行：python -m pip install winsdk pillow"
Write-Host "2. 编辑 $Config，填写 wechat_name（微信里显示的对话名）"
Write-Host "3. 运行：python `"$SkillDest\scripts\send_report.py`" --list"
Write-Host "4. 预检：python `"$SkillDest\scripts\send_report.py`" --agent daily-summary --project `"项目名`" --title `"标题`" --background `"项目背景`" --summary `"完成内容`" --check"
Write-Host "5. 发送：去掉 --check 再执行一次；--dry-run 会定位对话并填入消息但不发送"
