from .. import helper
import os
import bpy

# =================================================================================================
# Operators
# =================================================================================================

class OT_Open_Local_Mods(bpy.types.Operator):
  bl_idname = "lets_school_helper.open_local_mods_folder"
  bl_label = "Open Local Mods Folder"
  bl_description = "Open the Local Mods folder"

  @classmethod
  def poll(cls, context):
    return context.preferences.addons["lets_school_helper"].preferences.default_local_folder != ""

  def execute(self, context):
    preferences = context.preferences.addons["lets_school_helper"].preferences
    os.startfile(preferences.default_local_folder)
    return {"FINISHED"}

class OT_Open_Workshop(bpy.types.Operator):
  bl_idname = "lets_school_helper.open_workshop_folder"
  bl_label = "Open Workshop Folder"
  bl_description = "Open the Workshop folder"

  @classmethod
  def poll(cls, context):
    return context.preferences.addons["lets_school_helper"].preferences.default_steam_folder != ""

  def execute(self, context):
    preferences = context.preferences.addons["lets_school_helper"].preferences
    os.startfile(preferences.default_steam_folder + "\\content\\1937500")
    return {"FINISHED"}


# =================================================================================================
# View
# =================================================================================================

class VIEW3D_PT_Mods_Folder_Panel(bpy.types.Panel):
  bl_space_type = helper.base_data["space"]
  bl_region_type = helper.base_data["region"]
  bl_category = helper.base_data["category"]
  bl_label = "Mods Folder"
  bl_options = {"DEFAULT_CLOSED"}

  def draw(self, context):
    layout = self.layout
    column = layout.column()
    column.scale_y = 1.5

    column.operator(OT_Open_Local_Mods.bl_idname, icon="FILE_FOLDER")
    column.operator(OT_Open_Workshop.bl_idname, icon="FILE_FOLDER")

    if context.preferences.addons["lets_school_helper"].preferences.default_local_folder == "" or context.preferences.addons["lets_school_helper"].preferences.default_steam_folder == "":
      col = layout.column()
      col.label(text="Path not set", icon="ERROR")

      box = col.box()
      helper.create_wrapped_text(context, box, [
        "Please set the default folders in the 'Addon Preferences'",
      ])
