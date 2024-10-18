import textwrap
import bpy

base_data = {
  "space": "VIEW_3D",
  "region": "UI",
  "category": "LSH"
}

def create_wrapped_text(context: bpy.types.Context, element: bpy.types.UILayout, texts: list[str]):
  for area in context.screen.areas:
    if area.type == "VIEW_3D":
      break
  for region in area.regions:
    if region.type == "UI":
      panel_width = region.width
      break

  ui_font_scale = 8 * context.preferences.view.ui_scale
  max_width = int(panel_width // ui_font_scale)
  wrapper = textwrap.TextWrapper(width=max_width)

  col = element.column(align=True)
  col.scale_y = 0.8
  col.alignment = "EXPAND"

  for index,text in enumerate(texts):
    lines = wrapper.wrap(text)
    for line in lines:
      col.label(text=line)
    if index < len(texts) - 1:
      col.separator()

def get_available_lsh_collection(self, context:bpy.types.Context):
  available = []
  for collection in bpy.data.collections:
    if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
      continue
    if any(obj.name == f"{collection.name}.empty" for obj in collection.objects):
      available.append((collection.name, collection.name, ""))

  if len(available) == 0:
    available.append(("NONE", "No collections found", ""))

  return available
def update_lsh_collection(self, context:bpy.types.Context):
  collections = get_available_lsh_collection(self, context)
  selected_collection = context.scene.lets_school_helper_collections or None

  if not selected_collection or len(collections) == 0 or selected_collection not in collections:
    return {"CANCELLED"}

  if not selected_collection in bpy.data.collections:
    return {"CANCELLED"}

  context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(selected_collection)
  # Hide all other axis
  for collection in collections:
    name = collection[0]
    if name == selected_collection:
      continue
    if bpy.data.objects.get(f"{name.lower()}.empty"):
      axis = bpy.data.objects.get(f"{name.lower()}.empty")
      axis.hide_viewport = True

  axis = bpy.data.objects.get(f"{selected_collection.lower()}.empty")
  camera = bpy.data.objects.get("__lets_school_camera__")
  if axis:
    context.view_layer.objects.active = axis
    axis.hide_viewport = False
    if camera:
      camera.constraints["Copy Location"].target = axis

  focus_collection(context, selected_collection)


def focus_collection(context: bpy.types.Context, name:str):
  if context.scene.lets_school_helper_is_focused:
    for collection in bpy.data.collections:
      if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
        continue
      if collection.name == name:
        collection.hide_viewport = False
        collection.hide_render = False
        collection.hide_select = False

      collection.hide_viewport = True
      collection.hide_render = True
      collection.hide_select = True
  else:
    for collection in bpy.data.collections:
      if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
        continue
      collection.hide_viewport = False
      collection.hide_render = False
      collection.hide_select = False
