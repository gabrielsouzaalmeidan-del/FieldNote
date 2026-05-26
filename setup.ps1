# setup.ps1 — FieldNote / Claude Code environment setup
# Run once on any machine after git clone/pull to activate all skills,
# commands, plugins, and project hooks automatically.
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
Write-Host "Claude  : $claudeHome"
Write-Host ""

# ── 1. Skills (global) ────────────────────────────────────────────────────────
Write-Host "[1/4] Copiando skills para ~/.claude/skills/ ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force "$claudeHome\skills" | Out-Null
Get-ChildItem "$claudeProj\skills" -Directory | ForEach-Object {
    $dest = "$claudeHome\skills\$($_.Name)"
    Copy-Item $_.FullName $dest -Recurse -Force
}
$count = (Get-ChildItem "$claudeProj\skills" -Directory).Count
Write-Host "    $count skills copiadas." -ForegroundColor Green

# ── 2. Commands (global) ──────────────────────────────────────────────────────
Write-Host "[2/4] Copiando commands para ~/.claude/commands/ ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force "$claudeHome\commands" | Out-Null
Copy-Item "$claudeProj\commands\*" "$claudeHome\commands\" -Recurse -Force
$count = (Get-ChildItem "$claudeProj\commands" -Recurse -File).Count
Write-Host "    $count arquivos de commands copiados." -ForegroundColor Green

# ── 3. settings.json global — merge enabledPlugins ────────────────────────────
Write-Host "[3/4] Sincronizando plugins em ~/.claude/settings.json ..." -ForegroundColor Yellow
$srcSettings = Get-Content "$claudeProj\settings.json" | ConvertFrom-Json
$globalSettingsPath = "$claudeHome\settings.json"

if (Test-Path $globalSettingsPath) {
    $globalSettings = Get-Content $globalSettingsPath | ConvertFrom-Json
} else {
    $globalSettings = [PSCustomObject]@{}
}

# Garante que enabledPlugins existe no global
if (-not ($globalSettings.PSObject.Properties.Name -contains "enabledPlugins")) {
    $globalSettings | Add-Member -MemberType NoteProperty -Name "enabledPlugins" -Value ([PSCustomObject]@{})
}

# Merge: adiciona cada plugin do projeto no global (não sobrescreve outros)
foreach ($prop in $srcSettings.enabledPlugins.PSObject.Properties) {
    if (-not ($globalSettings.enabledPlugins.PSObject.Properties.Name -contains $prop.Name)) {
        $globalSettings.enabledPlugins | Add-Member -MemberType NoteProperty -Name $prop.Name -Value $prop.Value
    }
}

# Preserva tema se já definido, senão aplica dark
if (-not ($globalSettings.PSObject.Properties.Name -contains "theme")) {
    $globalSettings | Add-Member -MemberType NoteProperty -Name "theme" -Value "dark"
}

$globalSettings | ConvertTo-Json -Depth 10 | Set-Content $globalSettingsPath -Encoding UTF8
Write-Host "    Plugins habilitados." -ForegroundColor Green

# ── 4. settings.local.json — hook de auto-push do index.html ─────────────────
Write-Host "[4/4] Criando .claude/settings.local.json para esta máquina ..." -ForegroundColor Yellow
$localPath = "$claudeProj\settings.local.json"

# Monta o hook com o caminho real desta máquina
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
Write-Host "    settings.local.json criado com caminho: $projectRoot" -ForegroundColor Green

# ── Resumo ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Setup concluido!" -ForegroundColor Cyan
Write-Host ""
Write-Host "O que foi configurado:" -ForegroundColor White
Write-Host "  ✓ Skills disponíveis globalmente (~/.claude/skills/)"
Write-Host "  ✓ Commands disponíveis globalmente (~/.claude/commands/)"
Write-Host "  ✓ Plugins habilitados (~/.claude/settings.json)"
Write-Host "  ✓ Hook de auto-push do index.html (.claude/settings.local.json)"
Write-Host ""
Write-Host "As skills e commands tambem carregam automaticamente ao abrir"
Write-Host "Claude Code dentro deste diretório (sem precisar rodar setup)."
Write-Host ""
