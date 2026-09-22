# Open Vide Vision Device SDK

A GitHub-ready C++17 integration layer connecting the Open Vide Vision Agent
architecture to Insta360 X5 and Link 2 devices on Windows.

## What this repository contains

- A vendor-neutral `IDeviceAdapter` interface.
- A policy boundary in `DeviceExecutor`.
- An asynchronous-job-shaped `IMediaProcessor` interface.
- A JSON Schema for validated Agent device actions.
- Mock implementations that compile and run without proprietary SDK files.
- Optional build hooks for CameraSDK 2.2.0 and Link 2 UVCCamera SDK.
- Vendor setup and architecture documentation.

Official SDK binaries, headers, models and archives are intentionally excluded.

## Build the portable Mock version

```powershell
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Run:

```powershell
.\build\Debug\ovv_device_demo.exe
```

## Integration rule

```text
Agent -> structured plan -> PlanValidator -> DeviceExecutor -> adapter -> device
```

Agents cannot call CameraSDK, MediaSDK or UVCCamera directly. This preserves
permissions, capability checks, range validation and an auditable mapping from
Skill rule and event evidence to every physical device action.

See `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/VENDOR_SETUP.md` and `docs/GITHUB_CHECKLIST.md`.


