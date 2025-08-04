# Blender NDOF Object Transformer

With this add-on you can transform (translate and rotate) the active object in the 3D viewport using your NDOF device (like 3DConnexion SpaceMouse).

To enable/disable the NDOF-Object-Transformer mode, use the keyboard shortcut CTRL-SHIFT-M in the 3D viewport.

- For Blender 4.5 and 5.x
- Tested with 3DConnexion SpaceMouse Wireless

This video explains everything: TODO


### Installation

- Download the ndof_object_transformer.py file
- In Blender open Preferences > Add-ons
- Use "Install from Disk" from the little dropdown in the top right corner of the Add-ons panel
- and install the ndof_object_transformer.py file

As long as the add-on is enabled, you can use the keyboard shortcut (CTRL-SHIFT-M by default) to enable/disable moving and rotating the active object in the 3D viewport.

You can change the keyboard shortcut in Blender's Preferences in the "Keymap" section: Search by name for "ndof" and look for "NDOF Object Transform"


### Add-on Preferences

You can set the Translation and Rotation speeds in the Add-On's preferences.

To disable translation or rotation, set the speed to zero.


### Contribute

Ideas that need YOU:
- **Transform all selected objects, not just the active one**
- Detect older Blender versions with different APIs to access the NDOF motion data and make this add-on work with Blender 4.4 and maybe even down to 3.6 (?)
- Turn this into an "extensions" for Blender 4+ instead of a legacy add-on
- Keep it working in the future with newer Blender/API versions

