# Windows 官方 SDK 配置

必须使用 MSVC x64 工具链。Windows x64 SDK 不能使用 Win32、MinGW或WSL工具链链接。

## 配置与构建

```powershell
cmake -S . -B build -A x64 `
  -DOVV_ENABLE_X5_CAMERA=ON `
  -DINSTA360_CAMERA_SDK_ROOT="D:/SDK/CameraSDK-2.2.0" `
  -DOVV_ENABLE_LINK_UVC=ON `
  -DINSTA360_LINK_SDK_ROOT="D:/SDK/UVCCamera_win/x64" `
  -DOVV_ENABLE_MEDIA_SDK=ON `
  -DINSTA360_MEDIA_SDK_ROOT="D:/SDK/MediaSDK-3.1.7"

cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

三个路径分别指向解压后的 CameraSDK、MediaSDK 和 Link 2 `x64` 目录。

## 运行时资源

应用部署时，需要将以下官方资源复制到可执行程序旁边：

- CameraSDK：`CameraSDK.dll` 和 `bin/jsons`。
- MediaSDK：`MediaSDK.dll`、它依赖的DLL、`bin/models` 和其他必要运行库。
- Link 2：`UVCCamera.dll` 及其依赖项。

官方SDK文件必须由开发者单独取得。只有在影石协议明确允许再分发时，才能把这些文件提交到仓库或发布包。

## 驱动模式

- X5 CameraSDK：相机USB模式应选择Android，并安装CameraSDK要求的Windows USB驱动。
- Link 2：保持标准UVC设备驱动。不要用X5所需的libusbK驱动替换Link 2的UVC驱动。

## CLion设置

1. 在CLion中打开本目录。
2. 进入“设置 → 构建、执行、部署 → 工具链”。
3. 选择Visual Studio/MSVC x64工具链。
4. 在CMake选项中填写三个SDK根目录和启用开关。
5. 重新加载CMake工程。
