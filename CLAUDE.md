# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Blender extension (add-on, id `ndof_object_transformer`) that lets an NDOF device (3DConnexion SpaceMouse) translate/rotate the active object (Object mode) or active pose bone (Pose mode) in the 3D viewport. Targets Blender 4.5 and 5.x; it relies on `event.ndof_motion.translation/.rotation`, which older Blender versions don't expose the same way. Licensed GPL-3.0-or-later.

The entire add-on is `__init__.py`; metadata lives in `blender_manifest.toml` (no legacy `bl_info`).

## Build & install

```bash
blender --command extension build
```

Produces `ndof_object_transformer-<version>.zip` (git-ignored). Install by drag-and-dropping the ZIP into Blender. Also available: `blender --command extension validate`.

Headless smoke test (registration cycles, GLOBAL-mode math incl. rotation modes/locks/pose bones, load reset):

```bash
blender -b --factory-startup --python-exit-code 1 --python tests/smoke_test.py
```

Modal/NDOF behavior itself can only be verified manually in Blender with an NDOF device. Toggle the mode in the 3D viewport with `Ctrl+Shift+F`; `Esc` also turns it off.

## Architecture

- `NDOFObjectTransformerPreferences` (AddonPreferences): transform mode (`VIEW` default / `GLOBAL`), translation/rotation speed, per-axis invert toggles. Read on every event via `context.preferences.addons.get(__package__)` — use `__package__`, never a hardcoded name, because extensions are namespaced (`bl_ext.<repo>.ndof_object_transformer`). A `None` result means the add-on was disabled while the modal handler was alive, so the modal cancels.
- `NDOFObjectTransformer` (modal operator `view3d.ndof_object_transform`): `execute` is a toggle. Running state lives in the module-level `_session` (`_Session`: owning operator, window timer, dirty flags), **not** on the operator, because the Python operator object may already be freed when the mode must stop. `stop_session()` is the single, idempotent way to turn it off (timer, undo flush, indicator).
- Single-instance guard: `modal()` returns `{'CANCELLED'}` unless `_session.op is self` (identity only — don't touch attributes of possibly-freed operators). Stale handlers from a quick off/on remove themselves this way.
- State resets: `@persistent` `load_pre` handler and `cancel()` (Blender calls it when the handler is freed externally) call `stop_session(push_undo=False)`; any exception during a transform stops the session too.
- Undo: no `'UNDO'` bl_option (a modal that never FINISHES pushes nothing). Motion marks the session dirty; the 0.1 s window timer pushes `ed.undo_push` once `UNDO_DELAY` passes without motion → one undo step per gesture. GLOBAL moves are auto-keyed at that point if auto-keying is on (`bpy.ops.transform` in VIEW mode auto-keys itself).
- Only OBJECT (active object) and POSE (active pose bone) modes transform; other modes `PASS_THROUGH` so NDOF navigates the view while the mode stays on.
- Indicator: a `SpaceView3D` POST_PIXEL draw handler shows "NDOF Transform" while a session exists.
- Keymap: `register()` adds `Ctrl+Shift+F` to the addon keyconfig's "3D View" keymap (skipped when no addon keyconfig exists, e.g. background mode); users can rebind it under Keymap > "NDOF Object Transform".

Non-obvious details when changing motion handling:

- NDOF axes are Y-up: in `GLOBAL` mode `ty` drives `location.z`/`rotation_euler.z` and `tz` drives `.y`.
- `is_inv(True)` returns `+1` and `is_inv(False)` returns `-1` — the "invert" defaults were tuned around this, and `VIEW` mode additionally uses `not` on the Y translation flag. Changing these silently changes behavior for existing users' saved preferences.
- `GLOBAL` mode (`apply_global`, pure and headless-testable) writes `location` and the rotation channel matching `rotation_mode` (Euler add; quaternion/axis-angle via a pre-multiplied delta quaternion), skipping locked axes and linked data. `VIEW` mode (`apply_view`) calls `bpy.ops.transform.translate/trackball/rotate` with `orient_type='VIEW'` inside `temp_override` for the 3D view under the mouse (`find_view3d`), so it affects all selected items; 3-axis view rotation is emulated as trackball (X/Y) + view rotate (Z).

## Conventions

- On release: bump `version` in `blender_manifest.toml` and add a dated entry to the Change Log in `README.md`. The README also holds a "Tested Settings" table of per-device preference values.
- Non-runtime files (`README.md`, `CLAUDE.md`, `tests/`, `.github/`, `.claude/`, ZIPs, ...) are excluded from the build via `[build].paths_exclude_pattern`; add new non-runtime files there too.
