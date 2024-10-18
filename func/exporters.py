import bpy
from bpy.types import Context
from .. import helper

# =================================================================================================
# Types
# =================================================================================================

def get(scene):
  addon_prefs = bpy.context.preferences.addons['lets_school_helper'].preferences
  return bpy.context.scene.get("lets_school_export_path", addon_prefs.default_export_path)
def set(scene, value):
  scene["lets_school_export_path"] = value
bpy.types.Scene.lets_school_export_path = bpy.props.StringProperty(
  name="Export Path",
  description="The path to export files to",
  subtype="DIR_PATH",
  get=get,
  set=set
)

# =================================================================================================
# Operators
# =================================================================================================

class OT_Reset_Export_Path(bpy.types.Operator):
  bl_idname = "lets_school_helper.reset_export_path"
  bl_label = "Reset Export Path"
  bl_description = "Reset the path to export files to"

  @classmethod
  def poll(cls, context: Context):
    export_path = context.scene.lets_school_export_path or context.preferences.addons["lets_school_helper"].preferences.default_export_path
    return export_path != context.preferences.addons["lets_school_helper"].preferences.default_export_path

  def execute(self, context):
    context.scene.lets_school_export_path = context.preferences.addons["lets_school_helper"].preferences.default_export_path
    return {"FINISHED"}

class OT_Open_Export_Path(bpy.types.Operator):
  bl_idname = "lets_school_helper.open_export_path"
  bl_label = "Open Export Path"
  bl_description = "Open the export path in file explorer"

  def execute(self, context):
    import os
    os.startfile(context.scene.lets_school_export_path)
    return {"FINISHED"}

class OT_Export_Selected_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.export_selected_collection"
  bl_label = "Export Selected"
  bl_description = "Export the selected collection to the specified path"

  @classmethod
  def poll(cls, context: Context):
    has_empty = False
    for obj in context.view_layer.active_layer_collection.collection.objects:
      if obj.name.endswith(".empty"):
        has_empty = True
        break

    if context.view_layer.active_layer_collection.name == "Scene Collection":
      return False

    return has_empty

  def execute(self, context):
    bpy.ops.export_scene.fbx(
      filepath=f"{context.scene.lets_school_export_path}/{context.view_layer.active_layer_collection.name}.fbx",
      use_active_collection=True,
      use_visible=True,
      use_triangles=True,
      axis_forward="-Z",
    )
    self.report({"INFO"}, f"Exported '{context.view_layer.active_layer_collection.name}' to '{context.scene.lets_school_export_path}'")

    return {"FINISHED"}

class OT_Export_All_Collections(bpy.types.Operator):
  bl_idname = "lets_school_helper.export_all_collections"
  bl_label = "Export All"
  bl_description = "Export all collections to the specified path"

  @classmethod
  def poll(cls, context: Context):
    # Check if there any collection besides the Scene Collection
    for collection in context.view_layer.layer_collection.children:
      if collection.name != "Scene Collection":
        return True
    return False

  def execute(self, context):
    exported = 0
    for collection in context.view_layer.layer_collection.children:
      if collection.name != "Scene Collection":
        allow_export = False
        for obj in collection.collection.objects:
          if obj.name == f"{collection.name}.empty":
            allow_export = True
            break

        # Expected to have empty inside, so only export if there are more than 1 object
        if len(collection.collection.objects) <= 1:
          allow_export = False

        if not allow_export:
          continue

        # Check if collection is hidden
        if collection.exclude:
          continue

        bpy.ops.export_scene.fbx(
          filepath=f"{context.scene.lets_school_export_path}/{collection.name}.fbx",
          collection=collection.collection.name,
          use_visible=True,
          use_triangles=True,
          axis_forward="-Z",
        )
        exported += 1

    self.report({"INFO"}, f"Exported {exported} collections to {context.scene.lets_school_export_path}")

    return {"FINISHED"}

class OT_Render_Selected_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.render_selected_collection"
  bl_label = "Render Selected"
  bl_description = "Render the selected collection to the specified path"

  @classmethod
  def poll(cls, context: Context):
    has_empty = False
    for obj in context.view_layer.active_layer_collection.collection.objects:
      if obj.name.endswith(".empty"):
        has_empty = True
        break

    if context.view_layer.active_layer_collection.name == "Scene Collection" or context.view_layer.active_layer_collection.name == "__lets_school_guide__":
      return False

    return has_empty

  def execute(self, context):
    bpy.context.scene.render.filepath = f"{context.scene.lets_school_export_path}/{context.view_layer.active_layer_collection.name}.png"
    active_collection = context.view_layer.active_layer_collection.collection.name

    available_collections = helper.get_available_lsh_collection(self, context)
    collections_data = []
    collections_state = {}
    for collection in available_collections:
      name = collection[0]
      if bpy.data.collections.get(name):
        collections_data.append(bpy.data.collections.get(name))
        collections_state[name] = bpy.data.collections.get(name).hide_render

    if not len(collections_data):
      self.report({"ERROR"}, "No collections to render")
      return {"CANCELLED"}

    for collection in collections_data:
      name = collection.name
      if name == active_collection:
        collection.hide_render = False
      else:
        collection.hide_render = True

    prefs = context.preferences
    is_dirty = prefs.is_dirty
    prev_render_display_type = prefs.view.render_display_type
    prev_film_transparent = bpy.context.scene.render.film_transparent
    def restore_prefs(self,context: bpy.types.Context):
      prefs.view.render_display_type = prev_render_display_type
      bpy.context.scene.render.film_transparent = prev_film_transparent
      prefs.is_dirty = is_dirty

      for collection in collections_data:
        collection.hide_render = collections_state[collection.name]
      bpy.app.handlers.render_complete.remove(restore_prefs)
      return None

    bpy.app.handlers.render_complete.append(restore_prefs)
    bpy.context.scene.render.film_transparent = True
    prefs.view.render_display_type = "WINDOW"
    bpy.ops.render.view_show("INVOKE_DEFAULT")

    bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)

    return {"FINISHED"}

class OT_Render_All_Collections(bpy.types.Operator):
  bl_idname = "lets_school_helper.render_all_collections"
  bl_label = "Render All"
  bl_description = "Render all collections to the specified path"

  @classmethod
  def poll(cls, context: Context):
    # Check if there any collection besides the Scene Collection
    for collection in context.view_layer.layer_collection.children:
      if collection.name != "Scene Collection":
        return True
    return False

  def execute(self, context):
    scene = context.scene
    original_path = scene.render.filepath
    render_collections = helper.get_available_lsh_collection(self, context)

    for collection in render_collections:
      name = collection[0]
      # Check if collection is hidden
      print(name, bpy.data.collections.get(name).hide_render, bpy.data.collections.get(name).hide_viewport)
      if bpy.data.collections.get(name).hide_render or bpy.data.collections.get(name).hide_viewport:
        continue
      for view_layer in scene.view_layers:
        for layer_collection in view_layer.layer_collection.children:
          layer_collection.exclude = (layer_collection.name != name)

      scene.render.filepath = f"{scene.lets_school_export_path}/{name}.png"

      bpy.ops.render.render(write_still=True)

    scene.render.filepath = original_path
    self.report({"INFO"}, f"Rendered {len(render_collections)} collections rendered")

    return {"FINISHED"}

# =================================================================================================
# View
# =================================================================================================

class VIEW3D_PT_Exporters_Panel(bpy.types.Panel):
  bl_space_type = helper.base_data["space"]
  bl_region_type = helper.base_data["region"]
  bl_category = helper.base_data["category"]
  bl_label = "Exporter"


  def draw(self, context):
    layout = self.layout

    # File path input
    col = layout.column()
    col.label(text="Export Path:")

    row = col.row(align=True)
    row.scale_y = 1.25
    row.alignment = "EXPAND"
    row.prop(context.scene, "lets_school_export_path", text="")
    row.operator(OT_Reset_Export_Path.bl_idname, text="", icon="FILE_REFRESH")
    col.operator(OT_Open_Export_Path.bl_idname, text=OT_Open_Export_Path.bl_label, icon="FILE_FOLDER")

    col.separator()

    layout.label(text="Export Collection:")

    # Export button
    col = layout.column()
    col.scale_y = 1.5
    col.operator(OT_Export_Selected_Collection.bl_idname, text=OT_Export_Selected_Collection.bl_label, icon="EXPORT")
    col.operator(OT_Export_All_Collections.bl_idname, text=OT_Export_All_Collections.bl_label, icon="EXPORT")

    col = layout.column()
    col.scale_y = 1.5
    col.operator(OT_Render_Selected_Collection.bl_idname, text=OT_Render_Selected_Collection.bl_label, icon="RENDER_STILL")
    col.operator(OT_Render_All_Collections.bl_idname, text=OT_Render_All_Collections.bl_label, icon="RENDER_STILL")

    col = layout.column(heading="Export Notes")
    col.label(text="Note:", icon="INFO")
    box = col.box()
    helper.create_wrapped_text(context, box, [
      "Empty collections and hidden collections will not be exported / rendered",
      "Hidden objects will also not be exported / rendered",
    ])
