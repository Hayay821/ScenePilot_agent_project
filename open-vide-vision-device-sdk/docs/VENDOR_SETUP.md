# Windows vendor SDK setup

Use MSVC x64. Do not use Win32 or WSL for these Windows x64 libraries.

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

At deployment time, copy the required runtime assets beside the application:

- CameraSDK: `CameraSDK.dll` and `bin/jsons`.
- MediaSDK: `MediaSDK.dll`, its dependent DLLs, `bin/models`, and required runtime assets.
- Link 2: `UVCCamera.dll` and its runtime dependencies.

The official SDK files must be obtained separately. Do not commit them unless
your Insta360 agreement explicitly permits redistribution.

## Driver modes

- X5 CameraSDK: camera USB mode must be Android; Windows uses the SDK-required USB driver.
- Link 2: remains a UVC device. Do not replace its normal UVC driver with the X5 libusbK driver.


