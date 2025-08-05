# GNU General Public License v3.0 (see LICENSE)
# (C) 2025 ChrisP


bl_info = {
    "name": "NDOF Object Transformer",
    "author": "ChrisP",
    "version": (1, 0, 1),
    "blender": (4, 5, 0),
    "location": "View3D",
    "description": "Tansform objects in the 3D viewport using NDOF device",
    "category": "3D View",
}


import bpy


# Preferences
class NDOFObjectTransformerPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    translation_speed: bpy.props.FloatProperty(
        name="Translation Speed",
        default=.03,
        min=0,
        max=0.5,
        precision=2,
        step=0.05
    )
    rotation_speed: bpy.props.FloatProperty(
        name="Rotation Speed",
        default=.02,
        min=0,
        max=0.5,
        precision=2,
        step=0.05
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "translation_speed")
        layout.prop(self, "rotation_speed")


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
            self.report({'INFO'}, "NDOF Transform cancelled: not running")
            self.cancel(context)
            return {'CANCELLED'}
        
        match context.mode:
            case 'OBJECT':
                obj = context.active_object
            case 'POSE':
                obj = context.active_pose_bone
            case _:
                self.cancel(context)
                self.report({'INFO'}, "NDOF Transform cancelled: editor mode not implemented")
                return {'CANCELLED'}
        

        if event.type == 'NDOF_MOTION' and obj is not None:
            prefs = context.preferences.addons[__name__].preferences
            tx, ty, tz = event.ndof_motion.translation
            rx, ry, rz = event.ndof_motion.rotation

            # Translate
            obj.location.x += tx * prefs.translation_speed
            obj.location.y += -tz * prefs.translation_speed
            obj.location.z += ty * prefs.translation_speed
            # Rotate (in radians!)
            obj.rotation_euler.x += -rx * prefs.rotation_speed
            obj.rotation_euler.y += rz * prefs.rotation_speed
            obj.rotation_euler.z += -ry * prefs.rotation_speed
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

    # Add shortcut: Ctrl+Shift+M in 3D View
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(NDOFObjectTransformer.bl_idname, type='M', value='PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))

    # Adding extra keymap inplace of Open Recent since Pose Mode CtrlShift+M is for mirror something
    # this keymap will need to be removed by the user
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(NDOFObjectTransformer.bl_idname, type='O', value='PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))
    

def unregister():
    bpy.utils.unregister_class(NDOFObjectTransformer)
    bpy.utils.unregister_class(NDOFObjectTransformerPreferences)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
