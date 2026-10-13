# Treehouse capture synchronization research

**Implemented and replayed:** the task-owned core now applies the scheduling
changes below and disables frame skipping. Two fresh entry runs match on all
3,040 video callbacks, 3,040 synchronized PIT samples, and recorded audio. See
[the first-stage report](treehouse_first_stage.md) for final hashes and limits.
The investigation and proposed verification below record how that result was
reached; wider keyboard/reset/activity coverage remains future work.

Date: 2026-09-25. Read-only review of `D:/Work/math-rescue/testing/output/dosbox-audio-trace/dosbox_pure_libretro.cpp`, SHA-256 `240594089f609a066f42b6461fd870449691673dd3b0b10e831603ea302197df`. No files in that project were changed. The findings describe this exact local primary source; they are not a claim about every DOSBox Pure version.

The parent investigation reports identical1800-callback idle runs, but196 differing pixel-frame hashes across3040 callbacks in two input replays while PCM hashes match. These observations establish that idle repeatability is insufficient; they do not by themselves prove the precise race. Source inspection exposes two concrete scheduling windows consistent with the discrepancy.

## Two windows in the existing frontend contract

In `retro_run`, `input_poll_cb` is invoked at line3427, mouse events are queued at lines3432–3453, and button mappings are updated shortly afterward. The previous emulation frame is only finished/paused at line3569. The worker can therefore consume a new input event during whichever point it has reached in its current frame.

At line3613, `TCM_NEXT_FRAME` releases the worker before audio and video callbacks. The normal software video callback is at line3683. Triple buffering can protect a completed pixel buffer, but guest RAM/PIT reads performed in or after that callback may already describe a later emulation instant. A matching screenshot and sampled game tick can therefore belong to different boundaries.

Keyboard callbacks have another entry path: lines2876–2892 directly modify key-state fields and call `DBP_QueueEvent`. The source itself notes that the callback can arrive on another thread without a mutex. Moving mouse polling alone does not synchronize externally delivered keys.

## Thread-control semantics

`DBP_ThreadControl` is at lines526–624:

- `TCM_FINISH_FRAME`: if no frame is pending, return without waking the worker. If a frame is paused midway, resume it, then wait for its completion semaphore. Clear `dbp_frame_pending`. Repeating this call after a completed frame is safe and does not advance another frame.
- Worker `TCM_ON_FINISH_FRAME`: post the completion semaphore, then block on the continue semaphore.
- `TCM_NEXT_FRAME`: assert no frame pending; if state is EXITED return; otherwise set pending and post the continue semaphore exactly once.
- `TCM_PAUSE_FRAME`/`TCM_RESUME_FRAME`: support stopping midway through a frame. They are not interchangeable with the finish/next pair.
- BOOT and SHUTDOWN states are explicitly invalid for thread-control calls. Enum order at line60 makes `state >= FIRST_FRAME` equivalent to FIRST_FRAME or RUNNING in this version.

`GFX_Events` at lines1772 onward calls `GFX_AdvanceFrame` before draining the event queue. The latter blocks at `TCM_ON_FINISH_FRAME` at line1649. Events queued while the worker is parked will be drained immediately after its next release, giving a useful deterministic input boundary.

## Recommended task-owned instrumentation

For the software-rendered, fixed-cycle, no-frame-skip reference-capture profile:

1. Immediately before `input_poll_cb`, call `DBP_ThreadControl(TCM_FINISH_FRAME)` only if state is FIRST_FRAME or RUNNING. Preserve existing startup, reboot, shutdown and early-return handling. Using explicit state equality is clearer than relying on enum order.
2. The frontend queues keyboard transitions until this `input_poll_cb`, then delivers them on the frontend thread in recorded order. It also exposes a fixed mouse/button state for that poll. No keyboard callback should be delivered between these synchronized polls.
3. Retain the existing later `TCM_FINISH_FRAME` call: it becomes an idempotent no-op for ordinary capture frames. This avoids broad surgery to initial-frame and state-management logic.
4. Remove the normal-path resume/next call from its current pre-callback position. Place it once, at the end of the normal path, after audio, software-video and any standalone OSD callbacks.
5. Hash/copy pixel data and sample the guest PIT counter, palette and relevant RAM **inside the video callback**, before the worker is released. Reading RAM after `retro_run` returns remains a race because the final release has already happened.

Conceptual order:

```text
finish previous pending emulation frame
poll and queue next input batch while worker is parked
mix/copy audio from completed frame
copy video and sample guest state from completed frame
release worker once to consume that input batch and produce next frame
```

This preserves the core's pipelined design. Input polled during callback-indexN is eligible for the next emulated frame, not the already-completed image being delivered in callbackN. Record both input-poll index and completed-frame index so comparison tools do not silently introduce a one-frame offset.

## Deadlock and frame-count boundaries

The additional FINISH call does not create a second frame or consume a second semaphore when `pending` is already false. FIRST_FRAME is valid: initialization sets pending=true before starting the worker (lines2825–2827). The existing first-frame finish remains safe after the new early finish. EXITED/REBOOT/BOOT/SHUTDOWN should not enter the new barrier; preserve their existing early-return paths. `TCM_NEXT_FRAME` already refuses to wake EXITED state.

The patch must retain exactly one normal-path NEXT release. Calling NEXT twice violates its pending assertion and can leave extra semaphore credits. Calling RESUME in its place when pending=false does nothing and leaves emulation parked.

Disable frame skipping and multiplayer fpsboost for this capture profile. With early FINISH, a later PAUSE on a skip call sees no pending frame, and its paired RESUME does nothing. That does not necessarily deadlock—the next non-skipped call can release a new frame—but it changes skip/pipeline behavior and can drop a just-finished frame from the emitted sequence. A strict capture build should assert `skip_emulate == false`, use no network session, and configure throttling so `DBP_NeedFrameSkip` returns0 in both frontend and worker paths. Frame-stepping throttle is an explicit no-skip path in lines653–675; an accurately matched emulation/video rate is another.

The review covers the software path used by Treehouse. An OpenGL presentation path might have its own worker synchronization; do not generalize this patch to that path without examining it.

## Remaining verification

The hook removes the identified input-boundary and RAM-sampling races, but it is not proof of deterministic replay until rebuilt runs agree. Repeat identical full input replays and compare every callback's pixel hash, synchronized game tick and audio hash. Capture reset, key-down/up and mouse-down/up transitions as well as stable held states. Keep fixed CPU cycles and recorded core configuration.

`DBP_GetTicks` uses host `time_cb` at lines1294–1297, and CPU auto-adjust uses measured timing elsewhere in the same source. Fixed-cycle operation avoids that auto-adjust path; touchpad gesture timing still depends on host ticks, so use direct mouse mode for this reference protocol. The engine's60Hz game counter should be read from guest RAM at the synchronized callback, not substituted with frontend wall time.
