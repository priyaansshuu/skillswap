param(
    [string]$Python = "",
    [ValidateRange(1024,65535)][int]$Port = 8000
)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendRoot = Join-Path (Split-Path -Parent $projectRoot) "frontend"
if (-not $Python) {
    $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) { $Python = $venvPython }
    else { $Python = (Get-Command python -ErrorAction Stop).Source }
}
$Python = (Resolve-Path -LiteralPath $Python).Path
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ".env"))) {
    throw "Create a local .env using .env.example and configure PostgreSQL first. See docs/FRONTEND_DEMO.md."
}
$demoUrl = "http://127.0.0.1:$Port"
try {
    $ready = Invoke-RestMethod "$demoUrl/health/ready" -TimeoutSec 2
    $demoHomeResponse = Invoke-WebRequest "$demoUrl/" -TimeoutSec 2 -UseBasicParsing
    if ($ready.status -eq "ready" -and $demoHomeResponse.Content -match "SkillSwap") {
        Write-Output "SkillSwap is already running at $demoUrl"
        return
    }
} catch { }
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is occupied by another service. Choose a different -Port or stop that service first."
}
$runtimeDir = Join-Path $projectRoot "runtime"
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
Push-Location $projectRoot
try {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Check your local PostgreSQL service and .env." }
    $frontendIndex = Join-Path $frontendRoot "dist\index.html"
    if (-not (Test-Path -LiteralPath $frontendIndex)) {
        Push-Location $frontendRoot
        try {
            & npm.cmd ci --no-audit --no-fund
            if ($LASTEXITCODE -ne 0) { throw "Frontend dependencies could not be installed." }
            & npm.cmd run build
            if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
        } finally { Pop-Location }
    }
    $process = Start-Process -FilePath $Python -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port",$Port) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir "api.stdout.log") -RedirectStandardError (Join-Path $runtimeDir "api.stderr.log")
    $process.Refresh()
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        $process.Refresh()
        if ($process.HasExited) { throw "The API stopped. Check runtime/api.stderr.log; the port may already be occupied." }
        try {
            $ready = Invoke-RestMethod "$demoUrl/health/ready" -TimeoutSec 1
            if ($ready.status -eq "ready") {
                $managedChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($process.Id)" | ForEach-Object {
                    $childProcess = Get-Process -Id $_.ProcessId -ErrorAction Stop
                    @{ pid=$childProcess.Id; path=$childProcess.Path; started=$childProcess.StartTime.ToUniversalTime().ToString("o") }
                })
                @{ pid=$process.Id; path=$process.Path; started=$process.StartTime.ToUniversalTime().ToString("o"); children=$managedChildren; url=$demoUrl } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runtimeDir "demo-process.json")
                Write-Output "SkillSwap is ready at $demoUrl"
                Write-Output "Use two separate browser sessions for the teaching and learning demo."
                return
            }
        } catch { }
        Start-Sleep -Milliseconds 250
    }
    throw "Startup timed out. Check runtime/api.stderr.log."
} finally { Pop-Location }
