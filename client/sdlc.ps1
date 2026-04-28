#Requires -Version 5.1
<#
.SYNOPSIS
    SDLC Autonomous Orchestrator — submit a goal and watch the live DAG unfold.
    Edit the CONFIGURATION section below, then copy-paste the entire script into a terminal.
#>

# ─── CONFIGURATION (edit these before running) ────────────────────────────────
$BaseUrl      = "https://my-app.centralindia.azurecontainerapps.io"          # e.g. "https://my-app.centralindia.azurecontainerapps.io"
$LlmProvider  = "ollama"   # "gemini" or "ollama"
$OllamaBaseUrl = "https://my-api.trycloudflare.com"        # Ollama endpoint — e.g. Cloudflare tunnel URL from Kaggle or local
                           # Leave blank to use the server's OLLAMA_BASE_URL env var
$OllamaModel  = "Qwen/Qwen2.5-7B-Instruct"         # e.g. "llama3", "codellama", "gemma3:4b" (only used when LlmProvider = "ollama")
$ReviewCycles = 3          # 0–5$RepoOwner    = ""         # GitHub owner or org (e.g. "my-org"). Falls back to server's REPO_OWNER env var.
$RepoName     = ""         # GitHub repo name (e.g. "my-repo"). Falls back to server's REPO_NAME env var.# ──────────────────────────────────────────────────────────────────────────────

# Env-var fallbacks (so you can also set $env:SDLC_BASE_URL etc. once in your profile)
if (-not $BaseUrl)       { $BaseUrl       = $env:SDLC_BASE_URL }
if (-not $LlmProvider)   { $LlmProvider   = if ($env:SDLC_LLM_PROVIDER)  { $env:SDLC_LLM_PROVIDER }  else { "gemini" } }
if (-not $OllamaBaseUrl) { $OllamaBaseUrl = $env:SDLC_OLLAMA_BASE_URL }
if (-not $OllamaModel)   { $OllamaModel   = $env:SDLC_OLLAMA_MODEL }
if (-not $ReviewCycles)  { $ReviewCycles  = if ($env:SDLC_REVIEW_CYCLES) { [int]$env:SDLC_REVIEW_CYCLES } else { 2 } }
if (-not $RepoOwner)     { $RepoOwner     = $env:REPO_OWNER }
if (-not $RepoName)      { $RepoName      = $env:REPO_NAME }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── Visual helpers ───────────────────────────────────────────────────────────

# Probe for a real console handle — some terminals (VS Code, ConEmu, corp proxies)
# don't expose one and [Console]::WindowWidth / [Console]::Write throw IOException.
try   { $W = [Math]::Min(72, [Console]::WindowWidth - 1); $script:hasConsole = $true }
catch { $W = 72;                                           $script:hasConsole = $false }

function Write-Rule([string]$c = "─") { Write-Host ($c * $W) -ForegroundColor DarkCyan }

function Write-Banner {
    Write-Host ""
    Write-Rule "═"
    Write-Host "   🤖  SDLC Autonomous Orchestrator" -ForegroundColor Cyan
    Write-Rule "═"
    Write-Host ""
}

function Write-Step([string]$msg) {
    Write-Host "  ▸ " -NoNewline -ForegroundColor DarkCyan
    Write-Host $msg
}

# Phase display — prints once per phase change (no animation, no horizontal scroll)
function Show-Phase([string]$msg) {
    $maxLen = $W - 6
    if ($msg.Length -gt $maxLen) { $msg = $msg.Substring(0, $maxLen - 3) + "..." }
    Write-Host ("  ⯿  {0}" -f $msg) -ForegroundColor DarkGray
}

# Render one DAG event with colour-coded type badge
function Write-DagEvent([PSCustomObject]$ev) {
    $dto = [DateTimeOffset]::FromUnixTimeMilliseconds([long]$ev.t)
    $ts  = $dto.LocalDateTime.ToString("HH:mm:ss")

    switch ($ev.type) {
        "agent_started" {
            Write-Host ("  {0}  " -f $ts) -NoNewline -ForegroundColor DarkGray
            Write-Host "◷ START   " -NoNewline -ForegroundColor DarkYellow
            Write-Host $ev.agent -ForegroundColor Cyan
        }
        "agent_done" {
            Write-Host ("  {0}  " -f $ts) -NoNewline -ForegroundColor DarkGray
            Write-Host "✓ DONE    " -NoNewline -ForegroundColor Green
            Write-Host ("{0,-28}" -f $ev.agent) -NoNewline -ForegroundColor Green
            Write-Host ("  {0}/{1} agents" -f $ev.completed, $ev.total) -ForegroundColor DarkGray
        }
        "agent_failed" {
            Write-Host ("  {0}  " -f $ts) -NoNewline -ForegroundColor DarkGray
            Write-Host "✗ FAILED  " -NoNewline -ForegroundColor Red
            Write-Host ("{0,-28}" -f $ev.agent) -NoNewline -ForegroundColor Red
            if ($ev.PSObject.Properties["error"] -and $ev.error) {
                $errTxt = "$($ev.error)"
                $maxErr = [Math]::Max(10, $W - 50)
                if ($errTxt.Length -gt $maxErr) { $errTxt = $errTxt.Substring(0, $maxErr - 3) + "..." }
                Write-Host ("  → {0}" -f $errTxt) -ForegroundColor DarkRed
            } else { Write-Host "" }
        }
        "agent_pruned" {
            Write-Host ("  {0}  " -f $ts) -NoNewline -ForegroundColor DarkGray
            Write-Host "⊘ PRUNED  " -NoNewline -ForegroundColor Yellow
            Write-Host $ev.agent -ForegroundColor Yellow
        }
        "helper_spawned" {
            Write-Host ("  {0}  " -f $ts) -NoNewline -ForegroundColor DarkGray
            Write-Host "⚡ SPAWNED " -NoNewline -ForegroundColor Magenta
            Write-Host ("{0,-28}" -f $ev.helper) -NoNewline -ForegroundColor Magenta
            Write-Host ("  unblocking: {0}" -f $ev.blocked_agent) -ForegroundColor DarkGray
        }
        default {
            Write-Host ("  {0}  · {1}" -f $ts, ($ev | ConvertTo-Json -Compress)) -ForegroundColor DarkGray
        }
    }
}

# ─── Input ────────────────────────────────────────────────────────────────────

Write-Banner

if (-not $BaseUrl) {
    Write-Host "  Tip: set " -NoNewline -ForegroundColor DarkGray
    Write-Host '$env:SDLC_BASE_URL' -NoNewline -ForegroundColor Yellow
    Write-Host " to skip this prompt next time." -ForegroundColor DarkGray
    $BaseUrl = (Read-Host "  Container App URL").Trim()
}
$BaseUrl = $BaseUrl.TrimEnd("/")

# Show active configuration
Write-Host "  ┌─ Session Config ──────────────────────────────────────────┐" -ForegroundColor DarkCyan
Write-Host "  │                                                          │" -ForegroundColor DarkCyan
Write-Host "  │  Endpoint   " -NoNewline -ForegroundColor DarkCyan
Write-Host ("{0,-44}" -f "✓ Connected") -NoNewline -ForegroundColor Green
Write-Host "│" -ForegroundColor DarkCyan
Write-Host "  │  LLM        " -NoNewline -ForegroundColor DarkCyan
$llmDisplay = $LlmProvider
if ($LlmProvider -eq "ollama" -and $OllamaModel) { $llmDisplay = "$LlmProvider ($OllamaModel)" }
Write-Host ("{0,-44}" -f $llmDisplay) -NoNewline -ForegroundColor Yellow
Write-Host "│" -ForegroundColor DarkCyan
if ($LlmProvider -eq "ollama") {
    Write-Host "  │  Endpoint   " -NoNewline -ForegroundColor DarkCyan
    $urlDisplay = if ($OllamaBaseUrl) { "✓ Custom URL set" } else { "server default" }
    Write-Host ("{0,-44}" -f $urlDisplay) -NoNewline -ForegroundColor $(if ($OllamaBaseUrl) { "Green" } else { "DarkGray" })
    Write-Host "│" -ForegroundColor DarkCyan
}
Write-Host "  │  Reviews    " -NoNewline -ForegroundColor DarkCyan
$cycleBar = ("█" * $ReviewCycles) + ("░" * (5 - $ReviewCycles))
Write-Host ("{0,-44}" -f "$cycleBar  $ReviewCycles cycles") -NoNewline -ForegroundColor Yellow
Write-Host "│" -ForegroundColor DarkCyan
Write-Host "  │                                                          │" -ForegroundColor DarkCyan
Write-Host "  └──────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan

Write-Host ""
Write-Rule
Write-Host ""
Write-Host "  📝  What would you like the AI team to build?" -ForegroundColor Cyan
Write-Host "  Type your goal below. Multiple lines OK — press " -NoNewline -ForegroundColor DarkGray
Write-Host "Enter" -NoNewline -ForegroundColor White
Write-Host " on a blank line to submit." -ForegroundColor DarkGray
Write-Host ""

$lines = [System.Collections.Generic.List[string]]::new()
while ($true) {
    $line = Read-Host "    ›"
    if ($line -eq "") { break }
    $lines.Add($line)
}
$Goal = ($lines -join " ").Trim()

if (-not $Goal) {
    Write-Host ""
    Write-Host "  No goal provided. Exiting." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Echo what we're about to do
Write-Host ""
Write-Rule
Write-Host "  Goal: " -NoNewline -ForegroundColor DarkGray
Write-Host $Goal -ForegroundColor White
Write-Rule
Write-Host ""

# ─── Dispatch ─────────────────────────────────────────────────────────────────

Write-Step "Dispatching to orchestrator..."

try {
    $body = @{ text = $Goal; llm_provider = $LlmProvider; review_cycles = $ReviewCycles }
    if ($OllamaModel)   { $body["ollama_model"]    = $OllamaModel }
    if ($OllamaBaseUrl) { $body["ollama_base_url"] = $OllamaBaseUrl }
    if ($RepoOwner)     { $body["repo_owner"]      = $RepoOwner }
    if ($RepoName)      { $body["repo_name"]       = $RepoName }
    $body = $body | ConvertTo-Json
    $resp = Invoke-RestMethod -Uri "$BaseUrl/teams-trigger" -Method Post -Body $body -ContentType "application/json"
} catch {
    Write-Host "`n  ✗ Could not reach orchestrator: $_" -ForegroundColor Red
    exit 1
}

$jobId     = $resp.job_id
$statusUrl = "$BaseUrl/status/$jobId"

Write-Host "  Job ID  " -NoNewline -ForegroundColor DarkGray ; Write-Host $jobId -ForegroundColor White
Write-Host "  Status  " -NoNewline -ForegroundColor DarkGray ; Write-Host $statusUrl -ForegroundColor DarkGray
Write-Host ""

# ─── Live event stream ────────────────────────────────────────────────────────

Write-Step "Execution graph  (live)"
Write-Host "  $(("─" * ($W - 4)))" -ForegroundColor DarkGray
Write-Host ""

$cursor     = 0   # index into job.events already printed
$lastStep   = ""
$isComplete = $false

while (-not $isComplete) {
    Start-Sleep -Milliseconds 2500

    try {
        $job = Invoke-RestMethod -Uri $statusUrl -Method Get
    } catch {
        continue
    }

    # Drain any new events since last tick
    $allEvents = @($job.events)   # force array even if single item
    if ($allEvents.Count -gt $cursor) {
        foreach ($ev in $allEvents[$cursor..($allEvents.Count - 1)]) {
            Write-DagEvent $ev
        }
        $cursor = $allEvents.Count
    }

    # Show phase change once per transition (no animation)
    if ($job.current_step -ne $lastStep) {
        $lastStep = $job.current_step
        # DAG events already show agent-level progress; only display non-running phases
        if (-not $lastStep.StartsWith("running:")) {
            Show-Phase $lastStep
        }
    }

    if ($job.status -eq "complete" -or $job.status -eq "failed") {
        $isComplete = $true
    }
}

# ─── Final result ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Rule "═"

if ($job.status -eq "complete") {
    Write-Host "  ✅  COMPLETE" -ForegroundColor Green
    Write-Host ""
    $result = "$($job.result)"
    # Highlight GitHub PR URL in a distinct colour
    if ($result -match "(https://github\.com/\S+)") {
        $pr     = $Matches[1]
        $before = $result.Substring(0, $result.IndexOf($pr))
        $after  = $result.Substring($result.IndexOf($pr) + $pr.Length)
        Write-Host "  $before" -NoNewline -ForegroundColor Green
        Write-Host $pr         -NoNewline -ForegroundColor Cyan
        Write-Host $after                 -ForegroundColor Green
    } else {
        Write-Host "  $result" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌  FAILED" -ForegroundColor Red
    Write-Host ""
    $errFull = "$($job.error)"
    $lineMax = $W - 4
    for ($i = 0; $i -lt $errFull.Length; $i += $lineMax) {
        $chunk = $errFull.Substring($i, [Math]::Min($lineMax, $errFull.Length - $i))
        Write-Host "  $chunk" -ForegroundColor Red
    }
}

Write-Rule "═"
Write-Host ""
