# GNU General Public License v3.0 (see LICENSE)
# (C) 2025 ChrisP


bl_info = {
    "name": "NDOF Object Transformer",
    "author": "ChrisP",
    "version": (1, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D",
    "description": "Tansform objects in the 3D viewport using NDOF device",
    "category": "3D View",
}


import bpy


def is_inv(value):
    if value:
        return 1
    else:
        return -1


# Preferences
class NDOFObjectTransformerPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

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



# Modal Operator to transform the active object with the NDOF device
class NDOFObjectTransformer(bpy.types.Operator):
    bl_idname = "view3d.ndof_object_transform"
    bl_label = "NDOF Object Transform"
    bl_options = {'REGISTER', 'UNDO'}

    _is_running = False


    def modal(self, context, event):
        if event.type == 'ESC':
            self.report({'INFO'}, "NDOF Transform cancelled")
            self.cancel(context)
            return {'CANCELLED'}

        if not self._is_running:
            self.report({'INFO'}, "NDOF Transform cancelled: Not running")
            self.cancel(context)
            return {'CANCELLED'}

        match context.mode:
            case 'OBJECT':
                obj = context.active_object
            case 'POSE':
                obj = context.active_pose_bone
            case _:
                self.cancel(context)
                self.report({'INFO'}, "NDOF Transform cancelled: Editor mode not implemented")
                return {'CANCELLED'}


        if event.type == 'NDOF_MOTION' and obj is not None:
            prefs = context.preferences.addons[__name__].preferences
            tx, ty, tz = event.ndof_motion.translation
            rx, ry, rz = event.ndof_motion.rotation

            match prefs.transform_mode:
                case "GLOBAL":
                    # Translate
                    obj.location.x += tx * prefs.translation_speed * is_inv(prefs.invert_translation_x)
                    obj.location.y += tz * prefs.translation_speed * is_inv(prefs.invert_translation_y)
                    obj.location.z += ty * prefs.translation_speed * is_inv(prefs.invert_translation_z)
                    # Rotate (in radians!)
                    obj.rotation_euler.x += rx * prefs.rotation_speed * is_inv(prefs.invert_rotation_x)
                    obj.rotation_euler.y += rz * prefs.rotation_speed * is_inv(prefs.invert_rotation_y)
                    obj.rotation_euler.z += ry * prefs.rotation_speed * is_inv(prefs.invert_rotation_z)

                case "VIEW":
                    # Translate, this is relative to the viewport, but also effects all selected objects
                    bpy.ops.transform.translate(
                        value=(tx * prefs.translation_speed * is_inv(    prefs.invert_translation_x),
                               ty * prefs.translation_speed * is_inv(not prefs.invert_translation_y),
                               tz * prefs.translation_speed * is_inv(    prefs.invert_translation_z)),
                        orient_type='VIEW',
                    )

                    # Three axis rotation does not exist so I will emulate it with a trackball and z-axis rotation
                    bpy.ops.transform.trackball(
                        value=(rx * prefs.rotation_speed * is_inv(prefs.invert_rotation_x),
                               ry * prefs.rotation_speed * is_inv(prefs.invert_rotation_z)),
                    )
                    bpy.ops.transform.rotate(
                        value=(rz * prefs.rotation_speed * is_inv(prefs.invert_rotation_y)),
                        orient_type='VIEW',
                    )

                case _:
                    self.report({'INFO'}, "NDOF Transform cancelled: Transform mode not known!")
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}


    def execute(self, context):
        if NDOFObjectTransformer._is_running:
            self.cancel(context)
            self.report({'INFO'}, "NDOF Transform Off")
            return {'CANCELLED'}
        else:
            context.window_manager.modal_handler_add(self)
            NDOFObjectTransformer._is_running = True
            self.report({'INFO'}, "NDOF Transform On")
            return {'RUNNING_MODAL'}

    def cancel(self, context):
        NDOFObjectTransformer._is_running = False


addon_keymaps = []

def register():
    bpy.utils.register_class(NDOFObjectTransformerPreferences)
    bpy.utils.register_class(NDOFObjectTransformer)

    # Add shortcut: Ctrl+Shift+F in 3D View
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(NDOFObjectTransformer.bl_idname, type='F', value='PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(NDOFObjectTransformer)
    bpy.utils.unregister_class(NDOFObjectTransformerPreferences)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
