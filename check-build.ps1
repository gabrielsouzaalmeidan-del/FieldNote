# check-build.ps1 — Verifica o resultado do build no GitHub Actions
# Uso:
#   .\check-build.ps1           -> monitora o ultimo run
#   .\check-build.ps1 87        -> monitora o run #87
#   $env:GH_TOKEN="ghp_..."     -> com token, polling 3x mais rapido (5000 req/h vs 60/h)

param([int]$RunNumber = 0)

$repo     = "gabrielsouzaalmeidan-del/FieldNote"
$workflow = "Build APK - FieldNote"
$interval = if ($env:GH_TOKEN) { 20 } else { 90 }

$headers = @{ "Accept" = "application/vnd.github+json"; "X-GitHub-Api-Version" = "2022-11-28" }
if ($env:GH_TOKEN) { $headers["Authorization"] = "Bearer $env:GH_TOKEN" }

function gh-api($path) {
    try { Invoke-RestMethod -Uri "https://api.github.com$path" -Headers $headers -ErrorAction Stop }
    catch { $null }
}

# Encontrar run alvo
$runs = gh-api "/repos/$repo/actions/runs?per_page=10"
if (-not $runs) {
    Write-Host "API indisponivel (rate limit sem token). Acesse:" -ForegroundColor Yellow
    Write-Host "  https://github.com/$repo/actions" -ForegroundColor Cyan
    exit 1
}

$target = $runs.workflow_runs | Where-Object { $_.name -eq $workflow } |
    & { if ($RunNumber) { process { if ($_.run_number -eq $RunNumber) { $_ } } } else { Select-Object -First 1 } }

if (-not $target) { Write-Host "Run nao encontrado." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Build #$($target.run_number)" -ForegroundColor Cyan -NoNewline
Write-Host "  $($target.head_commit.message -replace '\n.*','')" -ForegroundColor White
Write-Host "  $($target.head_sha.Substring(0,7)) / $($target.head_branch)" -ForegroundColor DarkGray
Write-Host "  $($target.html_url)" -ForegroundColor DarkGray
Write-Host ""

$runId = $target.id
$t0 = Get-Date

while ($true) {
    $run = (gh-api "/repos/$repo/actions/runs?per_page=10").workflow_runs |
           Where-Object { $_.id -eq $runId }

    if (-not $run) {
        $s = [int]((Get-Date)-$t0).TotalSeconds
        Write-Host "  [${s}s] rate limit — aguardando ${interval}s..." -ForegroundColor DarkYellow
        Start-Sleep -Seconds $interval
        continue
    }

    if ($run.status -eq 'completed') { break }

    $s = [int]((Get-Date)-$t0).TotalSeconds
    Write-Host "  [${s}s] $($run.status)..." -ForegroundColor Yellow
    Start-Sleep -Seconds $interval
}

# Detalhes dos steps
$jobs = gh-api "/repos/$repo/actions/runs/$runId/jobs"
$job  = $jobs.jobs[0]

Write-Host ""
foreach ($step in $job.steps | Where-Object { $_.status -ne 'pending' -and $_.conclusion -ne 'skipped' }) {
    $cor    = switch ($step.conclusion) { 'success' { 'Green' } 'failure' { 'Red' } default { 'DarkGray' } }
    $prefix = if ($step.conclusion -eq 'failure') { 'X' } elseif ($step.conclusion -eq 'success') { 'v' } else { '-' }
    $num    = $step.number.ToString().PadLeft(2)
    Write-Host "  [$prefix] $num. $($step.name)" -ForegroundColor $cor
}

Write-Host ""
if ($run.conclusion -eq 'success') {
    Write-Host "BUILD OK — #$($run.run_number)" -ForegroundColor Green
    $rel = (gh-api "/repos/$repo/releases?per_page=1")[0]
    if ($rel -and $rel.tag_name -like "build-$($run.run_number)*") {
        Write-Host "Release : $($rel.html_url)" -ForegroundColor Green
        if ($rel.assets.Count -gt 0) {
            Write-Host "APK     : $($rel.assets[0].browser_download_url)" -ForegroundColor Green
        }
    }
} else {
    Write-Host "BUILD FALHOU — #$($run.run_number) ($($run.conclusion))" -ForegroundColor Red
    $ann = gh-api "/repos/$repo/check-runs/$($job.id)/annotations"
    ($ann | Where-Object { $_.annotation_level -eq 'failure' }) |
        ForEach-Object { Write-Host "  > $($_.message)" -ForegroundColor Red }
}
Write-Host ""
