# Headless smoke test. Run from the repo root:
#   blender -b --factory-startup --python-exit-code 1 --python tests/smoke_test.py
# Covers what can run without a window/NDOF device: registration, GLOBAL-mode math
# (rotation modes, locks, pose bones) and the toggle-state reset on file load.

import importlib.util
import math
import os
import sys
from types import SimpleNamespace

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "ndof_object_transformer", os.path.join(ROOT, "__init__.py"),
    submodule_search_locations=[ROOT])
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

failures = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def close(a, b, eps=1e-6):
    return all(abs(x - y) < eps for x, y in zip(a, b))


def prefs(**kw):
    p = dict(translation_speed=0.1, rotation_speed=0.1,
             invert_translation_x=True, invert_translation_y=False, invert_translation_z=True,
             invert_rotation_x=False, invert_rotation_y=False, invert_rotation_z=False)
    p.update(kw)
    return SimpleNamespace(**p)


def new_object(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    return obj


print("== register / unregister cycles")
for _ in range(2):
    mod.register()
    check(hasattr(bpy.types, "VIEW3D_OT_ndof_object_transform"), "operator registered")
    check(mod._on_load_pre in bpy.app.handlers.load_pre, "load_pre handler registered")
    mod.unregister()
    check(not hasattr(bpy.types, "VIEW3D_OT_ndof_object_transform"), "operator unregistered")
    check(mod._on_load_pre not in bpy.app.handlers.load_pre, "load_pre handler removed")
    check(not mod.addon_keymaps, "keymaps cleared")

print("== GLOBAL: Euler object, axis mapping and invert semantics")
obj = new_object("Euler")
mod.apply_global(obj, (1.0, 2.0, 3.0), (1.0, 2.0, 3.0), prefs())
# tx -> X (+1, inverted), tz -> Y (-1), ty -> Z (+1, inverted); rotation not inverted -> -1
check(close(obj.location, (0.1, -0.3, 0.2)), f"location {tuple(obj.location)}")
check(close(obj.rotation_euler, (-0.1, -0.3, -0.2)), f"rotation_euler {tuple(obj.rotation_euler)}")

print("== GLOBAL: locks")
obj = new_object("Locked")
obj.lock_location = (True, False, True)
obj.lock_rotation = (False, True, True)
mod.apply_global(obj, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), prefs())
check(obj.location[0] == 0 and obj.location[2] == 0 and obj.location[1] != 0, "locked location axes unchanged")
check(obj.rotation_euler[1] == 0 and obj.rotation_euler[2] == 0 and obj.rotation_euler[0] != 0,
      "locked rotation axes unchanged")

print("== GLOBAL: quaternion and axis-angle")
obj = new_object("Quat")
obj.rotation_mode = 'QUATERNION'
mod.apply_global(obj, (0, 0, 0), (1.0, 0, 0), prefs())
q = obj.rotation_quaternion
check(abs(q.magnitude - 1.0) < 1e-5, "quaternion normalized")
check(abs(q.to_euler().x - (-0.1)) < 1e-5, f"quaternion rotated about X ({q.to_euler().x:.4f})")

obj = new_object("AxisAngle")
obj.rotation_mode = 'AXIS_ANGLE'
mod.apply_global(obj, (0, 0, 0), (0, 1.0, 0), prefs())  # NDOF ry -> Z
angle, ax, ay, az = obj.rotation_axis_angle
check(abs(angle - 0.1) < 1e-5 and abs(abs(az) - 1.0) < 1e-5, f"axis-angle about Z ({angle:.4f}, {az:.2f})")

print("== GLOBAL: pose bone (quaternion by default)")
arm = bpy.data.armatures.new("Arm")
rig = bpy.data.objects.new("Rig", arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
bone = arm.edit_bones.new("Bone")
bone.tail = (0, 0, 1)
bpy.ops.object.mode_set(mode='OBJECT')
pb = rig.pose.bones["Bone"]
check(pb.rotation_mode == 'QUATERNION', "pose bone defaults to quaternion")
mod.apply_global(pb, (1.0, 0, 0), (0, 1.0, 0), prefs())
check(abs(pb.location[0] - 0.1) < 1e-6, "pose bone moved")
check(not close(pb.rotation_quaternion, (1, 0, 0, 0)), "pose bone rotated (was a no-op before)")
check(mod.is_editable(pb) and mod.is_editable(obj), "local data is editable")

print("== autokey helper")
mod.autokey(pb)
check(rig.animation_data is not None and rig.animation_data.action is not None,
      "keyframes inserted on pose bone")

print("== load_pre resets toggle state")
mod.register()
mod._session = mod._Session(op=object(), timer=None)
mod._on_load_pre(None)
check(mod._session is None, "session cleared on file load")
mod.unregister()

print()
if failures:
    print(f"SMOKE TEST FAILED: {len(failures)} failure(s)")
    raise SystemExit(1)
print("SMOKE TEST PASSED")
