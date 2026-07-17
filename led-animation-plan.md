# LED Animation Rework Plan

Rework the RGB LED code so animation never blocks the main loop, and make the
animation effect configurable per profile.

## Current state

- `led.py` — `Led` owns three `pwmio.PWMOut` channels (GP21/GP20/GP19, 1 kHz)
  plus the onboard LED. `fadeToRGBLedColor(red, green, blue)` is a blocking
  loop: ~21 steps with `time.sleep(0.01)` between them (~210 ms of dead input
  per call).
- Call sites (`code.py`): twice at boot (green, then blue) and once in
  `setRunValuesFromCurrentProfile()` — so every profile switch costs ~210 ms of
  frozen inputs.
- Per-profile color lives in the profile dict as
  `"rgb": {"red": 0-255, "green": 0-255, "blue": 0-255}`, read via
  `profileHelper.getRGBLedValues()`.
- The main loop is free-running (no throttle), which makes it a good clock for
  driving animation frames.

## Goals

- Zero blocking sleeps on any code path that runs after boot.
- Animation effect selectable per profile, stored in the profile JSON.
- Backward compatible: existing `config.json` files and the current serial
  protocol keep working unchanged; profiles without animation config behave
  exactly as today (fade to static color).
- No new dependencies, no meaningful new RAM or GC pressure in the main loop.

## Non-goals

- Changing the boot sequence feel (boot fades may remain blocking — inputs
  aren't live yet anyway).
- Touching `boot.py`, the HID descriptors, or the onboard LED (`setLedState`).
- Manager-app UI work. The protocol additions below are readable/writable by
  the existing generic `getProfile` / `setProfileValue` plumbing, so app
  support can land later.

## Design

Keep one `Led` object. Split today's "compute target + block until done" into
"start animation" + "pump from the main loop":

```
led.startEffect(effectConfig)   # sets state, returns immediately
led.update()                    # called once per main-loop iteration
```

`Led` keeps small animation state: the active effect name, the base (profile)
color, the color shown at the moment the effect started (so fades start from
what's actually on the LED), a start timestamp, and the last duty values
written. `update()` computes the current frame from elapsed time and writes
PWM duty cycles. If no RGB LED is configured (`redPwm is None`), both methods
no-op exactly as today.

Keep `fadeToRGBLedColor(red, green, blue)` as a thin **blocking wrapper**
around the engine (start a `fade` effect, then `update()` + small sleep until
finished). The two boot call sites keep using it, so boot looks and behaves
exactly as now, and there is only one animation implementation to maintain.

### Engine internals (led.py)

- Timing: `time.monotonic()` captured at `startEffect`; per `update()`,
  `elapsed = time.monotonic() - self.startTime`.
- Phase: `phase = (elapsed % period) / period` gives a 0.0–1.0 sawtooth for
  periodic effects. Float math at ~100 Hz update rate is fine on RP2040; do
  not compute per loop iteration faster than needed (see throttling below).
- Color mapping reuses the existing helpers: 0–255 channel → 0–100% →
  `duty_cycle(percent)` → 0–65535.
- Only write `pwm.duty_cycle` when the value actually changed (compare against
  the stored last duties). Steady effects then cost one comparison per frame,
  and even animated effects skip redundant writes.
- No allocations in `update()`: no lists/tuples created per frame; keep the
  three duty values as plain attributes.

## Config format (per profile)

Keep the existing `rgb` key as the base color. Add one optional key:

```json
"ledEffect": { "effect": "fade", "speed": 1000 }
```

- `effect`: one of `instant`, `fade`, `pulse`, `blink`, `cycle` (see effect
  notes below). Missing/unknown → `fade` (today's behavior).
- `speed`: effect-specific, milliseconds. For `fade`: transition duration.
  For `pulse`/`blink`/`cycle`: period of one full cycle. Clamp to a sane
  range (100–60000) on ingest.

Rules:

- `ledEffect` absent → behave as `{"effect": "fade", "speed": 1000}`.
- Old firmware reading a config that has `ledEffect` ignores it harmlessly
  (unknown profile keys pass through untouched everywhere today).
- `config.saveToFile()` / `getDataJson()` serialize `profiles` wholesale, so
  persistence needs **no config.py changes**.

## Integration points

- `profileHelper.py` — add `getLedEffect(profile)`: returns the parsed effect
  dict with defaults applied, validating `effect` against the known list and
  clamping `speed`. Mirrors how `getRGBLedValues` tolerates missing data.
- `code.py` / `setRunValuesFromCurrentProfile()` — replace the
  `fadeToRGBLedColor(...)` call with:
  fetch `rgb` + `ledEffect`, then `led.startEffect(rgb, effect)`. Boot calls
  to `fadeToRGBLedColor` stay as they are.
- `code.py` main loop — call `led.update()` once per iteration (next to the
  existing `stick.doStickCalculations` area is fine).
- `profileManager.setProfileValue()` — accept `valueName == "ledEffect"` and
  store the dict on the profile (same pattern as the existing `rgb` branch).
  The existing `handleSetProfileValue` serial handler and its
  `{"profileChange": True}` return already trigger a reload, which restarts
  the effect — no new wire commands needed.

## Effect implementation notes

All effects render into the three PWM channels from the profile base color
`(r, g, b)` (0–255 each) and a brightness multiplier `k` in 0.0–1.0:
`channel = int(base * k)`, then through the existing 0–255 → duty mapping.
`k = 1` means "show base color".

- `instant` — write `k = 1` once in `startEffect`; `update()` does nothing.
- `fade` — non-blocking version of today's behavior. Store the starting
  duties at `startEffect`; each frame compute `t = min(elapsed / speed, 1)`,
  interpolate each channel from start to base, write, and stop updating at
  `t == 1`. This is also what the blocking boot wrapper uses.
- `pulse` (breathing) — `k` follows a triangle wave:
  `k = 2 * phase if phase < 0.5 else 2 * (1 - phase)`. Cheap and looks smooth;
  a sine (`math.sin`) also works but the triangle avoids float trig per frame.
  Floor `k` at ~0.05 rather than 0 if true-off looks like a dead device.
- `blink` — `k = 1 if phase < duty else 0`, with `duty` fixed at 0.5 (or a
  third optional config field later). Good for "profile active but attention"
  states.
- `cycle` (rainbow) — ignores base color; hue = `phase * 360`, convert
  HSV(h, 1, 1) → RGB with a small sector-based helper (no floats needed:
  hue sector 0–5, integer interpolation per channel). Write a tiny local
  `hsv2rgb` in `led.py`; do not import colorsys (not in CircuitPython).

Shared concerns:

- Update throttle: recompute a frame at most every 10 ms (100 Hz) — compare
  `elapsed` against a stored `lastFrameTime` and return early otherwise.
  Human-visible PWM blending needs nowhere near the full main-loop rate, and
  this keeps the per-iteration cost near zero.
- Gamma: raw linear duty looks dim in the mid-range. Optional: apply a small
  16-entry gamma lookup table when mapping brightness → duty. Note it as a
  polish step, not required for v1.
- PWM frequency: keep 1 kHz; lower brightness values can flicker slightly at
  low duty — acceptable, the `pulse` floor above hides it.
- Profile switch mid-animation: `startEffect` simply retargets (fade starts
  from current duties; periodic effects restart their phase). No special
  handling.

## Testing

- Extend the CPython stub-harness approach used for the reliability fixes:
  stub `board`/`pwmio`/`time` with a fake clock, drive `led.py` directly, and
  assert: `update()` never sleeps (no `time.sleep` in the non-blocking path),
  duty writes stop once `fade` completes, unknown effect names fall back to
  `fade`, and `speed` clamping behaves.
- Grep check: `time.sleep` may only appear in the blocking boot wrapper.
- On-device checklist: profile switch responsiveness during `pulse`, serial
  `setProfileValue` with `ledEffect` survives save/reboot, old config without
  `ledEffect` behaves identically to current firmware.

## Rollout order

1. `led.py`: engine + blocking wrapper, behavior-neutral for existing calls.
2. `code.py`: `led.update()` in the main loop; boot untouched.
3. `profileHelper.getLedEffect` + `setRunValuesFromCurrentProfile` switch to
  `startEffect` (still defaulting to `fade` — behavior-neutral).
4. `profileManager.setProfileValue` `ledEffect` branch.
5. New effects land one at a time behind the `effect` key.
6. Manager app picks up the new optional key whenever convenient.
