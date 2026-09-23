$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$deviceUrl = 'http://127.0.0.1:8766/api/v1/health'
$appUrl = 'http://127.0.0.1:8765/app/create.html'

$deviceReady = $false
try {
    $health = Invoke-RestMethod $deviceUrl -TimeoutSec 1
    $deviceReady = $health.mode -eq 'real-device-sdk'
} catch {}
if (-not $deviceReady) {
    Start-Process powershell -ArgumentList @('-ExecutionPolicy','Bypass','-File',(Join-Path $projectRoot '启动X5真实服务.ps1')) -WorkingDirectory $projectRoot -WindowStyle Hidden
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 300
        try {
            $health = Invoke-RestMethod $deviceUrl -TimeoutSec 1
            if ($health.mode -eq 'real-device-sdk') { $deviceReady=$true; break }
        } catch {}
    }
}

$agentReady = $false
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/health' -TimeoutSec 1
    if ($health.mode -eq 'real-device-sdk') {
        throw '旧设备服务仍占用8765端口，请结束 ovv_x5_device_service.exe 后重新运行。'
    }
    $agentReady = [bool]$health.success
} catch {
    if ($_.Exception.Message -like '*旧设备服务*') { throw }
}
if (-not $agentReady) {
    $agentRoot = Join-Path $projectRoot 'agents_Module_good'
    $agentMode = if ($env:AGENT_MODE) { $env:AGENT_MODE } else { 'mock' }
    Start-Process python -ArgumentList @('fast.py','serve','--mode',$agentMode) -WorkingDirectory $agentRoot -WindowStyle Hidden
    for ($i=0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 300
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/health' -TimeoutSec 1
            if ($health.success) { $agentReady=$true; break }
        } catch {}
    }
}

Write-Host "BoldMaker 页面: $appUrl"
Write-Host $(if($deviceReady){'真实设备服务已就绪（8766）。'}else{'真实设备服务仍在启动。'})
Write-Host $(if($agentReady){'ScenePilot 服务已就绪（8765）。'}else{'ScenePilot 服务启动失败，请检查 Python 依赖。'})
Start-Process $appUrl