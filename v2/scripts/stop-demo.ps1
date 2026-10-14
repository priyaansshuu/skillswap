$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$recordPath = Join-Path $projectRoot "runtime\demo-process.json"
if (-not (Test-Path -LiteralPath $recordPath)) { Write-Output "No managed SkillSwap process was recorded."; return }
$record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$process = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($process) {
    $recordedStart = [datetime]::Parse($record.started).ToUniversalTime()
    if ($process.Path -ne $record.path -or $process.StartTime.ToUniversalTime() -ne $recordedStart) {
        throw "The recorded process identity no longer matches. No process was stopped."
    }
    $childrenToStop = @()
    foreach ($childRecord in $record.children) {
        $childProcess = Get-Process -Id $childRecord.pid -ErrorAction SilentlyContinue
        if ($childProcess) {
            $childInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($childProcess.Id)"
            $childStart = [datetime]::Parse($childRecord.started).ToUniversalTime()
            if ($childInfo.ParentProcessId -ne $process.Id -or $childProcess.Path -ne $childRecord.path -or $childProcess.StartTime.ToUniversalTime() -ne $childStart) {
                throw "A recorded child process identity no longer matches. No process was stopped."
            }
            $childrenToStop += $childProcess
        }
    }
    foreach ($childProcess in $childrenToStop) { Stop-Process -Id $childProcess.Id -ErrorAction Stop }
    $process.Refresh()
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -ErrorAction Stop
    }
}
Remove-Item -LiteralPath $recordPath
Write-Output "The managed SkillSwap demo is stopped. PostgreSQL data is preserved."
