# Blender NDOF Object Transformer

With this add-on you can transform (translate and rotate) the active object in the 3D viewport using your NDOF device (like 3DConnexion SpaceMouse).

To enable/disable the NDOF-Object-Transformer mode, use the keyboard shortcut `CTRL-SHIFT-F` in the 3D viewport.

For Blender 4.5 and 5.x

This video explains things: https://youtu.be/BqXvFh1Kp0w

## Installation

-   Download the ndof_object_transformer.py file
-   In Blender open Preferences > Add-ons
-   Use "Install from Disk" from the little dropdown in the top right corner of the Add-ons panel
-   and install the ndof_object_transformer.py file

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
| 3DConnexion SpaceMouse Wireless |  View  |    0.05 |   X, Z   |    0.03 |  (none)  |
| 3DConnexion SpaceMouse Wireless | Global |    0.05 |   X, Z   |    0.03 |    Y     |

> Please submit your tested settings so we can include them in the table above and maybe even make some presets in the future!

## Contribute

Known issues and ideas that need YOU:

-   Detect older Blender versions with different APIs to access the NDOF motion data and make this add-on work with Blender 4.4 and maybe even down to 3.6 (?)
-   Turn this into an "extension" for Blender 4+ instead of a legacy add-on
-   Keep it working in the future with newer Blender/API versions

## Change Log

-   v1.1 @ 2025-08-24
    -   View Transform Mode, Invert axes, Pose bone (Contributor: @FuzzyExpress)
    -   New Preferences UI
    -   New Keyboard shortcut CTRL-SHIFT-F (no conflict with other shortcuts)
