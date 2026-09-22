# Architecture integration

```text
Director / Photographer / Editor Agents
                  |
          structured DeviceAction
                  v
            PlanValidator
                  |
        approved=true + evidence
                  v
            DeviceExecutor
           /              \
   X5CameraAdapter     Link2Adapter
           |
   downloaded .insp/.insv
           v
       IMediaProcessor
           |
 panorama / frame sequence / stitched video
```

The package belongs in the local backend control module. Cloud services and
Agents never load vendor DLLs and never directly issue camera commands.

## Responsibilities

- `PlanValidator`: validates permissions, ranges, device state and Skill policy.
- `DeviceExecutor`: enforces approval again, routes actions and emits audit records.
- `IDeviceAdapter`: isolates a specific vendor SDK and exposes capabilities.
- `IMediaProcessor`: owns asynchronous offline stitching jobs.
- Storage layer: owns input/output paths and persists audit records.

## Device mapping

| Project action | X5 CameraSDK | Link 2 UVCCamera SDK | MediaSDK |
|---|---|---|---|
| Capture/record | Yes | UVC host captures frames | No |
| Preview input | Camera live stream | Standard UVC video capture | Real-time X5 stitch |
| PTZ/tracking/composition | No | Yes | No |
| Download camera media | Yes | Not applicable | No |
| Panorama image/video | Source material | Not applicable | Yes |
| Frame extraction | Source material | Host may capture frames | Yes |

## Agent contract

Agents produce JSON matching `schemas/device_action.schema.json`. Only the
PlanValidator may set `approved` to true. Every execution records `rule_id` and
`evidence_id`, which connects a physical action to the director timeline.

