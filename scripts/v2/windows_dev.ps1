#Requires -Version 7.0
[CmdletBinding()]
param([ValidateSet('start', 'stop', 'status')][string]$Action = 'status')

$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$runtime = Join-Path $root 'var'
$stateFile = Join-Path $runtime 'windows-dev.json'
$data = Join-Path $runtime 'pgdata'
$pgCtl = Join-Path $runtime 'pgsql\Library\bin\pg_ctl.exe'
$executables = @{
    api = Join-Path $root '.venv\Scripts\python.exe'
    worker = Join-Path $root '.venv\Scripts\python.exe'
    web = 'C:\Program Files\nodejs\node.exe'
    db = Join-Path $runtime 'pgsql\Library\bin\postgres.exe'
}
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
# A second launcher must not race the PID record or create duplicate workers.
$lock = [IO.File]::Open((Join-Path $runtime 'windows-dev.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
try {
    $state = if (Test-Path -LiteralPath $stateFile) {
        Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json -AsHashtable
    } else { @{} }

    function Save-State {
        $temporary = "$stateFile.tmp"
        [IO.File]::WriteAllText($temporary, ($state | ConvertTo-Json -Depth 4))
        Move-Item -LiteralPath $temporary -Destination $stateFile -Force
    }

    function Get-OwnedProcess([string]$Name) {
        if (-not $state.ContainsKey($Name)) { return $null }
        $entry = $state[$Name]
        $process = Get-Process -Id $entry.pid -ErrorAction SilentlyContinue
        if ($null -eq $process) { return $null }
        try {
            if ($process.Path -eq $executables[$Name] -and
                $process.StartTime.ToUniversalTime() -eq ([datetime]$entry.startedAt).ToUniversalTime()) {
                return $process
            }
        } catch { }
        return $null
    }

    function Save-Process([string]$Name, [Diagnostics.Process]$Process) {
        $state[$Name] = @{
            pid = $Process.Id
            startedAt = $Process.StartTime.ToUniversalTime().ToString('o')
        }
        Save-State
        if ($null -eq (Get-OwnedProcess $Name)) {
            throw "$Name 프로세스의 실행파일과 생성시각을 확인하지 못했습니다. 로그를 확인하세요."
        }
    }

    function Get-DatabaseProcess {
        $pidFile = Join-Path $data 'postmaster.pid'
        if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
        $databasePid = Get-Content -LiteralPath $pidFile -TotalCount 1
        if ($databasePid -notmatch '^\d+$') { throw 'postmaster.pid가 올바르지 않습니다.' }
        $process = Get-Process -Id ([int]$databasePid) -ErrorAction SilentlyContinue
        if ($null -ne $process -and $process.Path -eq $executables.db) { return $process }
        return $null
    }

    function Assert-FreePort([int]$Port) {
        if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
            throw "$Port 포트를 다른 프로세스가 사용합니다. 기존 서비스를 종료하지 않았습니다."
        }
    }

    function Start-ServiceProcess([string]$Name, [string[]]$Arguments, [string]$Directory) {
        if ($null -ne (Get-OwnedProcess $Name)) {
            Write-Host "$Name 이미 실행 중입니다."
            return
        }
        if ($Name -eq 'api') { Assert-FreePort 8001 }
        if ($Name -eq 'web') { Assert-FreePort 5173 }
        $process = Start-Process -FilePath $executables[$Name] -ArgumentList $Arguments `
            -WorkingDirectory $Directory -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $runtime "$Name.stdout.log") `
            -RedirectStandardError (Join-Path $runtime "$Name.stderr.log")
        Save-Process $Name $process
        Write-Host "$Name 시작했습니다. PID=$($process.Id)"
    }

    function Test-Endpoint([string]$Url) {
        try {
            return (Invoke-WebRequest -Uri $Url -TimeoutSec 2 -NoProxy).StatusCode -eq 200
        } catch { return $false }
    }

    function Show-Status {
        $database = Get-DatabaseProcess
        if ($null -eq $database) { Write-Host 'db 중지됨 (127.0.0.1:55432)' }
        elseif ($null -ne (Get-OwnedProcess 'db')) { Write-Host "db 실행 중 (관리 대상, PID=$($database.Id), 127.0.0.1:55432)" }
        else { Write-Host "db 실행 중 (외부 시작 DB 재사용, stop 대상 아님, PID=$($database.Id))" }
        foreach ($name in @('api', 'worker', 'web')) {
            $process = Get-OwnedProcess $name
            if ($null -eq $process) { Write-Host "$name 관리 대상 프로세스 없음" }
            else { Write-Host "$name 실행 중 (PID=$($process.Id))" }
        }
        Write-Host "API HTTP 정상: $(Test-Endpoint 'http://127.0.0.1:8001/api/v1/health')"
        Write-Host "웹 HTTP 정상: $(Test-Endpoint 'http://127.0.0.1:5173/')"
    }

    if ($Action -eq 'start') {
        foreach ($path in @($pgCtl, $executables.api, $executables.web,
            (Join-Path $data 'PG_VERSION'), (Join-Path $root 'frontend\node_modules\vite\bin\vite.js'))) {
            if (-not (Test-Path -LiteralPath $path)) { throw "필수 파일이 없습니다: $path" }
        }
        if ($null -eq (Get-DatabaseProcess)) {
            Assert-FreePort 55432
            $databaseStart = Start-Process -FilePath $pgCtl -ArgumentList @(
                '-D', "`"$data`"", '-l', "`"$(Join-Path $runtime 'postgres.log')`"",
                '-o', '"-h 127.0.0.1 -p 55432"', '-w', '-t', '30', 'start'
            ) -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput (Join-Path $runtime 'db-start.stdout.log') `
                -RedirectStandardError (Join-Path $runtime 'db-start.stderr.log')
            # Start-Process -Wait also waits for the long-lived PostgreSQL child.
            if (-not $databaseStart.WaitForExit(35000)) { throw 'DB 시작 명령이 35초 안에 끝나지 않았습니다. 로그를 확인하세요.' }
            if ($databaseStart.ExitCode -ne 0) { throw 'DB 시작 실패: var/db-start.stderr.log와 var/postgres.log를 확인하세요.' }
            $database = Get-DatabaseProcess
            if ($null -eq $database) { throw '시작한 DB 프로세스를 확인하지 못했습니다.' }
            Save-Process 'db' $database
        } elseif ($null -eq (Get-OwnedProcess 'db')) {
            Write-Host '외부에서 시작한 var/pgdata DB를 재사용합니다. 이 helper의 stop은 이 DB를 종료하지 않습니다.'
        }
        $previousEncoding = $env:PYTHONIOENCODING
        $previousProxy = $env:OW_API_PROXY_TARGET
        try {
            $env:PYTHONIOENCODING = 'utf-8'
            Start-ServiceProcess 'api' @('scripts\v2\dev.py', 'serve', '--port', '8001') $root
            Start-ServiceProcess 'worker' @('scripts\v2\dev.py', 'worker') $root
            $env:OW_API_PROXY_TARGET = 'http://127.0.0.1:8001'
            Start-ServiceProcess 'web' @('node_modules\vite\bin\vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort') (Join-Path $root 'frontend')
        } finally {
            $env:PYTHONIOENCODING = $previousEncoding
            $env:OW_API_PROXY_TARGET = $previousProxy
        }
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        do {
            if ((Test-Endpoint 'http://127.0.0.1:8001/api/v1/health') -and
                (Test-Endpoint 'http://127.0.0.1:5173/')) { break }
            Start-Sleep -Milliseconds 500
        } while ([DateTime]::UtcNow -lt $deadline)
        Show-Status
        foreach ($name in @('api', 'worker', 'web')) {
            if ($null -eq (Get-OwnedProcess $name)) { throw "$name 프로세스가 종료되었습니다. var/$name.stderr.log를 확인하세요." }
        }
        if (-not (Test-Endpoint 'http://127.0.0.1:8001/api/v1/health') -or
            -not (Test-Endpoint 'http://127.0.0.1:5173/')) {
            throw '30초 안에 HTTP 준비를 확인하지 못했습니다. 시작된 프로세스는 유지됩니다. status와 로그를 확인하세요.'
        }
    } elseif ($Action -eq 'stop') {
        foreach ($name in @('web', 'api', 'worker')) {
            $process = Get-OwnedProcess $name
            if ($null -ne $process) {
                & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F | Out-Null
                if ($LASTEXITCODE -ne 0 -and $null -ne (Get-OwnedProcess $name)) { throw "$name 종료에 실패했습니다." }
                Write-Host "$name 프로세스 트리를 종료했습니다."
            } elseif ($state.ContainsKey($name)) {
                Write-Host "$name PID 기록이 만료되었습니다. 해당 PID를 종료하지 않았습니다."
            }
            $state.Remove($name)
            Save-State
        }
        $database = Get-OwnedProcess 'db'
        if ($null -ne $database) {
            $cluster = Get-DatabaseProcess
            if ($null -eq $cluster -or $cluster.Id -ne $database.Id) { throw 'DB 클러스터의 PID와 관리 기록이 달라 DB를 종료하지 않았습니다.' }
            $databaseStop = Start-Process -FilePath $pgCtl -ArgumentList @('-D', "`"$data`"", '-m', 'fast', '-w', '-t', '30', 'stop') `
                -WindowStyle Hidden -Wait -PassThru `
                -RedirectStandardOutput (Join-Path $runtime 'db-stop.stdout.log') `
                -RedirectStandardError (Join-Path $runtime 'db-stop.stderr.log')
            if ($databaseStop.ExitCode -ne 0) { throw 'DB 정상 종료 실패: var/db-stop.stderr.log를 확인하세요. 데이터 파일은 삭제하지 않았습니다.' }
            Write-Host 'DB를 정상 종료했습니다. 데이터는 보존됩니다.'
        } elseif ($null -ne (Get-DatabaseProcess)) {
            Write-Host '외부 시작 DB는 유지합니다. 이 helper의 종료 대상이 아닙니다.'
        }
        $state.Remove('db')
        Save-State
        Show-Status
    } else { Show-Status }
} catch {
    Write-Error "로컬 실행 $Action 실패: $($_.Exception.Message)" -ErrorAction Continue
    exit 1
} finally { $lock.Dispose() }
