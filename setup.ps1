# setup.ps1 — FieldNote / Claude Code environment setup
# Run once on any machine after git clone to activate project hooks.
#
# Usage: .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$claudeHome  = "$env:USERPROFILE\.claude"
$claudeProj  = "$projectRoot\.claude"

Write-Host ""
Write-Host "FieldNote — Claude Code Setup" -ForegroundColor Cyan
Write-Host "Project : $projectRoot"
Write-Host ""

# ── 0. Git remote ─────────────────────────────────────────────────────────────
Write-Host "[1/3] Configurando git remote ..." -ForegroundColor Yellow
$correctRemote = "https://github.com/gabrielsouzaalmeidan-del/FieldNote.git"
$currentRemote = git -C $projectRoot remote get-url origin 2>$null
if ($currentRemote -ne $correctRemote) {
    git -C $projectRoot remote set-url origin $correctRemote
    Write-Host "    Remote atualizado." -ForegroundColor Green
} else {
    Write-Host "    Remote ja correto." -ForegroundColor Green
}

# ── 1. settings.json global — merge enabledPlugins ────────────────────────────
Write-Host "[2/3] Sincronizando plugins em ~/.claude/settings.json ..." -ForegroundColor Yellow
$srcSettings = Get-Content "$claudeProj\settings.json" | ConvertFrom-Json
$globalSettingsPath = "$claudeHome\settings.json"

if (Test-Path $globalSettingsPath) {
    $globalSettings = Get-Content $globalSettingsPath | ConvertFrom-Json
} else {
    $globalSettings = [PSCustomObject]@{}
}

if (-not ($globalSettings.PSObject.Properties.Name -contains "enabledPlugins")) {
    $globalSettings | Add-Member -MemberType NoteProperty -Name "enabledPlugins" -Value ([PSCustomObject]@{})
}

foreach ($prop in $srcSettings.enabledPlugins.PSObject.Properties) {
    if (-not ($globalSettings.enabledPlugins.PSObject.Properties.Name -contains $prop.Name)) {
        $globalSettings.enabledPlugins | Add-Member -MemberType NoteProperty -Name $prop.Name -Value $prop.Value
    }
}

if (-not ($globalSettings.PSObject.Properties.Name -contains "theme")) {
    $globalSettings | Add-Member -MemberType NoteProperty -Name "theme" -Value "dark"
}

$globalSettings | ConvertTo-Json -Depth 10 | Set-Content $globalSettingsPath -Encoding UTF8
Write-Host "    Plugins habilitados." -ForegroundColor Green

# ── 2. settings.local.json — hook de auto-push do index.html ─────────────────
Write-Host "[3/3] Criando .claude/settings.local.json para esta maquina ..." -ForegroundColor Yellow
$localPath = "$claudeProj\settings.local.json"

$msg     = 'Auto: index.html $ts'
$hookCmd = '$j = [Console]::In.ReadToEnd() | ConvertFrom-Json; ' +
           '$fp = $j.tool_input.file_path; ' +
           "if (`$fp -like '*index.html') { " +
           "Set-Location '$projectRoot'; " +
           '$ts = Get-Date -Format ''yyyy-MM-dd HH:mm:ss''; ' +
           'git add index.html; ' +
           "git commit -m '$msg'; " +
           'git push } 2>$null'

$localConfig = [ordered]@{
    permissions = [ordered]@{
        allow = @(
            "Bash(git init *)",
            "Bash(git add *)",
            "Bash(git commit -m ' *)",
            "Bash(git push *)",
            "Skill(update-config)",
            "PowerShell(jq *)"
        )
    }
    hooks = [ordered]@{
        PostToolUse = @(
            [ordered]@{
                matcher = "Write|Edit"
                hooks   = @(
                    [ordered]@{
                        type          = "command"
                        command       = $hookCmd
                        shell         = "powershell"
                        timeout       = 30
                        statusMessage = "Fazendo push do index.html..."
                    }
                )
            }
        )
    }
}

$localConfig | ConvertTo-Json -Depth 10 | Set-Content $localPath -Encoding UTF8
Write-Host "    settings.local.json criado: $projectRoot" -ForegroundColor Green

Write-Host ""
Write-Host "Setup concluido!" -ForegroundColor Cyan
Write-Host "  Plugins habilitados em ~/.claude/settings.json"
Write-Host "  Hook de auto-push configurado para index.html"
Write-Host ""