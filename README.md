# Blender NDOF Object Transformer

With this add-on you can transform (translate and rotate) the active object in the 3D viewport using your NDOF device (like 3DConnexion SpaceMouse).

To enable/disable the NDOF-Object-Transformer mode, use the keyboard shortcut `CTRL-SHIFT-F` in the 3D viewport.

For Blender 4.5 and 5.x

This video explains things: https://youtu.be/BqXvFh1Kp0w

## Installation

This add-on is a Blender Extension.

-   Get the extension ZIP file (`ndof_object_transformer-<version>.zip`), or build it yourself (see below)
-   Drag-and-drop the ZIP file into Blender, or open Preferences > Get Extensions and use "Install from Disk" from the little dropdown in the top right corner

> **Upgrading from v1.1 or older:** Uninstall the old legacy add-on ("NDOF Object Transformer" in Preferences > Add-ons) first, so the two don't conflict.

As long as the add-on is enabled, you can use the keyboard shortcut (`CTRL-SHIFT-F` by default) to enable/disable moving and rotating the active object in the 3D viewport.

You can change the keyboard shortcut in Blender's Preferences in the "Keymap" section: Search by name for "ndof" and look for "NDOF Object Transform"

> **Tip:** In the 3DConnexion driver you can assign CTRL-SHIFT-F as a macro for Blender to one of the buttons on the SpaceMouse!

## Add-on Preferences

▶ Transform Mode:

-   View ... Transformations are relative to the viewport: Push forward = Move away from the viewport (DEFAULT)
-   Global ... Transform on global axes: Push on X axis = Move on world coordinate X axis

**Note:** View Mode transforms all selected objects while Global mode only transforms the active object

▶ Set **Translation/Rotation Speed**

▶ **Invert Translation/Rotation** X/Y/Z

> **Tip:** To disable translation or rotation, set the speed to zero.

### Tested Settings

| Model                           |  Mode  | T Speed | Invert T | R Speed | Invert R |
| ------------------------------- | :----: | ------: | :------: | ------: | :------: |
| 3DConnexion SpaceMouse Wireless |  View  |    0.05 |   X, Z   |    0.03 |    Y     |
| 3DConnexion SpaceMouse Wireless | Global |    0.05 |   X, Z   |    0.03 |    Y     |

> Please submit your tested settings so we can include them in the table above and maybe even make some presets in the future!

## Local Build & Install

-   Build: `blender --command extension build`
-   Install: Drag-and-drop the generated ZIP file into Blender
-   Smoke test (headless): `blender -b --factory-startup --python-exit-code 1 --python tests/smoke_test.py`

## Contribute

Known issues and ideas that need YOU:

-   Detect older Blender versions with different APIs to access the NDOF motion data and make this add-on work with Blender 4.4 and maybe even down to 4.2 (the oldest version supporting extensions)
-   Keep it working in the future with newer Blender/API versions

## Change Log

-   v1.2.0 @ 2026-11-18
    -   Converted to a Blender Extension (`blender_manifest.toml`), replacing the legacy add-on
    -   Each SpaceMouse gesture is now one undo step (Ctrl+Z works as expected)
    -   "NDOF Transform" indicator in the 3D viewport while the mode is on
    -   Global mode: rotation now works for quaternion/axis-angle rotation modes (pose bones!), respects transform locks and auto-keying, skips linked data
    -   View mode follows the 3D viewport under the mouse pointer
    -   Mode stays on in Edit/Sculpt/... (NDOF navigates the view there) instead of switching off
    -   Fixed: toggle needing two presses after opening a file, double-speed motion after a quick off/on, mode stuck "on" after an error

-   v1.1 @ 2025-08-24
    -   View Transform Mode, Invert axes, Pose bone (Contributor: @FuzzyExpress)
    -   New Preferences UI
    -   New Keyboard shortcut CTRL-SHIFT-F (no conflict with other shortcuts)
