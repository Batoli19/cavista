
$apps = Get-StartApps
$apps | Select-Object Name, AppID | ConvertTo-Json > apps.json
