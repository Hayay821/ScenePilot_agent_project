$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime=Join-Path $projectRoot 'device_bridge\runtime'
$assetDir=Join-Path $projectRoot 'agents_Module_good\data\camera_captures'
New-Item -ItemType Directory -Force -Path $assetDir | Out-Null
$env:OVV_ASSET_DIR=$assetDir
$mediaBin='E:\SDK\CameraSDK_MediaSDK\Linux_CameraSDK-2.1.8_MediaSDK-3.1.6\MediaSDK-3.1.7-20260917_192552-win64_1789644678232\bin'
$linkBin='E:\SDK\Link SDK\Link SDK\UVCCamera_win\x64\bin'
$env:PATH=$linkBin+';'+$mediaBin+';'+$env:PATH
$exe=Join-Path $runtime 'ovv_x5_device_service.exe'
if(-not(Test-Path $exe)){throw '请先运行 构建X5服务.ps1。'}
try {
    $health=Invoke-RestMethod 'http://127.0.0.1:8766/api/v1/health' -TimeoutSec 2
    if($health.mode -eq 'real-device-sdk'){
        Write-Host '真实设备服务已经运行：http://127.0.0.1:8766'
        exit 0
    }
    throw '8766端口已被其他程序占用。'
} catch {
    if($_.Exception.Message -like '*其他程序*'){throw}
}
Set-Location $runtime
Write-Host '正在启动 X5 和 Link 2 真实设备服务（8766）...'
& $exe