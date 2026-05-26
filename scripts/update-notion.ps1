# FieldNote -> Notion Reporter
# Dispara automaticamente ao fim de cada sessao Claude Code
#
# Configuracao: defina as variaveis de ambiente abaixo ou crie um arquivo
# scripts\.env.local com o conteudo:
#   NOTION_TOKEN=seu_token_aqui
#   NOTION_PARENT_PAGE_ID=id_da_pagina_fieldnote_updates

$PROJECT_PATH   = "C:\Users\gabriel.montenegro\Documents\fauna-campo-main"
$NOTION_VERSION = "2022-06-28"

$env:PATH = "C:\Program Files\nodejs\;C:\Users\gabriel.montenegro\AppData\Roaming\npm;" + $env:PATH

# ── Carrega .env.local se existir ─────────────────────────────────────────────
$envFile = Join-Path $PROJECT_PATH "scripts\.env.local"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$NOTION_TOKEN   = $env:NOTION_TOKEN
$PARENT_PAGE_ID = $env:NOTION_PARENT_PAGE_ID

if (-not $NOTION_TOKEN -or -not $PARENT_PAGE_ID) {
    Write-Host "ERRO: Variaveis NOTION_TOKEN e NOTION_PARENT_PAGE_ID nao definidas."
    Write-Host "Crie o arquivo scripts\.env.local com as variaveis. Veja scripts\.env.example."
    exit 1
}

$headers = @{
    "Authorization"  = "Bearer $NOTION_TOKEN"
    "Notion-Version" = $NOTION_VERSION
    "Content-Type"   = "application/json"
}

# ── Git info ──────────────────────────────────────────────────────────────────
Push-Location $PROJECT_PATH
$recentLog    = git log -5 --pretty=format:"- %s" 2>$null
$changedFiles = git diff --name-only HEAD~1 HEAD 2>$null
$stats        = (git diff --stat HEAD~1 HEAD 2>$null | Select-Object -Last 1)
Pop-Location

$logText   = if ($recentLog)    { ($recentLog    -join " | ") } else { "Sem commits recentes." }
$filesText = if ($changedFiles) { ($changedFiles -join ", ") }  else { "Nenhum arquivo alterado." }
$statsText = if ($stats)        { $stats.Trim() }               else { "Sem estatisticas." }

$now       = Get-Date -Format "yyyy-MM-dd HH:mm"
$pageTitle = "FieldNote Update - $now"

# ── Monta blocos ──────────────────────────────────────────────────────────────
function blk($type, $text) {
    return @{
        object = "block"
        type   = $type
        $type  = @{ rich_text = @(@{ type = "text"; text = @{ content = $text } }) }
    }
}

$blocks = @(
    (blk "heading_2"  "Resumo da Sessao"),
    (blk "paragraph"  "Data/hora : $now"),
    (blk "paragraph"  "Projeto   : FieldNote"),
    (blk "heading_2"  "Commits Recentes"),
    (blk "paragraph"  $logText),
    (blk "heading_2"  "Arquivos Modificados"),
    (blk "paragraph"  $filesText),
    (blk "heading_2"  "Estatisticas"),
    (blk "paragraph"  $statsText),
    (blk "paragraph"  "--- Gerado automaticamente pelo Claude Code ---")
)

# ── Cria pagina no Notion ─────────────────────────────────────────────────────
$body = @{
    parent     = @{ page_id = $PARENT_PAGE_ID }
    properties = @{
        title = @{ title = @(@{ type = "text"; text = @{ content = $pageTitle } }) }
    }
    children   = $blocks
} | ConvertTo-Json -Depth 20

Write-Host "[FieldNote] Enviando relatorio para o Notion..."

try {
    $r = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" `
        -Method POST -Headers $headers -Body $body -ErrorAction Stop
    Write-Host "OK! Relatorio criado: $($r.url)"
} catch {
    $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    Write-Host "ERRO: $($err.message)"
    exit 1
}
