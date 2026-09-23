$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$cameraRoot='E:\SDK\CameraSDK_MediaSDK\Linux_CameraSDK-2.1.8_MediaSDK-3.1.6\CameraSDK-2.2.0-20260918_164435-win64\CameraSDK-2.2.0-20260918_164435-win64'
$mediaRoot='E:\SDK\CameraSDK_MediaSDK\Linux_CameraSDK-2.1.8_MediaSDK-3.1.6\MediaSDK-3.1.7-20260917_192552-win64_1789644678232'
$linkRoot='E:\SDK\Link SDK\Link SDK\UVCCamera_win\x64'
$source=Join-Path $projectRoot 'open-vide-vision-device-sdk'
$buildDir=Join-Path $projectRoot 'device_bridge\build-x5'
$cmake=Get-Command cmake -ErrorAction SilentlyContinue
if(-not $cmake){$cmake=[pscustomobject]@{Source='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'}}
if(-not $cmake){throw 'CMake was not found. Install Visual Studio 2022 Build Tools with Desktop C++ and CMake.'}
& $cmake.Source -S $source -B $buildDir -A x64 -DOVV_ENABLE_X5_CAMERA=ON -DOVV_ENABLE_LINK_UVC=ON -DOVV_BUILD_TESTS=OFF -DOVV_BUILD_EXAMPLES=OFF "-DINSTA360_CAMERA_SDK_ROOT=$cameraRoot" "-DINSTA360_MEDIA_SDK_ROOT=$mediaRoot" "-DINSTA360_LINK_SDK_ROOT=$linkRoot"
& $cmake.Source --build $buildDir --config Release --target ovv_x5_device_service