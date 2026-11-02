# TuFFpad Reliability and Performance Implementation Plan

## Purpose

This plan converts the firmware review findings into small, ordered units of work.
Each phase must be independently reviewable, testable, shippable, and suitable for
one commit in each affected repository. Do not commit or push unless the user
explicitly asks for that separate action.

The repositories are:

- TuFFpad: `rasp-pi-pico-narwhal`
- Waveshare joystick: `waveshare-joystick`

Implement each shared phase in TuFFpad first, port it to Waveshare in the same
phase, and test both before considering the phase complete. A logical phase may
therefore produce one commit in each repository, but the two ports must not drift
into different behavior.

## Decided behavior and scope

These are requirements, not choices for the implementing agent:

1. Reject deletion of the final profile.
2. Keep the existing six-regular-key USB HID keyboard format. Do not implement
   NKRO in this work.
3. More than six requested regular keys must never crash the firmware. Preserve
   already-active keys, leave excess keys pending, and activate pending keys when
   report slots become available. Modifier keys remain independent of the
   six-regular-key limit.
4. Profile changes are layer-like. Ordinary held controls immediately use their
   new bindings. Controls that could repeatedly trigger profile navigation are
   latched until released.
5. A held control whose binding is equivalent in the old and new profiles should
   remain logically pressed without an unnecessary release/repress cycle.
6. Do not add a momentary-layer binding or management-app protocol feature in
   this plan. That can be a separate future feature.
7. Preserve the existing serial command names, device handshake responses, and
   `getSaveData` string payload format. Invalid commands should receive failure
   responses where the command already has a response shape; do not invent a new
   generic error protocol.
8. Keep TuFFpad-only keypad, D-pad, hat, and RGB behavior out of Waveshare unless
   a shared helper naturally supports it without enabling hardware features.

## Engineering rules

- Keep the main loop cooperative. Do not add threads, interrupts, or async code.
- Do not add external dependencies.
- Do not change the USB descriptors except where a phase explicitly says not to
  change them. In particular, keyboard overflow handling must not alter HID.
- Preserve the current device-specific pins, default profiles, and handshake:
  TuFFpad answers `areyouatuffpad?`; Waveshare answers
  `areyouatuffjoystick?`.
- Avoid steady-state allocations in the main loop. Allocations caused by a serial
  command, profile transition, or HID edge are acceptable when bounded.
- Do not catch broad exceptions around the entire main loop. Validate expected
  bad input and handle specific I/O exceptions only at their actual boundaries.
- A state variable must represent exactly one concept. Physical switch state,
  binding state, requested HID state, successfully sent HID state, and profile
  navigation latch state must not be conflated.
- Every successful serial mutation must return `True`; every rejected or invalid
  mutation must return `False` and leave runtime and stored configuration
  unchanged.
- Do not silently accept a setting in RAM but reject it in the runtime stick or
  keyboard-mode objects. Apply validated changes atomically to all affected
  objects.
- After every phase, run `git status` in both repositories and remove generated
  caches, logs, or other artifacts not intended for the commit.

## Verification conventions

There is no persistent test suite in these repositories. Unless the user later
requests one, use temporary or inline CPython harnesses with hardware stubs and
do not commit test scaffolding. Set `PYTHONDONTWRITEBYTECODE=1` so harnesses do
not leave `__pycache__` directories.

Pure modules can be imported directly. Hardware modules need small stubs for
`board`, `analogio`, `digitalio`, `usb_hid`, `usb_cdc`, `keypad`, `pwmio`, and
`micropython` as applicable. Do not execute an infinite `code.py` loop in a
harness; test extracted classes/functions, or arrange a controlled exception
after a known number of iterations.

CPython checks establish algorithmic behavior only. Before shipping each phase,
perform its listed on-device checks on TuFFpad and, for shared phases, on
Waveshare. Record any check that could not be performed; do not describe untested
hardware behavior as verified.

## Dependency chain

1. Make deadzone math safe.
2. Validate global settings and stick boundaries.
3. Harden serial parsing and command responses.
4. Normalize profiles and enforce profile lifecycle rules.
5. Separate physical input state from aggregated HID output state.
6. Make TuFFpad runtime RGB fades non-blocking.
7. Implement immediate layer-style profile remapping and navigation latches.
8. Make configuration persistence recoverable and bound management memory use.
9. Eliminate redundant gamepad report packing.
10. Reduce steady-state stick math and allocation pressure.
11. Make runtime USB writes retry safely.

Phases 1-4 deliberately come before the input rewrite so the later state machine
only handles validated data. Phase 6 precedes phase 7 because a blocking fade
would otherwise delay immediate remapping and could lose keypad events. Phases
9-11 are optimizations/hardening and must not change the behavior established by
phases 1-8.

---

## Phase 1: Make deadzone math safe

### Goal

Prevent boot-time stick movement or a large configured deadzone from causing a
zero/negative denominator, inverted axes, or a stick that can never leave its
deadzone.

### TuFFpad changes

1. In `stickDeadzone.py`, define one module-level maximum radial deadzone of
   `0.99`.
2. In `initBoundary()`, calculate the existing value:
   `originalDeadzoneMagnitude + deadzoneBuffer`, then clamp it to the inclusive
   range `0.0` through `0.99` before assigning `deadzoneMagnitude`.
3. In `stick.py`, defensively apply the same clamp when copying
   `deadzone.deadzoneMagnitude` in `setDeadzone()`. This preserves the invariant
   even if another caller changes the deadzone object directly.
4. Do not change calibration duration, raw boundary collection, `baseDeadzone`,
   upper/lower boundary reporting, or normal deadzone scaling.
5. Remove no public getters and change no serial commands.

### Waveshare port

Port the identical `stickDeadzone.py` and `stick.py` changes. These files are
currently byte-identical and should remain so after this phase.

### Tests

- With a normal centered calibration, verify output before and after the change
  is identical for representative centered, cardinal, and diagonal inputs.
- Set `originalDeadzoneMagnitude = 1.1` and `deadzoneBuffer = 0.1`, call
  `initBoundary()`, and verify the resulting runtime deadzone is `0.99`.
- With that moved calibration, feed full positive X/Y and verify both outputs
  are positive and reach `127`, not negative values.
- Test configured buffer values `1`, `32768`, and `65535`; none may produce a
  denominator of zero or a negative denominator.
- On both devices, boot while holding the stick off-center, then verify all
  directions still move in the correct direction and return to center.

### Ship criteria

No normal-calibration behavior change, no inversion after moved calibration,
and identical shared module behavior on both devices.

---

## Phase 2: Validate global settings and stick boundaries

### Goal

Make global configuration setters reject malformed values without mutation,
prevent equal/reversed axis limits, and stop valid-but-malformed global JSON from
crashing startup.

### TuFFpad changes

1. Add small validation helpers in `config.py` or `stickCommon.py` for:
   - Integer conversion that accepts existing integer strings, rejects booleans,
     rejects fractional floats, and catches `TypeError`/`ValueError`.
   - Actual Boolean values for orientation reversal; do not use `bool(value)` on
     arbitrary input.
2. Standardize configuration setters to return `True` on mutation and `False` on
   rejection. Update every caller; do not leave keyboard-mode handlers passing a
   Boolean result into `setXStartOffset()` as though it were a numeric offset.
3. Validate raw stick boundaries as integers from `1` through `65535` and require
   `low < high` for each axis. Check the candidate against the other current
   limit before mutating anything.
4. Restrict orientation axis to integer `0` or `1`. Require `reverse` to be a
   JSON Boolean. Parse the entire orientation candidate before assigning either
   field so failure cannot partially update it.
5. Preserve the existing external deadzone numeric range; phase 1 already makes
   its mapped value safe.
6. Restrict keyboard-mode X/Y offsets and Y cone end to integers from `1`
   through `127`. Do not add a new requirement that cone end be greater than the
   X offset in this phase.
7. Make serial boundary handlers call the validating configuration setter first.
   Only when it returns `True` may they update both `stick` and `stickDeadzone`.
   Return the actual Boolean result over serial.
8. Apply the same validate-then-apply ordering to orientation, deadzone, and
   keyboard-mode settings. Invalid values must not trigger orientation reloads,
   deadzone recomputation, or runtime profile reloads.
9. Rework `loadFromFile()` for global fields:
   - Require the top-level JSON value to be a dictionary.
   - Start with existing defaults.
   - Load each global field through its validator rather than replacing whole
     dictionaries.
   - Missing or invalid global fields retain defaults while other valid fields
     still load.
   - Keep syntactically invalid JSON behavior: use defaults without crashing.
   - Profile normalization is phase 4; for now, do not add new profile semantics.

### Waveshare port

Port all shared validators, setters, serial handlers, and global loading behavior.
Do not copy TuFFpad default keypad, thumb, D-pad, or RGB fields into Waveshare.
The only intentional `serialHelper.py` difference remains the handshake response.

### Tests

- For every numeric setter, test valid values, zero, negatives, values above the
  maximum, `None`, Booleans, lists, dictionaries, fractional floats, integer
  strings, and non-numeric strings.
- Verify `low == high` and `low > high` are rejected for both axes and return
  `False` over serial without changing config or runtime values.
- Verify valid high/low updates reach config, `Stick`, and `StickDeadzone` and
  stick calculations do not divide by zero.
- Verify orientation `{"axis": 0, "reverse": "false"}` is rejected rather than
  storing `True`; test axes `-1`, `2`, and string `"1"`.
- Verify invalid keyboard-mode values do not alter `KbMode` and valid values do.
- Load global JSON objects with missing keys, wrong container types, and invalid
  individual fields. Startup must retain usable defaults for invalid fields.
- Exercise every setting through the real serial handler, not just the config
  method, and check both payload and runtime result.
- On both devices, confirm the management app can read and change every global
  setting and save/reboot retains valid values.

### Ship criteria

No invalid global value is acknowledged as successful, no valid update is only
partially applied, and no tested global config shape can crash stick math.

---

## Phase 3: Harden serial parsing and command responses

### Goal

Ensure malformed but syntactically valid commands cannot crash the firmware and
that management requests do not silently disappear.

### TuFFpad changes

1. Keep the existing line-based JSON protocol and single-element array
   normalization for value-less commands.
2. Add per-command payload validators before accessing nested fields. Validate
   the complete payload before calling a manager or config object.
3. Required payload shapes include:
   - `setActiveProfile`, `getProfile`, `createNewProfile`, and `deleteProfile`:
     one non-empty string name.
   - `renameProfile`: a dictionary containing non-empty string
     `oldProfileName` and `newProfileName`.
   - `setProfileValue`: a dictionary containing string `profile`, string
     `valueName`, and a present, non-`None` `value`.
   - `reorderProfile`: a dictionary containing string `profileName` and an
     integer-compatible `position` accepted by the existing reorder rules.
   - Global setters: the scalar or orientation shape validated in phase 2.
4. A malformed recognized mutation returns its command name with `False` and has
   no side effects. Do not allow `KeyError`, `TypeError`, or `ValueError` from
   ordinary payload access to escape the dispatcher.
5. Make query behavior deterministic:
   - `getProfiles` always responds with a list, including `[]` if empty.
   - `getActiveProfile` responds with the active name or `None`.
   - `getProfile` responds with the profile or `None`.
   - Existing ping, global-settings, save-data, and stick-read response shapes
     remain unchanged.
6. `handleSetProfileValue()` must request a runtime profile reload only when the
   mutation succeeded. Phase 4 will further narrow reloads to the active profile.
7. Replace the current oversized-input tail-splicing behavior with an explicit
   overlong-line state:
   - Keep the 512-byte command limit.
   - Once a line exceeds the limit, discard bytes through its next newline.
   - Resume parsing at the first byte after that newline.
   - Never combine the tail of an overlong line with the next valid command.
8. Limit work to one complete inbound command per main-loop iteration, as today.
9. Do not add a blanket `except Exception` around dispatch. JSON decode errors,
   Unicode errors, and expected validation errors should be handled locally.

### Waveshare port

Port the complete phase except for preserving the Waveshare handshake response.
The serial helpers should otherwise remain identical.

### Tests

Use a fake CDC object whose input can be supplied in arbitrary chunks and whose
output records complete responses. Cover:

- Split commands one byte at a time and several commands in one read.
- CRLF, LF, blank lines, invalid UTF-8, invalid JSON, scalar JSON, unknown
  commands, and unexpected arrays.
- Every recognized mutation with `null`, missing nested keys, wrong container
  types, and wrong value types; expect `False` and no mutation.
- Empty profile lists and missing profiles; expect a response rather than a
  timeout.
- A rejected `setProfileValue`; verify no profile reload flag is returned.
- Inputs of 511, 512, 513, and several thousand bytes, including an overlong line
  immediately followed by a valid ping; the ping must be parsed cleanly.
- Management-app discovery, ping, get, and normal mutation flows on both devices.

### Ship criteria

All malformed command cases leave the main loop alive and state unchanged, all
query cases have deterministic responses, and valid app traffic is unchanged.

---

## Phase 4: Normalize profiles and enforce lifecycle rules

### Goal

Guarantee a valid active profile, reject ambiguous names and final-profile
 deletion, and prevent malformed stored profile data from crashing runtime or
serial operations.

### TuFFpad changes

1. Add explicit profile limits as named constants: maximum 32 profiles and
   maximum 64 UTF-8 bytes per profile name. Reject over-limit creation/rename and
   reject names that are empty or not strings. Do not silently truncate names.
2. Require unique names for `createNewProfile()` and `renameProfile()`. Renaming
   a profile to its own current name may return `True` without changing order or
   runtime state.
3. Reject `deleteProfile()` when exactly one profile remains. Return `False`, do
   not change `currentProfileIndex`, and do not request a runtime reload.
4. Preserve the existing active-index adjustments for successful deletion and
   reorder. Add focused tests for active profiles before, at, and after the
   affected index.
5. Normalize profiles during config load:
   - Start each accepted profile from a fresh device-specific default profile.
   - Require a valid unique name; skip invalid/duplicate entries.
   - Merge valid known fields and retain unknown optional fields for forward
     compatibility.
   - Invalid known nested fields use defaults rather than remaining malformed.
   - Require `isKbModeEnabled` to be an actual Boolean.
   - Require binding IDs to be strings. Unknown binding strings may remain stored
     for forward compatibility, but `ProfileHelper.getAction()` must continue to
     map them to a disabled action rather than raising.
   - RGB channels must be integers from `0` through `255` on TuFFpad.
   - TuFFpad `keys` must contain exactly 20 string entries; D-pad must contain
     up/down/left/center and keyboard mode must contain up/down/left/right.
   - If no valid profiles remain, install one default profile named `1`.
6. Make `ProfileManager` loops use normalized assumptions only after config
   normalization. Keep defensive dictionary/name checks in public lookups so a
   malformed caller-supplied config does not cause avoidable crashes.
7. In `setProfileValue()`, validate the target nested structure and index before
   mutation. TuFFpad key indices must be `0` through `19` and also less than the
   actual target `keys` length. Do not partially parse or partially apply values.
8. Return a reload flag from `handleSetProfileValue()` only when the update
   succeeded and the edited profile is active. Editing an inactive profile needs
   no runtime reload.
9. Renaming and reordering do not require rebuilding bindings. Successful active
   profile selection and deletion do. Preserve current selection semantics.
10. Ensure startup always calls `setRunValuesFromCurrentProfile()` with a valid
    profile after normalization.

### Waveshare port

Port profile count/name rules, uniqueness, final-delete rejection, active-index
handling, active-only reloads, and general normalization. Use Waveshare defaults
and fields: no 20-key list, thumb button, D-pad, or RGB requirements. Preserve the
TuFFpad-only `dpad center` difference and do not copy TuFFpad defaults.

### Tests

- Create duplicate names, rename to an existing name, empty/non-string names,
  64-byte and 65-byte UTF-8 names, and profile counts 32 and 33.
- Delete the only profile; expect `False`, unchanged runtime, and no reload.
- Delete active first/middle/last profiles with at least two remaining; verify
  the selected replacement and index.
- Reorder the active profile and profiles around it; verify object identity and
  index remain correct.
- Load empty profile lists, non-list profiles, duplicate names, missing nested
  dictionaries, short/long TuFFpad key lists, wrong binding types, invalid RGB,
  and unknown future fields. Verify a valid default/normalized result.
- Set valid and invalid values on active and inactive profiles; verify only a
  successful active mutation requests reload.
- On both devices, verify create/rename/reorder/delete/save/reboot and active
  profile behavior through the management app.

### Ship criteria

There is always at least one valid profile, names are unambiguous, inactive edits
do not disturb live controls, and malformed profile storage cannot crash tested
startup or command paths.

---

## Phase 5: Separate physical state from aggregated HID output

### Goal

Fix duplicate-binding releases, mixed hat/non-hat directions, keypad event
backlog, and six-key crashes without yet changing profile-transition policy.

### Design required for this phase

Create a shared, hardware-independent `ActionManager` module rather than adding
more global dictionaries to `code.py`. It may call the supplied keyboard/gamepad
objects but must not import board or USB modules itself.

The manager must maintain distinct state for:

1. Physical/logical input state indexed by the existing state names.
2. Current binding for each state name.
3. Desired keyboard keys, gamepad button mask, and hat value derived from all
   bindings and physical states.
4. Successfully applied keyboard keys/gamepad outputs used to calculate deltas.
5. Pending profile-next/profile-previous edge events.

Provide explicit methods to set a binding, set a physical state, read a physical
state, consume a profile navigation event, and apply dirty outputs. Setting
physical state must work even when the binding is `None` or disabled. Output
recomputation must happen only when physical state or bindings change, not on
every free-running loop iteration.

### TuFFpad changes

1. Register stick click, thumb, four keyboard-mode stick directions, five D-pad
   directions, and 20 matrix keys with stable state names matching current code.
2. Update direct-button physical states from pin samples every loop. Update
   keyboard-mode direction states from `KbMode.calculateStickInput()`.
3. Drain `keyMatrix.events.get()` in a bounded loop until empty during each main
   loop iteration. Process every event in order. The bound is the queue capacity
   plus a small margin; document the chosen bound and avoid an endless loop if a
   stub always returns events.
4. Aggregate keyboard output across all controls:
   - Two controls holding the same key produce one desired key.
   - Releasing one control releases that key only if no other held control wants
     it.
   - Apply releases before new presses so freed slots can be reused.
   - Keep already-applied regular keys when more than six are desired.
   - Add pending regular keys in stable binding-registration order as slots become
     available.
   - Handle modifiers separately and preserve all requested modifier bits.
   - Never call `Keyboard.press()` with a seventh distinct regular key.
5. Aggregate gamepad buttons as one 16-bit mask. Releasing one input must not
   clear a bit still requested by another input.
6. Calculate hat only from D-pad physical states whose current binding type is
   hat. A direction bound to a keyboard key, gamepad button, profile action, or
   disabled action must not contribute to the hat. Preserve current diagonal and
   opposite-direction resolution.
7. Generate profile-next/previous only on a physical released-to-pressed edge.
   Do not generate navigation from output reconciliation.
8. Flush aggregated HID changes once after all inputs for that iteration have
   been processed, avoiding transient reports between queued matrix events.
9. On a profile change in this phase only, preserve the old neutral-first policy:
   release applied outputs, keep ordinary physical states from activating new
   bindings until repress, and retain navigation repeat protection. Implement
   this explicitly rather than relying on stale `actionStates`. Phase 7 replaces
   this policy.
10. Allocations during an input edge are acceptable; no new lists, dictionaries,
    sets, or JSON objects may be created on a no-change loop iteration.

### Waveshare port

Port `ActionManager` and the shared code integration for stick click and four
keyboard-mode directions. Do not register nonexistent matrix, thumb, D-pad, or
hat controls. Shared aggregation tests must include keyboard/gamepad duplicates;
six-key overflow is defensive on Waveshare even though its physical controls
cannot normally reach it.

### Tests

Use fake keyboard/gamepad objects that record every press/release/report:

- Hold the same keyboard key through two controls, release either one, and verify
  the key stays pressed until both release. Repeat for a gamepad button and a
  modifier.
- Hold seven or more regular keys; verify no exception, at most six applied, and
  stable pending behavior. Release an active key and verify exactly one pending
  key takes the freed slot without unnecessarily releasing other keys.
- Hold TuFFpad hat-up and keyboard-right together; verify hat reports up only.
  Test all eight hat directions, neutral, and opposite directions.
- Feed multiple queued matrix press/release events in one iteration; verify all
  are processed in order and only the final necessary HID deltas are emitted.
- Verify disabled and unknown bindings still track physical state without HID.
- Verify next/previous fires once per fresh press and not on release or rebuild.
- Verify no-change iterations do not allocate new output collections or send HID.
- Exercise the phase-specific neutral-first transition test as a baseline for
  phase 7.
- On both devices, test chords, duplicate bindings, profile navigation, keyboard
  mode, and all device-specific controls.

### Ship criteria

No duplicate early releases, no phantom hat input, no keypad backlog under normal
burst input, no seven-key crash, and no change yet to the agreed immediate-remap
work to be delivered in phase 7.

---

## Phase 6: Make TuFFpad runtime RGB fades non-blocking

### Goal

Remove the roughly 210 ms input stall on runtime profile updates while retaining
current fade appearance and boot behavior.

### TuFFpad changes

1. Keep `fadeToRGBLedColor()` as the blocking boot wrapper used by the two boot
   call sites. Do not change the boot LED sequence in this phase.
2. Add a small non-blocking runtime fade API to `Led`, with methods equivalent to
   `startRGBFade(red, green, blue)` and `update()`.
3. `startRGBFade()` must validate/clamp channels using existing behavior, set the
   three channels to black as the current runtime fade does, store target duty
   cycles and `time.monotonic()` start time, and return without sleeping.
4. Use a total runtime fade duration of 0.21 seconds, not the 1000 ms proposed by
   the older animation plan. Preserve the existing black-to-target behavior for
   compatibility. Starting from current color and configurable effects are out
   of scope.
5. `update()` must return immediately when no fade is active or RGB PWM is not
   configured. Limit frame writes to at most once every 10 ms. Compute progress
   from elapsed time, clamp to `1.0`, write duties, and mark the fade complete at
   the endpoint.
6. Do not allocate lists/tuples in `update()`. Store channel duties and timing in
   plain attributes. Avoid redundant duty writes after completion.
7. Replace the runtime call in `setRunValuesFromCurrentProfile()` with
   `startRGBFade()`. Call `led.update()` once per main-loop iteration.
8. Keep unknown/missing RGB behavior unchanged: no RGB update when values are
   absent.
9. Do not implement the configurable `ledEffect` protocol or effects from
   `led-animation-plan.md` in this phase.

### Waveshare port

No RGB fade port. Waveshare has a different NeoPixel/boot LED implementation and
no runtime profile RGB fade. Do not copy TuFFpad PWM code or add `led.update()`
calls to Waveshare.

### Tests

- Drive `Led` with fake PWM and fake monotonic time. Verify start returns without
  sleeping, channels begin at black, intermediate frames progress toward target,
  and the final target is exact.
- Verify updates before 10 ms do no work, completed fades do no further writes,
  and a new fade replaces the old target cleanly.
- Verify boot wrapper behavior remains blocking and reaches the same target.
- On TuFFpad, hold and tap matrix/direct controls during repeated profile
  changes. Verify no 210 ms freeze and no lost releases.
- Verify serial ping and stick reads remain responsive during a fade.

### Ship criteria

Runtime fades retain their approximate current appearance while input, serial,
and stick processing continue throughout the animation.

---

## Phase 7: Implement immediate layer-style profile remapping

### Goal

Make ordinary held controls follow new profile bindings immediately while
preventing profile-switch controls from repeating or activating accidental new
actions.

### TuFFpad changes

1. Extend `ActionManager`; do not reintroduce profile behavior into scattered
   `code.py` conditionals.
2. On every successful active-profile change:
   - Install all new bindings before output reconciliation.
   - Read the already-tracked physical states; do not infer them from the old
     HID reports.
   - Recompute desired outputs for ordinary held controls immediately.
   - Diff old and new desired outputs. Preserve equivalent held outputs instead
     of issuing blanket `release_all()` calls first.
3. Maintain a set of latched physical control names for profile transitions:
   - Always latch the control that initiated the change until it is released.
   - Latch every other currently held control whose old or new binding is a
     profile-next/profile-previous action until that control is released.
   - A latched control produces no keyboard, gamepad, hat, or further profile
     action, even if its new binding is ordinary. This specifically prevents the
     layer switch control from activating an unrelated binding in the new
     profile.
   - Continue tracking physical releases while latched. On release, remove the
     latch without emitting a phantom HID release. A subsequent press is a fresh
     edge and follows the current binding normally.
4. Ordinary non-latched controls that were already held must activate their new
   binding immediately. If the old and new desired HID output is identical, send
   no release/repress pair.
5. Clear/rebuild pending six-key state using the same aggregation rules. Do not
   exceed six regular keys during a transition; preserve still-valid active keys
   before filling pending slots.
6. Recompute the hat solely from eligible new-profile hat bindings and physical
   D-pad state. A profile transition must not resurrect stale directions.
7. Process navigation and serial active-profile changes through the same
   transition function. If both occur in one iteration, define one order: apply
   the serial selection first, then at most one physical navigation request, and
   rebuild outputs only once for the final profile.
8. Keep edits to inactive profiles reload-free as established in phase 4.
9. Do not implement release-to-restore/momentary layers in this phase.

### Waveshare port

Port the same `ActionManager` transition/latch behavior and serial/navigation
ordering for stick click and keyboard-mode directions. There is no RGB work in
this port. Do not add TuFFpad-only state names to Waveshare integration.

### Tests

- Hold an ordinary control bound to `A` in profile 1 and `B` in profile 2;
  switch profiles and verify `A` releases and `B` presses without waiting for
  physical release.
- Repeat with `A` in both profiles; verify no release/repress pair.
- Hold the next-profile control through several iterations; verify exactly one
  transition, no action from its new binding, and normal behavior only after
  release/repress.
- Hold a second profile-navigation control during a transition; verify it cannot
  cause a chained transition until released.
- Switch while multiple duplicate bindings are held; verify output ownership
  remains correct.
- Switch with more than six desired regular keys and verify stable pending-key
  behavior throughout.
- Switch with mixed hat/non-hat D-pad bindings and held directions; verify only
  new hat-eligible directions contribute.
- Issue a serial active-profile command and physical navigation in the same
  iteration; verify the documented order and one final output rebuild.
- On both devices, test quick next/previous layer changes with directions and
  buttons already held, plus long-lived profile changes.

### Ship criteria

Layer switching is immediate for ordinary controls, navigation cannot
auto-repeat, equivalent outputs remain pressed, and no stale or phantom outputs
appear after any tested transition.

---

## Phase 8: Make persistence recoverable and bound management memory use

### Goal

Avoid false save success and unrecoverable power-loss windows while keeping
management operations within bounded memory.

### TuFFpad changes

1. Require `f.write(configJson)` to equal the complete string length before
   treating the temporary file as valid. Close the file before rename.
2. Catch expected `OSError` failures around temporary write, backup rotation,
   rename, remove, and cleanup. Return `False` rather than crashing or claiming
   success. Keep the existing read-only-filesystem diagnostic.
3. Implement a recoverable two-file save sequence:
   - Write and close complete `config.tmp`.
   - Remove stale `config.bak` if present.
   - Rename current `config.json` to `config.bak`.
   - Rename `config.tmp` to `config.json`.
   - Only report success after the final rename succeeds.
4. On startup, try `config.json` first. If it is missing or invalid, try
   `config.bak`. If both fail, use defaults. Normalize whichever file loads using
   phases 2 and 4.
5. Do not claim rename-over-existing is atomic. The backup is the recovery
   mechanism for filesystems that cannot replace atomically.
6. Enforce the phase 4 profile-count/name limits before allocations for profile
   creation. Reject over-limit commands without appending.
7. Preserve `getSaveData` as a JSON string inside the response for management-app
   compatibility. Document that it currently requires multiple temporary copies;
   do not silently change it to an object.
8. Reduce avoidable copies where this can be done without changing the protocol:
   serialize directly to the config file if the CircuitPython JSON/file APIs
   support it on target; otherwise retain the complete string and explain the
   measured constraint. Do not introduce an unbounded outbound queue.
9. Keep save and large management responses command-driven, never periodic in
   the main loop.

### Waveshare port

Port the same save/backup/recovery and bounded-management behavior, using
Waveshare profile normalization. Keep both config filenames identical so the
management workflows remain consistent.

### Tests

With a fake filesystem, inject failures at temporary write, short write, close,
backup removal, old-config rename, and final rename. Verify `False`, no false
success, and recovery from the newest complete available file.

Simulate power loss after every save step and verify startup loads either the old
or new complete configuration, never a partial JSON document. Test read-only
filesystem behavior explicitly.

Measure `gc.mem_free()` before/after repeated `getSaveData`, profile creation to
the limit, and save on both devices. Force garbage collection between samples and
look for permanent growth rather than expecting identical transient values.
Verify the management app still accepts `getSaveData` unchanged.

### Ship criteria

Every interrupted-save test recovers a complete old or new config, every I/O
failure returns an accurate response, and repeated bounded management operations
show no unbounded retained-memory growth.

---

## Phase 9: Eliminate redundant gamepad report packing

### Goal

Avoid packing an unchanged seven-byte gamepad report every main-loop iteration
without suppressing necessary retries or state updates.

### TuFFpad changes

1. In `hid_gamepad.py`, track whether logical gamepad state has changed since the
   report was packed/sent.
2. `move_joysticks()`, button methods, and `set_hat()` must validate values first
   and avoid packing when the logical values and last successfully sent report
   already agree.
3. Preserve `reset_all()` forced-send behavior.
4. Update `_last_report` only after `send_report()` succeeds. A failed send must
   remain distinguishable from a successful unchanged state so phase 11 can
   retry it.
5. Do not rate-limit analog movement or change axis values in this optimization.

### Waveshare port

Port the identical `hid_gamepad.py` change; this file should remain byte-identical
between repositories.

### Tests

- One hundred unchanged `move_joysticks(x=0, y=0)` calls should perform no new
  packing and no new USB sends after initialization.
- Change each axis, button, and hat value and verify exactly the required report.
- Call `reset_all()` with unchanged state and verify a forced report.
- Inject `OSError` into a send and verify the last-sent marker is not updated and
  a later attempt can resend the same logical state.
- On both devices, verify analog responsiveness and button/hat behavior are
  unchanged.

### Ship criteria

Identical HID reports and input behavior with measurably fewer pack operations;
no optimization-related loss of retries.

---

## Phase 10: Reduce steady-state stick math and allocation pressure

### Goal

Reduce RP2040 CPU and GC pressure while preserving the calibrated outputs from
phase 1.

### TuFFpad changes

1. First add a characterization harness around the existing implementation.
   Record outputs for raw ADC values covering center, just inside/outside the
   deadzone, cardinals, diagonals, limits, and all orientation combinations.
2. Precompute axis mapping scale/offset and the deadzone denominator whenever a
   boundary/deadzone setting changes, not on each sample. Recompute all dependent
   values atomically after valid serial updates.
3. Compare squared magnitude against squared deadzone before calling `sqrt()`.
   Inputs inside the deadzone must return `[0, 0]` without square-root work.
4. For inputs outside the deadzone, preserve the existing radial scaling formula
   and clamp final outputs to `-127` through `127`.
5. Keep the reused two-element result list. Do not introduce tuples, temporary
   dictionaries, or per-sample lookup tables.
6. If integer conversion is considered, compare it against the characterization
   corpus first. Do not accept rounding changes silently; retain floating-point
   outside-deadzone calculations if needed for output compatibility.
7. Measure loop throughput and `gc` behavior on target before and after. Do not
   infer RP2040 allocation rates from CPython.

### Waveshare port

Port identical stick/common/deadzone optimizations and rerun the same corpus and
orientation tests. Keep shared modules byte-identical where possible.

### Tests

- Run the pre-change output corpus against the new implementation. Require exact
  integer outputs except for explicitly reviewed floating-point boundary cases.
- Instrument `stickCommon.magnitude()` or `math.sqrt()` to verify centered and
  inside-deadzone samples skip square root.
- Verify serial boundary/deadzone changes recompute every cached constant and do
  not leave stale values.
- Verify all axis swaps/reversals and keyboard-mode thresholds remain correct.
- Compare sustained loop iterations and GC counts on both devices with a stable
  analog source or repeatable stub on target.

### Ship criteria

No user-visible stick regression, fewer centered-sample math operations, and a
documented on-device CPU/GC improvement. If output compatibility cannot be
maintained, stop at precomputation plus squared-deadzone comparison.

---

## Phase 11: Make runtime USB writes retry safely

### Goal

Prevent temporary HID/CDC unavailability or partial serial writes from crashing
the firmware, losing logical state, or silently truncating management responses.

### TuFFpad changes

1. HID:
   - Catch `OSError` only around runtime `send_report()` boundaries.
   - Do not mark an output as successfully applied until its send succeeds.
   - Keep desired/physical state intact so reconciliation retries the same state.
   - Use a monotonic retry delay of 10 ms after failure to avoid a tight failing
     loop while buttons, serial input, and stick sampling continue.
   - Restore immediate sending after a successful report.
2. Keyboard driver reports are mutated before sending. Track success in
   `ActionManager`, not merely by inspecting the keyboard report buffer. A retry
   may call press/release for a key already present/absent in that local buffer;
   the important requirement is to resend the correct complete report.
3. Serial CDC:
   - Give `SerialHelper` one pending outbound byte buffer plus an offset.
   - `write()` must retain unwritten bytes and pump them until complete.
   - While a response is pending, do not parse another command that would require
     a second response. Continue polling inputs and pumping the pending response.
   - Handle short writes by advancing only the reported byte count.
   - On `OSError`, retain the pending bytes and retry with the same 10 ms delay.
   - Clear the pending buffer only after the final byte is written.
   - Preserve response byte content and CRLF framing exactly.
4. Do not allow read-stick-value responses to bypass the pending-response rule.
5. Do not catch and ignore persistent errors forever without diagnostics. Rate
   limit error logging so a disconnected host cannot flood the console or
   allocate continuously.

### Waveshare port

Port all HID and serial retry behavior. Preserve device handshakes and hardware
integration differences only.

### Tests

- Fake HID failures on press, release, axis, and hat reports; verify continued
  main-loop processing and eventual correct retry without duplicated logical
  actions.
- Verify a failed keyboard send does not mark the key applied even though the
  driver buffer changed.
- Fake serial writes of zero bytes, short writes, and `OSError`; verify complete,
  ordered, uncorrupted responses after recovery.
- Queue a second command during an unfinished response; verify it is not parsed
  until the first response completes.
- Disconnect/suspend and reconnect USB on both devices while moving the stick,
  holding controls, pinging, and requesting save data. Verify recovery without a
  reboot and without stuck keys/buttons.

### Ship criteria

No runtime USB exception escapes the main loop, no logical action is lost or
repeated because of retry, no serial response is truncated, and normal connected
USB behavior/latency remains unchanged.

---

## Final release checklist

After all phases, run a combined regression on both devices:

1. Boot with centered and moved stick; confirm safe deadzone behavior.
2. Load old valid configs and malformed global/profile configs; confirm
   normalization and backup recovery.
3. Exercise every serial command with valid and malformed payloads.
4. Verify discovery handshakes remain device-specific.
5. Test all bindings, duplicate chords, seven-key overflow, pending-key filling,
   and modifier behavior.
6. On TuFFpad, test all matrix keys, D-pad hat directions, mixed hat bindings,
   and RGB fades during heavy input.
7. Switch profiles with ordinary controls held, equivalent bindings held, and
   navigation controls held; verify immediate remap and latching.
8. Confirm final-profile deletion is rejected and inactive edits cause no live
   rebuild.
9. Save/reboot repeatedly and test injected power-loss recovery where practical.
10. Measure idle-loop CPU/GC behavior and confirm no no-change allocations from
    the new action or stick paths.
11. Test USB disconnect/reconnect and serial short-write recovery.
12. Review diffs in both repositories side by side. Shared logic should match;
    only documented hardware/default/handshake differences should remain.
13. Run `git status` and ensure only intentional source/document changes remain.

Do not tag or release until all required on-device checks have actually run on
both products and any management-app compatibility checks pass.
