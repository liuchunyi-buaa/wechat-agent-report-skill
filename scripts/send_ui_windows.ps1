$ErrorActionPreference = "Stop"

$NameFile = $env:WECHAT_AGENT_NAME_FILE
$MessageFile = $env:WECHAT_AGENT_MESSAGE_FILE
if (-not $NameFile -or -not $MessageFile) {
    throw "缺少 WECHAT_AGENT_NAME_FILE 或 WECHAT_AGENT_MESSAGE_FILE"
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic

[Microsoft.VisualBasic.Interaction]::AppActivate("微信")
Start-Sleep -Milliseconds 900

$OldClip = Get-Clipboard -Raw
try {
    $Name = Get-Content -Raw -Encoding UTF8 $NameFile
    Set-Clipboard -Value $Name.Trim()

    [System.Windows.Forms.SendKeys]::SendWait("^f")
    Start-Sleep -Milliseconds 700
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 1200

    [System.Windows.Forms.SendKeys]::SendWait("{DOWN}")
    Start-Sleep -Milliseconds 400
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds 1200

    $Message = Get-Content -Raw -Encoding UTF8 $MessageFile
    Set-Clipboard -Value $Message.TrimEnd()
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 600
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds 800
}
finally {
    Set-Clipboard -Value $OldClip
}
