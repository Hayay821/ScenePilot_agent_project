# GitHub submission checklist

- [ ] Commit only this integration package and your own project code.
- [ ] Confirm `git status` contains no `.dll`, `.lib`, models, JSON capability files or SDK archives.
- [ ] Add the repository remote and push the source tree.
- [ ] Configure all three SDK roots with CMake cache variables.
- [ ] Build with MSVC x64.
- [ ] Run the Mock test before connecting hardware.
- [ ] Run X5 discovery/capture/download smoke tests.
- [ ] Run Link 2 tracking/composition/PTZ smoke tests.
- [ ] Run `.insp` and `.insv` MediaSDK smoke tests.
- [ ] Record SDK, firmware and driver versions in the release notes.
