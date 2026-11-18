# GNU General Public License v3.0 (see LICENSE)
# (C) 2025-2026 ChrisP


import time
import traceback

import blf
import bpy
from bpy.app.handlers import persistent
from mathutils import Euler, Quaternion


# Seconds without NDOF motion after which a gesture is committed as one undo step
UNDO_DELAY = 0.3
TIMER_INTERVAL = 0.1


def is_inv(value):
    if value:
        return 1
    else:
        return -1


def is_editable(target):
    """False for linked (non-overridden) data that can't be changed."""
    id_data = target.id_data
    editable = getattr(id_data, "is_editable", None)
    if editable is not None:
        return editable
    return id_data.library is None


def apply_global(target, t, r, prefs):
    """Transform an Object or PoseBone on its own location/rotation channels.

    Axis mapping and invert semantics are kept as in v1.1 so saved preferences behave the same:
    NDOF is Y-up, so NDOF Y drives Z and NDOF Z drives Y.
    """
    tx, ty, tz = t
    rx, ry, rz = r
    ts = prefs.translation_speed
    rs = prefs.rotation_speed

    dloc = (tx * ts * is_inv(prefs.invert_translation_x),
            tz * ts * is_inv(prefs.invert_translation_y),
            ty * ts * is_inv(prefs.invert_translation_z))
    drot = [rx * rs * is_inv(prefs.invert_rotation_x),
            rz * rs * is_inv(prefs.invert_rotation_y),
            ry * rs * is_inv(prefs.invert_rotation_z)]

    for i in range(3):
        if not target.lock_location[i]:
            target.location[i] += dloc[i]

    for i in range(3):
        if target.lock_rotation[i]:
            drot[i] = 0.0
    if not any(drot):
        return

    # Rotation in radians, applied according to the target's rotation mode
    mode = target.rotation_mode
    if mode == 'QUATERNION':
        q = Euler(drot, 'XYZ').to_quaternion() @ target.rotation_quaternion
        q.normalize()
        target.rotation_quaternion = q
    elif mode == 'AXIS_ANGLE':
        angle, ax, ay, az = target.rotation_axis_angle
        q = Euler(drot, 'XYZ').to_quaternion() @ Quaternion((ax, ay, az), angle)
        axis, angle = q.to_axis_angle()
        target.rotation_axis_angle = (angle, axis.x, axis.y, axis.z)
    else:
        for i in range(3):
            target.rotation_euler[i] += drot[i]


def apply_view(t, r, prefs):
    """Transform the selection relative to the viewport in the current (overridden) context."""
    tx, ty, tz = t
    rx, ry, rz = r
    ts = prefs.translation_speed
    rs = prefs.rotation_speed

    bpy.ops.transform.translate(
        value=(tx * ts * is_inv(    prefs.invert_translation_x),
               ty * ts * is_inv(not prefs.invert_translation_y),
               tz * ts * is_inv(    prefs.invert_translation_z)),
        orient_type='VIEW',
    )
    # Three axis rotation does not exist, so emulate it with a trackball and a view-axis rotation
    bpy.ops.transform.trackball(
        value=(rx * rs * is_inv(prefs.invert_rotation_x),
               ry * rs * is_inv(prefs.invert_rotation_z)),
    )
    bpy.ops.transform.rotate(
        value=(rz * rs * is_inv(prefs.invert_rotation_y)),
        orient_type='VIEW',
    )


def find_view3d(window, event):
    """3D view under the mouse pointer, else the first 3D view of the window, else None."""
    if window is None:
        return None
    x, y = event.mouse_x, event.mouse_y
    first = None
    for area in window.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        if area.x <= x < area.x + area.width and area.y <= y < area.y + area.height:
            return area
        if first is None:
            first = area
    return first


def window_region(area):
    for region in area.regions:
        if region.type == 'WINDOW':
            return region
    return None


def autokey(target):
    """Insert keys like Blender's auto-keying would (GLOBAL mode writes properties directly)."""
    target.keyframe_insert("location")
    match target.rotation_mode:
        case 'QUATERNION':
            target.keyframe_insert("rotation_quaternion")
        case 'AXIS_ANGLE':
            target.keyframe_insert("rotation_axis_angle")
        case _:
            target.keyframe_insert("rotation_euler")


# Preferences
class NDOFObjectTransformerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    transform_mode: bpy.props.EnumProperty(
        name="Transform Mode",
        items=[
            ("GLOBAL", "Global", "Transform on global axes. I.E. Push on X axis = Move on world coordinate X axis"),
            ("VIEW", "View", "Transformations are relative to the viewport. I.E. Push forward = Move away from the viewport"),
        ],
        default="VIEW"
    )

    translation_speed: bpy.props.FloatProperty(
        name="Translation Speed",
        default=.05,
        min=0,
        max=0.5,
        precision=2,
        step=0.01
    )
    invert_translation_x: bpy.props.BoolProperty(
        name="Invert Translation X",
        default=True
    )
    invert_translation_y: bpy.props.BoolProperty(
        name="Invert Translation Y",
        default=False
    )
    invert_translation_z: bpy.props.BoolProperty(
        name="Invert Translation Z",
        default=True
    )

    rotation_speed: bpy.props.FloatProperty(
        name="Rotation Speed",
        default=.05,
        min=0,
        max=0.5,
        precision=2,
        step=0.01
    )
    invert_rotation_x: bpy.props.BoolProperty(
        name="Invert Rotation X",
        default=False
    )
    invert_rotation_y: bpy.props.BoolProperty(
        name="Invert Rotation Y",
        default=False
    )
    invert_rotation_z: bpy.props.BoolProperty(
        name="Invert Rotation Z",
        default=False
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "transform_mode")

        layout.prop(self, "translation_speed")
        itrow = layout.row(align=True)
        itrow.label(text="Invert Translation")
        itrow.prop(self, "invert_translation_x", text="X", toggle=True)
        itrow.prop(self, "invert_translation_y", text="Y", toggle=True)
        itrow.prop(self, "invert_translation_z", text="Z", toggle=True)

        layout.prop(self, "rotation_speed")
        irrow = layout.row(align=True)
        irrow.label(text="Invert Rotation")
        irrow.prop(self, "invert_rotation_x", text="X", toggle=True)
        irrow.prop(self, "invert_rotation_y", text="Y", toggle=True)
        irrow.prop(self, "invert_rotation_z", text="Z", toggle=True)


# State of the running transform mode. Kept outside the operator instance because a Python
# operator object may already be freed (e.g. after loading a file) when the mode has to stop.
class _Session:
    def __init__(self, op, timer):
        self.op = op
        self.timer = timer
        self.dirty = False         # moved since the last undo push
        self.global_dirty = False  # moved via GLOBAL mode (needs manual auto-keying)
        self.last_motion = 0.0
        self.warned = set()


_session = None
_draw_handle = None


def _draw_indicator():
    context = bpy.context
    region = context.region
    if _session is None or region is None:
        return
    scale = context.preferences.system.ui_scale
    text = "NDOF Transform"
    font = 0
    blf.size(font, 13 * scale)
    blf.color(font, 1.0, 0.6, 0.15, 1.0)
    width, _ = blf.dimensions(font, text)
    blf.position(font, (region.width - width) / 2, 12 * scale, 0)
    blf.draw(font, text)


def _redraw_view3d():
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _add_indicator():
    global _draw_handle
    if _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_indicator, (), 'WINDOW', 'POST_PIXEL')
    _redraw_view3d()


def _remove_indicator():
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
        _redraw_view3d()


def flush_undo(context, session):
    """Commit the moves since the last push as one undo step (and auto-key GLOBAL moves)."""
    if not session.dirty:
        return
    if session.global_dirty and context.scene.tool_settings.use_keyframe_insert_auto:
        target = context.active_pose_bone if context.mode == 'POSE' else context.active_object
        if target is not None and is_editable(target):
            try:
                autokey(target)
            except Exception:
                traceback.print_exc()
    session.dirty = False
    session.global_dirty = False
    try:
        bpy.ops.ed.undo_push(message="NDOF Transform")
    except Exception:
        traceback.print_exc()


def stop_session(context, push_undo=True):
    """Turn the transform mode off. Safe to call more than once."""
    global _session
    session = _session
    _session = None
    if session is not None:
        if session.timer is not None:
            try:
                context.window_manager.event_timer_remove(session.timer)
            except Exception:
                pass
            session.timer = None
        if push_undo:
            flush_undo(context, session)
    _remove_indicator()


# Modal Operator to transform the active object with the NDOF device
class NDOFObjectTransformer(bpy.types.Operator):
    """Toggle moving and rotating the active object or pose bone with the NDOF device"""
    bl_idname = "view3d.ndof_object_transform"
    bl_label = "NDOF Object Transform"

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        session = _session
        # Only one handler may act; stale handlers (e.g. after a quick off/on) remove themselves
        if session is None or session.op is not self:
            return {'CANCELLED'}

        # Add-on was disabled while this modal handler was still alive
        addon = context.preferences.addons.get(__package__)
        if addon is None:
            stop_session(context, push_undo=False)
            return {'CANCELLED'}

        if event.type == 'ESC' and event.value == 'PRESS':
            stop_session(context)
            self.report({'INFO'}, "NDOF Transform Off")
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if session.dirty and time.monotonic() - session.last_motion > UNDO_DELAY:
                flush_undo(context, session)
            return {'PASS_THROUGH'}

        if event.type != 'NDOF_MOTION':
            return {'PASS_THROUGH'}

        # Unsupported modes (Edit, Sculpt, ...): keep running, let NDOF navigate the view
        match context.mode:
            case 'OBJECT':
                target = context.active_object
            case 'POSE':
                target = context.active_pose_bone
            case _:
                return {'PASS_THROUGH'}
        if target is None:
            return {'PASS_THROUGH'}

        prefs = addon.preferences
        t = tuple(event.ndof_motion.translation)
        r = tuple(event.ndof_motion.rotation)

        try:
            if prefs.transform_mode == 'GLOBAL':
                if not is_editable(target):
                    if "linked" not in session.warned:
                        session.warned.add("linked")
                        self.report({'WARNING'}, "NDOF Transform: active item is linked and not editable")
                    return {'RUNNING_MODAL'}
                apply_global(target, t, r, prefs)
                session.global_dirty = True
            else:
                area = find_view3d(context.window, event)
                region = window_region(area) if area else None
                if region is None:
                    return {'PASS_THROUGH'}
                with context.temp_override(window=context.window, area=area, region=region):
                    apply_view(t, r, prefs)
        except Exception as ex:
            traceback.print_exc()
            stop_session(context)
            self.report({'ERROR'}, f"NDOF Transform stopped: {ex}")
            return {'CANCELLED'}

        session.dirty = True
        session.last_motion = time.monotonic()
        return {'RUNNING_MODAL'}

    def execute(self, context):
        global _session
        if _session is not None:
            stop_session(context)
            self.report({'INFO'}, "NDOF Transform Off")
            return {'CANCELLED'}

        wm = context.window_manager
        timer = wm.event_timer_add(TIMER_INTERVAL, window=context.window)
        wm.modal_handler_add(self)
        _session = _Session(self, timer)
        _add_indicator()
        self.report({'INFO'}, "NDOF Transform On")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # Called by Blender when the handler is removed externally (window closed, file loaded)
        if _session is not None and _session.op is self:
            stop_session(context, push_undo=False)


@persistent
def _on_load_pre(*_args):
    # Loading a file frees the modal handler; make sure the toggle state follows
    stop_session(bpy.context, push_undo=False)


addon_keymaps = []

def register():
    bpy.utils.register_class(NDOFObjectTransformerPreferences)
    bpy.utils.register_class(NDOFObjectTransformer)
    bpy.app.handlers.load_pre.append(_on_load_pre)

    # Add shortcut: Ctrl+Shift+F in 3D View (no addon keyconfig in background mode)
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(NDOFObjectTransformer.bl_idname, type='F', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    stop_session(bpy.context, push_undo=False)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    if _on_load_pre in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_on_load_pre)
    bpy.utils.unregister_class(NDOFObjectTransformer)
    bpy.utils.unregister_class(NDOFObjectTransformerPreferences)
