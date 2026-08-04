$scriptPath = 'd:\bot_telegram\bot.ps1'
$source = [System.IO.File]::ReadAllText($scriptPath)
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors) | Out-Null
if ($errors) {
    $errors | ForEach-Object { $_.Message }
    exit 1
}
Write-Host 'PARSE_OK'
