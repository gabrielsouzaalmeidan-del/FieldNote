$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $dir
$watcher.Filter = "index.html"
$watcher.NotifyFilter = [System.IO.NotifyFilters]"LastWrite"
$watcher.EnableRaisingEvents = $true

$lastPush = [DateTime]::MinValue
$debounce = 3  # segundos entre pushes

$action = {
    $now = Get-Date
    if (($now - $script:lastPush).TotalSeconds -lt $script:debounce) { return }
    $script:lastPush = $now

    $ts = $now.ToString("yyyy-MM-dd HH:mm:ss")
    Set-Location $script:dir
    git add index.html
    $result = git commit -m "Auto: index.html $ts" 2>&1
    if ($LASTEXITCODE -eq 0) {
        git push 2>&1 | Out-Null
        Write-Host "[$ts] Push realizado!" -ForegroundColor Green
    } else {
        Write-Host "[$ts] Sem alteracoes para commitar." -ForegroundColor Yellow
    }
}

Register-ObjectEvent $watcher "Changed" -Action $action -SourceIdentifier "FieldNoteWatcher" | Out-Null
Write-Host "Monitorando index.html em: $dir" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar." -ForegroundColor Cyan

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Unregister-Event -SourceIdentifier "FieldNoteWatcher" -ErrorAction SilentlyContinue
    $watcher.Dispose()
    Write-Host "Watcher encerrado." -ForegroundColor Gray
}
