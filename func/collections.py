import collections
from email.policy import default
import enum
import math
from operator import is_
import textwrap
from bpy.types import Context, Event
from numpy import object_
from requests import get
from .. import helper
import os
import bpy
import random
import bmesh

# =================================================================================================
# Types
# =================================================================================================

bpy.types.Collection.lets_school_helper_type = bpy.props.StringProperty(name="Type", description="The type of collection, used to mark collection as a pack or singular mod", default="MOD")
bpy.types.Scene.lets_school_helper_align_camera = bpy.props.BoolProperty(name="Align Camera", description="Scale the camera to fit to the placement size", default=False)
bpy.types.Scene.lets_school_helper_active_collection_size = bpy.props.StringProperty(name="Size", description="The size of the active collection", default="1x1")

def update_focus_collection(self, context:Context):
  # collections = get_available_collections(self, context)
  active_collection = context.view_layer.active_layer_collection.collection
  if active_collection.name == "Scene Collection" or active_collection.name == "__lets_school_guide__":
    return None

  if self.lets_school_helper_is_focused:
    for collection in bpy.data.collections:
      if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
        continue
      if collection.name == active_collection.name:
        continue
      collection.hide_render = True
      collection.hide_viewport = True
      collection.hide_select = True
    bpy.data.collections[active_collection.name].hide_render = False
    bpy.data.collections[active_collection.name].hide_viewport = False
    bpy.data.collections[active_collection.name].hide_select = False
  else:
    for collection in bpy.data.collections:
      if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
        continue
      collection.hide_render = False
      collection.hide_viewport = False
      collection.hide_select = False
bpy.types.Scene.lets_school_helper_is_focused = bpy.props.BoolProperty(name="Is Focused", description="Focus to current active collection, and hide the rest", default=False, update=update_focus_collection)

def get_available_collections(self, context: Context):
  availableCollections = []
  for index,collection in enumerate(bpy.data.collections):
    if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
      continue

    if any(obj.name.lower().endswith(".empty") for obj in collection.objects):
      availableCollections.append((collection.name, collection.name, ""))

  # if not availableCollections:
  #   availableCollections.append(("NONE", "No Collections", "Select 'Create Collection' to create a new collection", -1))

  return availableCollections

def update_active_collection(self, context: Context):
  collections = get_available_collections(self, context)
  selected_collection = context.scene.lets_school_helper_collections

  if len(collections) == 0:
    return
  if selected_collection == "NONE":
    return
  if not selected_collection:
    self.report({"ERROR"}, "No collection selected")
    return {"CANCELLED"}
  if selected_collection in bpy.data.collections:
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children.get(selected_collection)

    for collection in collections:
      name = collection[0]
      if name == selected_collection:
        continue
      if bpy.data.objects.get(f"{name.lower()}.empty"):
        axis = bpy.data.objects.get(f"{name.lower()}.empty")
        axis.hide_viewport = True

    axis = bpy.data.objects.get(f"{selected_collection.lower()}.empty")
    if axis:
      bpy.context.view_layer.objects.active = axis
      axis.hide_viewport = False

    camera = bpy.data.objects.get("__lets_school_camera__")
    if camera:
      camera.constraints["Copy Location"].target = bpy.data.objects.get(f"{selected_collection.lower()}.empty")

    if bpy.context.scene.lets_school_helper_is_focused:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        if collection.name == selected_collection:
          continue
        collection.hide_render = True
        collection.hide_viewport = True
        collection.hide_select = True
      bpy.data.collections[selected_collection].hide_render = False
      bpy.data.collections[selected_collection].hide_viewport = False
      bpy.data.collections[selected_collection].hide_select = False
    else:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        collection.hide_render = False
        collection.hide_viewport = False
        collection.hide_select = False

bpy.types.Scene.lets_school_helper_collections = bpy.props.EnumProperty(
  name="Active Collections",
  description="List of available collections to choose from",
  items=helper.get_available_lsh_collection,
  update=helper.update_lsh_collection,
)

# =================================================================================================
# Operators
# =================================================================================================

def isActiveCollectionScene() -> bool:
  return bpy.context.view_layer.active_layer_collection.collection.name == "Scene Collection" or bpy.context.view_layer.active_layer_collection.collection.name == "__lets_school_guide__"

def generateRandomName() -> str:
  firstWord = [
    "Aqua", "Astro", "Bio", "Geo", "Hydro",
    "Neo", "Photo", "Techno", "Xeno", "Aero",
    "Cosmo", "Dendro", "Flora", "Glacio", "Helio",
    "Litho", "Pyro", "Terra", "Zoo", "Cyber",
    "Digi", "Inf", "Meta", "Nano", "Tech",
    "Vir", "Web", "WiFi", "Arcane", "Chron",
    "Draco", "Enig", "Glyph", "Magi", "Necro",
    "Omni", "Psy", "Tele", "Anti", "Auto",
    "Bi", "Mono", "Poly", "Syn", "Tri",
    "Ultra", "Mega", "Giga"
  ]
  secondWord = [
    "Star", "Moon", "Sun", "Cloud", "Rainbow",
    "Tree", "Flower", "Mountain", "River", "Ocean",
    "Apple", "Banana", "Orange", "Grape", "Strawberry",
    "Dog", "Cat", "Bird", "Fish", "Rabbit",
    "House", "Car", "Boat", "Plane", "Train",
    "Dragon", "Unicorn", "Fairy", "Wizard", "Goblin",
    "Robot", "Alien", "Spaceship", "Time Machine", "Magic Wand",
    "Diamond", "Gold", "Silver", "Gem", "Jewel",
    "Tool", "Toy", "Game", "Puzzle", "Gift"
  ]

  return f"{firstWord[random.randint(0, len(firstWord) - 1)].lower()}{secondWord[random.randint(0, len(secondWord) - 1)]}"

def sort_collections():
  collections = bpy.context.scene.collection.children
  sorted_collections = sorted(collections, key=lambda c: c.name.lower())

  for collection in sorted_collections:
    ignore_current = False
    if collection.name == "Scene Collection":
      ignore_current = True

    if ignore_current:
      continue

    bpy.context.scene.collection.children.unlink(collection)
    bpy.context.scene.collection.children.link(collection)

class OT_Update_Active_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.update_active_collection"
  bl_label = "Update to Selected"
  bl_description = "Update the active collection to the currently selected object's collection"
  bl_options = {"REGISTER"}

  @classmethod
  def poll(cls, context: Context):
    # Check if not selecting any object
    if not context.view_layer.objects.active:
      return False

    active_collection = context.view_layer.active_layer_collection.collection.name
    active_object = context.view_layer.objects.active
    object_collection = active_object.users_collection[0].name

    return active_collection.lower() != object_collection.lower()

  def execute(self, context: Context):
    active_object = context.view_layer.objects.active
    active_collection = active_object.users_collection[0]
    context.scene.lets_school_helper_collections = active_collection.name

    camera = bpy.data.objects.get("__lets_school_camera__")
    if camera:
      camera.constraints["Copy Location"].target = bpy.data.objects.get(f"{active_collection.name.lower()}.empty")

    return {"FINISHED"}

class OT_Prev_Active_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.prev_active_collection"
  bl_label = "Prev Collection"
  bl_description = "Select the prev collection"
  bl_options = {"REGISTER"}

  @classmethod
  def poll(cls, context: Context):
    collections = get_available_collections(None, context)
    if len(collections) == 0:
      return False
    current_collection = context.scene.lets_school_helper_collections
    find_index = collections.index((current_collection, current_collection, ""))
    return find_index - 1 >= 0

  def execute(self, context: Context):
    collections = get_available_collections(self, context)
    selected_collection = context.scene.lets_school_helper_collections
    index = 0

    for i, collection in enumerate(collections):
      if collection[0] == selected_collection:
        index = i
        break

    if index - 1 < 0:
      index = len(collections) - 1
    else:
      index -= 1

    collection_name = collections[index][0]
    context.scene.lets_school_helper_collections = collection_name
    context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(collection_name)

    if bpy.context.scene.lets_school_helper_is_focused:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        if collection.name == collection_name:
          continue
        collection.hide_render = True
        collection.hide_viewport = True
        collection.hide_select = True
      bpy.data.collections[collection_name].hide_render = False
      bpy.data.collections[collection_name].hide_viewport = False
      bpy.data.collections[collection_name].hide_select = False
    else:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        collection.hide_render = False
        collection.hide_viewport = False
        collection.hide_select = False

    align_camera_to_active_collection(context)
    return {"FINISHED"}

class OT_Next_Active_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.next_active_collection"
  bl_label = "Next Collection"
  bl_description = "Select the next collection"
  bl_options = {"REGISTER"}

  @classmethod
  def poll(cls, context: Context):
    collections = get_available_collections(None, context)
    if len(collections) == 0:
      return False
    current_collection = context.scene.lets_school_helper_collections
    find_index = collections.index((current_collection, current_collection, ""))
    return find_index + 1 < len(collections)

  def execute(self, context: Context):
    collections = get_available_collections(self, context)
    selected_collection = context.scene.lets_school_helper_collections
    index = 0

    for i, collection in enumerate(collections):
      if collection[0] == selected_collection:
        index = i
        break

    if index + 1 >= len(collections):
      index = 0
    else:
      index += 1

    collection_name = collections[index][0]
    context.scene.lets_school_helper_collections = collection_name
    context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(collection_name)

    if bpy.context.scene.lets_school_helper_is_focused:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        if collection.name == collection_name:
          continue
        collection.hide_render = True
        collection.hide_viewport = True
        collection.hide_select = True
      bpy.data.collections[collection_name].hide_render = False
      bpy.data.collections[collection_name].hide_viewport = False
      bpy.data.collections[collection_name].hide_select = False
    else:
      for collection in bpy.data.collections:
        if collection.name == "Scene Collection" or collection.name == "__lets_school_guide__":
          continue
        collection.hide_render = False
        collection.hide_viewport = False
        collection.hide_select = False

    align_camera_to_active_collection(context)
    return {"FINISHED"}

class OT_Sort_Outliner_Collections(bpy.types.Operator):
  bl_idname = "lets_school_helper.sort_outliner_collections"
  bl_label = "Sort Collections"
  bl_description = "Sort collections in the outliner"
  bl_options = {"REGISTER", "UNDO"}

  def execute(self, context: Context):
    collections = bpy.data.collections
    sort_collections()
    self.report({"INFO"}, f"{len(collections) - 1} collections sorted")
    return {"FINISHED"}

class OT_Create_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.create_collection"
  bl_label = "Create Collection"
  bl_description = "Create a collection to organize objects for your asset"
  bl_options = {"REGISTER", "UNDO"}

  mod_name: bpy.props.StringProperty(name="Mod name", description="The name of the collection", options={"SKIP_SAVE"})

  def invoke(self, context: Context, event: Event):
    return context.window_manager.invoke_props_dialog(self)

  def execute(self, context: Context):
    if not self.mod_name:
      self.report({"ERROR"}, "Name must not be empty")
      return {"CANCELLED"}

    safe_name = self.mod_name.replace(" ", "_").lower()

    # Check if the collection already exists
    if bpy.data.collections.get(safe_name):
      self.report({"ERROR"}, f"Collection '{safe_name}' already exists")
      return {"CANCELLED"}

    collection = bpy.data.collections.new(safe_name)
    context.scene.collection.children.link(collection)
    context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(collection.name)

    bpy.ops.object.empty_add(type="CUBE", location=(0, 0, 1.25))
    bpy.ops.transform.resize(value=(0.5, 0.5, 1.25))
    bpy.context.object.hide_select = True
    bpy.context.object.name = f"{safe_name}.empty"
    bpy.context.object.hide_viewport = True

    # Create collection exporter to FBX
    bpy.ops.collection.exporter_add(name="IO_FH_fbx")

    # Get camera helper
    camera = bpy.data.objects.get("__lets_school_camera__")
    if camera:
      camera.constraints["Copy Location"].target = bpy.data.objects.get(f"{safe_name}.empty")


    # Sort collections
    sort_collections()
    bpy.context.scene.lets_school_helper_collections = collection.name

    return {"FINISHED"}

class OT_Remove_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.remove_collection"
  bl_label = "Remove Collection"
  bl_description = "Remove the active collection"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context: Context):
    return isActiveCollectionScene() == False

  def invoke(self, context: Context, event: Event):
    return context.window_manager.invoke_confirm(self, event, title="Remove Collection", message="This will remove the active collection and all its objects. Are you sure?")

  def execute(self, context: Context):
    active_collection = context.view_layer.active_layer_collection.collection

    # Empty object
    safe_name = active_collection.name.replace(" ", "_").lower()
    axis = bpy.data.objects.get(f"{safe_name}.empty")
    if axis:
      bpy.data.objects.remove(axis)

    # Select collection and all objects in it
    bpy.ops.object.select_all(action='DESELECT')
    for obj in active_collection.objects:
      obj.select_set(True)

    # Remove selected objects
    bpy.ops.object.delete()

    # Remove collection
    bpy.data.collections.remove(active_collection)

    # Set active collection to selected collection
    available_collections = get_available_collections(self, context)
    if len(available_collections) > 0:
      context.scene.lets_school_helper_collections = available_collections[0][0]
      context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(available_collections[0][0])


    return {"FINISHED"}

class OT_Rename_Collection(bpy.types.Operator):
  bl_idname = "lets_school_helper.rename_collection"
  bl_label = "Rename Collection"
  bl_description = "Rename the active collection"
  bl_options = {"REGISTER", "UNDO"}

  name: bpy.props.StringProperty(name="Mod name")

  @classmethod
  def poll(cls, context: Context):
    return isActiveCollectionScene() == False

  def invoke(self, context: Context, event: Event):
    return context.window_manager.invoke_props_dialog(self, title="Rename Collection")

  def execute(self, context: Context):
    active_collection = context.view_layer.active_layer_collection.collection
    old_name = active_collection.name

    old_safe_name = old_name.replace(" ", "_").lower()
    safe_name = self.name.replace(" ", "_").lower()

    # axis = bpy.data.objects.get(f"{old_safe_name}.empty")
    # if axis:
    #   axis.name = f"{safe_name}.empty"

    active_collection.name = self.name

    # Get all objects in the collection
    for obj in active_collection.objects:
      if obj.name.find(old_name) != -1:
        obj.name = obj.name.replace(old_name, self.name)
      else:
        obj.name = f"{self.name}.{obj.name}"

    # Get camera helper
    camera = bpy.data.objects.get("__lets_school_camera__")
    if camera:
      camera.constraints["Copy Location"].target = bpy.data.objects.get(f"{safe_name}.empty")

    # Sort collections
    sort_collections()

    return {"FINISHED"}

class OT_Create_Variation(bpy.types.Operator):
  bl_idname = "lets_school_helper.create_variation"
  bl_label = "Create Variation"
  bl_description = "Create a new variation of the active collection"
  bl_options = {"REGISTER", "UNDO"}

  var_name: bpy.props.StringProperty(name="Variation name", description="The name of the collection", options={"SKIP_SAVE"})

  def invoke(self, context: Context, event: Event):
    return context.window_manager.invoke_props_dialog(self)

  def execute(self, context: Context):
    if not self.var_name:
      self.report({"ERROR"}, "Name must not be empty")
      return {"CANCELLED"}

    active_collection = context.view_layer.active_layer_collection.collection
    new_collection = bpy.data.collections.new(f"{active_collection.name}_var_{self.var_name}")
    bpy.context.scene.collection.children.link(new_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children.get(new_collection.name)

    for object in active_collection.objects:
      data = object.data.copy() if object.data else None
      new_object = object.copy()
      if data:
        new_object.data = data
      if object.name.find(active_collection.name) != -1:
        new_object.name = object.name.replace(active_collection.name, new_collection.name)
      else:
        new_object.name = f"{new_collection.name}.{object.name}"
      new_collection.objects.link(new_object)

    sort_collections()
    bpy.context.scene.lets_school_helper_collections = new_collection.name
    bpy.ops.collection.exporter_add(name="IO_FH_fbx")

    return {"FINISHED"}

class OT_New_Object(bpy.types.Operator):
  bl_idname = "lets_school_helper.new_object"
  bl_label = "New Tracked Object"
  bl_description = "Create a new tracked blank object in the active collection"
  bl_options = {"REGISTER", "UNDO"}

  obj_name: bpy.props.StringProperty(name="Part name", description="The name of the object part", options={"SKIP_SAVE"})

  def invoke(self, context: Context, event: Event):
    return context.window_manager.invoke_props_dialog(self)

  def execute(self, context: Context):
    if not self.obj_name:
      self.report({"ERROR"}, "Name must not be empty")
      return {"CANCELLED"}

    active_collection = context.view_layer.active_layer_collection.collection
    location = (0, 0, 0)

    safe_name = active_collection.name.replace(" ", "_").lower()
    axis = bpy.data.objects.get(f"{safe_name}.empty")
    if not axis:
      self.report({"ERROR"}, "Axis empty object not found", icon="ERROR")
      return {"CANCELLED"}

    bpy.ops.mesh.primitive_cube_add(location=location)

    bpy.context.object.name = f"{safe_name}.{self.obj_name}"

    bpy.ops.view3d.snap_cursor_to_selected()

    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = axis
    bpy.context.object.constraints["Child Of"].use_scale_x = False
    bpy.context.object.constraints["Child Of"].use_scale_y = False
    bpy.context.object.constraints["Child Of"].use_scale_z = False

    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='VERT')

    self.report({"INFO"}, f"Object '{bpy.context.object.name}' created")

    return {"FINISHED"}

class OT_Track_Object(bpy.types.Operator):
  bl_idname = "lets_school_helper.track_object"
  bl_label = "Add Object Constraint"
  bl_description = "Track the selected object to the active collection"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context: Context):
    return context.view_layer.objects.active is not None

  def execute(self, context: Context):
    active_object = context.view_layer.objects.active
    object_collection = active_object.users_collection[0]

    safe_name = object_collection.name.replace(" ", "_").lower()
    axis = bpy.data.objects.get(f"{safe_name}.empty")
    if not axis:
      self.report({"ERROR"}, "Axis empty object not found", icon="ERROR")
      return {"CANCELLED"}

    # Add object constraints of Copy Location, and set the target to axis empty
    # bpy.ops.object.constraint_add(type='COPY_LOCATION')
    # bpy.context.object.constraints["Copy Location"].use_offset = True
    # bpy.context.object.constraints["Copy Location"].target = axis

    # Add child of constraint
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = axis
    bpy.context.object.constraints["Child Of"].use_scale_x = False
    bpy.context.object.constraints["Child Of"].use_scale_y = False
    bpy.context.object.constraints["Child Of"].use_scale_z = False

    return {"FINISHED"}

class OT_Guide_Init(bpy.types.Operator):
  bl_idname = "lets_school_helper.guide_init"
  bl_label = "Initialize Guide Object"
  bl_description = "Create a wireframe guide object"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context: Context):
    return context.scene.collection.get("__lets_school_guide__") is None

  def execute(self, context: Context):
    # Create guide collection
    if bpy.data.collections.get("__lets_school_guide__"):
      self.report({"ERROR"}, f"Guide collection '__lets_school_guide__' already exists")
      return {"CANCELLED"}

    current_active_object = context.view_layer.objects.active

    collection = bpy.data.collections.new("__lets_school_guide__")
    context.scene.collection.children.link(collection)
    prev_active_collection = context.view_layer.active_layer_collection
    context.view_layer.active_layer_collection = context.view_layer.layer_collection.children.get(collection.name)

    # Reset 3D cursor
    bpy.ops.view3d.snap_cursor_to_center()

    # Create guide object
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    bpy.context.object.name = "__guide.wall__"
    bpy.ops.transform.resize(value=(6, 0.2, 1.75))
    bpy.ops.transform.translate(value=(-2.5, -0.5, 0.875))
    bpy.context.object.display_type = "BOUNDS"
    bpy.context.object.show_name = True
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    bpy.context.object.visible_camera = False
    bpy.context.object.visible_shadow = False
    # bpy.context.object.hide_viewport = True

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    bpy.context.object.name = "__guide.upper_wall__"
    bpy.ops.transform.resize(value=(6, 0.2, 0.8))
    bpy.ops.transform.translate(value=(-2.5, -0.5, 1.75 + 0.4))
    bpy.context.object.display_type = "BOUNDS"
    bpy.context.object.show_name = True
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    bpy.context.object.visible_camera = False
    bpy.context.object.visible_shadow = False
    # bpy.context.object.hide_viewport = True

    # Floor
    base_height = 0
    floor_height = base_height + 0.025
    floor_vertices = [
      (0.5, 0, base_height),
      (0.5, -0.4, base_height),
      (0.47, -0.47, base_height),
      (0.4, -0.5, base_height),
      (0, -0.5, base_height),

      (0.45, 0, floor_height),
      (0.45, -0.35, floor_height),
      (0.42, -0.42, floor_height),
      (0.35, -0.45, floor_height),
      (0, -0.45, floor_height),

      (0.35, 0, floor_height),
      (0.35, -0.35, floor_height),
      (0, -0.35, floor_height),

      (0, 0, floor_height),
    ]
    floor_faces = [
      (0, 1, 6, 5), (1,2,7,6), (2,3,8,7), (3,4,9,8),
      (5,6,11,10), (6,7,8,11), (8,9,12,11),
      (10,11,12,13)
    ]

    mesh = bpy.data.meshes.new("__guide.floor__")
    obj = bpy.data.objects.new("__guide.floor__", mesh)
    context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(floor_vertices, [], floor_faces)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    bm.edges[3].select = True
    bm.edges[6].select = True
    bm.edges[9].select = True
    bm.edges[12].select = True
    for edge in bm.edges:
      if edge.select:
        edge.smooth = False
    bmesh.update_edit_mesh(mesh)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    bpy.ops.object.modifier_add(type="MIRROR")
    bpy.context.object.modifiers['Mirror'].use_axis[0] = True
    bpy.context.object.modifiers['Mirror'].use_axis[1] = True
    bpy.ops.object.modifier_apply(modifier="Mirror")

    bpy.ops.object.modifier_add(type="ARRAY")
    bpy.context.object.modifiers["Array"].use_relative_offset = False
    bpy.context.object.modifiers["Array"].use_constant_offset = True
    bpy.context.object.modifiers["Array"].constant_offset_displace[0] = -1
    bpy.context.object.modifiers["Array"].count = 6

    bpy.ops.object.modifier_add(type="ARRAY")
    bpy.context.object.modifiers["Array.001"].use_relative_offset = False
    bpy.context.object.modifiers["Array.001"].use_constant_offset = True
    bpy.context.object.modifiers["Array.001"].constant_offset_displace[0] = 0
    bpy.context.object.modifiers["Array.001"].constant_offset_displace[1] = 1
    bpy.context.object.modifiers["Array.001"].count = 4
    bpy.ops.object.modifier_apply(modifier="Array")
    bpy.context.object.show_name = True
    bpy.context.object.visible_shadow = False
    # bpy.context.object.hide_viewport = True


    bpy.data.collections["__lets_school_guide__"].hide_render = True
    bpy.data.collections["__lets_school_guide__"].hide_select = True
    context.view_layer.active_layer_collection = prev_active_collection
    context.view_layer.objects.active = current_active_object
    return {"FINISHED"}

class OT_Guide_Toggle(bpy.types.Operator):
  bl_idname = "lets_school_helper.guide_toggle"
  bl_label = "Toggle Guide Object"
  bl_description = "Toggle the visibility"
  bl_options = {"REGISTER", "UNDO"}

  type: bpy.props.StringProperty(name="Type", description="The type of guide object to toggle")

  @classmethod
  def poll(cls, context: Context):
    guide_collection = bpy.data.collections.get("__lets_school_guide__")
    if not guide_collection:
      return False

    view = []
    for object in guide_collection.objects:
      view.append(object.hide_viewport)



    return True

  def execute(self, context: Context):
    if not self.type:
      self.report({"ERROR"}, "Guide type not set")
      return {"CANCELLED"}

    guide_collection = bpy.data.collections.get("__lets_school_guide__")
    if not guide_collection:
      self.report({"ERROR"}, "Guide collection not found")
      return {"CANCELLED"}

    if self.type == "show_all":
      for object in guide_collection.objects:
        object.hide_viewport = False
      return {"FINISHED"}
    if self.type == "hide_all":
      for object in guide_collection.objects:
        object.hide_viewport = True
      return {"FINISHED"}

    for object in guide_collection.objects:
      if object.name == f"__guide.{self.type}__":
        object.hide_viewport = not object.hide_viewport
        break

    return {"FINISHED"}

def align_camera_to_active_collection(context: Context):
    active_collection = context.view_layer.active_layer_collection.collection
    axis = active_collection.objects.get(f"{active_collection.name.lower()}.empty")
    if not axis:
      return {"CANCELLED"}

    if bpy.context.scene.render.resolution_x / bpy.context.scene.render.resolution_y != 1/1:
      bpy.context.scene.render.resolution_x = 1080
      bpy.context.scene.render.resolution_y = 1080

    width = axis.scale[0] / 0.5
    height = axis.scale[1] / 0.5
    camera = bpy.data.objects.get("__lets_school_camera__") or None
    if not camera:
      print("Creating camera")
      bpy.ops.object.camera_add(location=(-3, 3, 3))
      bpy.context.object.rotation_euler = (0.955323, 0, -2.35619)
      bpy.context.object.name = "__lets_school_camera__"
      bpy.context.object.data.type = "ORTHO"
      bpy.context.object.data.ortho_scale = 3
      bpy.ops.object.constraint_add(type="COPY_LOCATION")
      context.view_layer.objects.active = bpy.context.object
      bpy.ops.object.move_to_collection(collection_index=0)
    else:
      context.view_layer.objects.active = camera

    bpy.context.object.constraints["Copy Location"].target = axis
    bpy.context.object.constraints["Copy Location"].use_offset = True
    bpy.ops.view3d.object_as_camera()
    bpy.context.object.hide_viewport = True

    x_pos = (int(width) - 1) * 0.5 * -1
    y_pos = (int(height) - 1) * 0.5 * 1
    axis.scale = (float(width)/2, float(height)/2, 1.25)
    axis.location = (x_pos, y_pos, 1.25)

    if context.scene.lets_school_helper_align_camera:
      cam_scale_base = 3
      cam_offset_x = 0.45
      cam_offset_y = 0.75
      cam_shift_y = 0.025

      bpy.context.object.data.ortho_scale = cam_scale_base + ((int(width) - 1) * cam_offset_x) + ((int(height) - 1) * cam_offset_y)
      bpy.context.object.data.shift_y = (int(height) - 1) * cam_shift_y
class OT_Resize_Placement(bpy.types.Operator):
  bl_idname = "lets_school_helper.resize_placement"
  bl_label = "Resize Placement"
  bl_description = "Resize the placement helper to fit the furniture size"
  bl_options = {"REGISTER", "UNDO"}

  size: bpy.props.StringProperty(name="Size", description="The size of the placement helper (wxh)", default="1x1")

  def execute(self, context: Context):
    if bpy.context.scene.render.resolution_x / bpy.context.scene.render.resolution_y != 1/1:
      bpy.context.scene.render.resolution_x = 1080
      bpy.context.scene.render.resolution_y = 1080

    current_active_object = context.view_layer.objects.active

    [width, height] = self.size.split("x")
    context.scene.lets_school_helper_active_collection_size = self.size
    active_collection = context.view_layer.active_layer_collection.collection
    axis = active_collection.objects.get(f"{active_collection.name.lower()}.empty")
    if not axis:
      self.report({"ERROR"}, "Axis empty object not found", icon="ERROR")
      return {"CANCELLED"}

    camera = bpy.data.objects.get("__lets_school_camera__") or None
    if not camera:
      print("Creating camera")
      bpy.ops.object.camera_add(location=(-3, 3, 3))
      bpy.context.object.rotation_euler = (0.955323, 0, -2.35619)
      bpy.context.object.name = "__lets_school_camera__"
      bpy.context.object.data.type = "ORTHO"
      bpy.context.object.data.ortho_scale = 3
      bpy.ops.object.constraint_add(type="COPY_LOCATION")
      bpy.context.object.constraints["Copy Location"].target = axis
      bpy.context.object.constraints["Copy Location"].use_offset = True
      bpy.ops.view3d.object_as_camera()
      bpy.ops.object.move_to_collection(collection_index=0)
      context.view_layer.objects.active = bpy.context.object
    else:
      context.view_layer.objects.active = camera

    camera = context.view_layer.objects.active

    x_pos = (int(width) - 1) * 0.5 * -1
    y_pos = (int(height) - 1) * 0.5 * 1
    axis.scale = (float(width)/2, float(height)/2, 1.25)
    axis.location = (x_pos, y_pos, 1.25)

    if context.scene.lets_school_helper_align_camera and camera:
      cam_scale_base = 3
      cam_offset_x = 0.45
      cam_offset_y = 0.75
      cam_shift_y = 0.025

      bpy.context.object.data.ortho_scale = cam_scale_base + ((int(width) - 1) * cam_offset_x) + ((int(height) - 1) * cam_offset_y)
      bpy.context.object.data.shift_y = (int(height) - 1) * cam_shift_y

    bpy.context.object.hide_viewport = True
    bpy.context.view_layer.objects.active = current_active_object
    return {"FINISHED"}

class OT_Render_Active(bpy.types.Operator):
  bl_idname = "lets_school_helper.render_active"
  bl_label = "Render Active Collection"
  bl_description = "Render the active collection"
  bl_options = {"REGISTER"}

  def execute(self, context: Context):
    current_active_collection = context.view_layer.active_layer_collection.collection.name

    if current_active_collection == "Scene Collection" or current_active_collection == "__lets_school_guide__":
      self.report({"ERROR"}, "Cannot render Scene or Guide collection")
      return {"CANCELLED"}

    available_collections = get_available_collections(None, context)
    collections_data = []
    collection_state = {}
    for collection in available_collections:
      if bpy.data.collections.get(collection[0]):
        collections_data.append(bpy.data.collections.get(collection[0]))
        collection_state[collection[0]] = bpy.data.collections.get(collection[0]).hide_render

    if not len(collections_data):
      self.report({"ERROR"}, "No collections to render")
      return {"CANCELLED"}

    for collection in collections_data:
      name = collection.name
      if name == current_active_collection:
        collection.hide_render = False
      else:
        collection.hide_render = True

    prefs = bpy.context.preferences
    prev_is_dirty = prefs.is_dirty
    prev_render_display_type = prefs.view.render_display_type
    prev_film_transparent = bpy.context.scene.render.film_transparent

    context.scene.render.film_transparent = True
    prefs.view.render_display_type = 'WINDOW'
    bpy.ops.render.view_show("INVOKE_DEFAULT")

    def restore_settings(self, context):
      # Restore
      prefs.view.render_display_type = prev_render_display_type
      bpy.context.scene.render.film_transparent = prev_film_transparent
      prefs.is_dirty = prev_is_dirty

      for collection in collections_data:
        collection.hide_render = collection_state[collection.name]


      bpy.app.handlers.render_complete.remove(restore_settings)
      return None

    bpy.app.handlers.render_complete.append(restore_settings)
    bpy.ops.render.render("INVOKE_DEFAULT")

    return {"FINISHED"}
# =================================================================================================
# View
# =================================================================================================

class VIEW3D_PT_Collections_Panel(bpy.types.Panel):
  bl_space_type = helper.base_data["space"]
  bl_region_type = helper.base_data["region"]
  bl_category = helper.base_data["category"]
  bl_label = "Collections"
  bl_idname = "VIEW3D_PT_Collections_Panel"

  def draw(self, context):
    layout = self.layout
    active_collection = context.view_layer.active_layer_collection.collection
    selected_collection = context.scene.lets_school_helper_collections
    # Check if the name has "_var_"
    is_var_collection = selected_collection.lower().find("_var_") != -1

    active_object = context.view_layer.objects.active
    object_collection = None
    is_object_in_active_collection = False
    is_allowed_to_update = False
    if active_object and len(active_object.users_collection) > 0:
      object_collection = active_object.users_collection[0].name
      is_object_in_active_collection = active_collection.name == object_collection
      is_allowed_to_update = not is_object_in_active_collection and (
        object_collection != "Scene Collection" and object_collection != "__lets_school_guide__"
      )


    col = layout.column()
    # if len(context.scene.lets_school_helper_collections) == 0:
    #   col.label(text="No LSH collections available", icon="ERROR")
    # else:
    col.label(text="Active Collection:")
    select = col.row(align=True)
    select.scale_y = 1.25
    select.alignment = "EXPAND"
    select.prop(context.scene, "lets_school_helper_collections", text="", icon="OUTLINER_COLLECTION")
    select.separator()
    select.operator(OT_Prev_Active_Collection.bl_idname, text="", icon="TRIA_LEFT")
    select.operator(OT_Next_Active_Collection.bl_idname, text="", icon="TRIA_RIGHT")
    if helper.get_available_lsh_collection(self,context)[0][0] != "NONE":
      col.prop(context.scene, "lets_school_helper_is_focused", text="Focus to active collection", icon="VIEWZOOM", toggle=True)

    if context.mode == "OBJECT":
      if is_allowed_to_update:
        object_collection = active_object.users_collection[0].name

        btn = col.column()
        btn.scale_y = 1.25
        btn.operator(OT_Update_Active_Collection.bl_idname, text=f"Set to '{object_collection}'", icon="OUTLINER_COLLECTION", depress=not is_object_in_active_collection)

      layout.separator()

      col = layout.column()
      btn = col.column()
      btn.scale_y = 1.25
      btn.operator(OT_Create_Collection.bl_idname, text=OT_Create_Collection.bl_label, icon="ADD")
      btn.operator(OT_Remove_Collection.bl_idname, text=OT_Remove_Collection.bl_label, icon="TRASH")
      btn.operator(OT_Rename_Collection.bl_idname, text=OT_Rename_Collection.bl_label, icon="GREASEPENCIL").name = active_collection.name
      if not is_var_collection:
        btn.operator(OT_Create_Variation.bl_idname, text="Create variation", icon="DUPLICATE")

      layout.separator()

      if(isActiveCollectionScene() == False):
        col = layout.column()
        btn = col.column()
        btn.scale_y = 1.25
        btn.operator(OT_New_Object.bl_idname, text=OT_New_Object.bl_label, icon="MESH_CUBE")

        if active_object is not None:
          active_object_constraint = active_object.constraints.get("Child Of")
          active_object_constraint_target = active_object_constraint.target if active_object_constraint else None
          active_object_collection = active_object.users_collection[0]

          active_object_is_mesh = active_object.type == "MESH"

          is_object_tracked = active_object_constraint and active_object_constraint_target == active_object_collection.objects.get(f"{active_object_collection.name.lower()}.empty")
          if not is_object_tracked and active_object_is_mesh:
            btn.operator(OT_Track_Object.bl_idname, text=OT_Track_Object.bl_label, icon="CON_LOCLIKE")


class VIEW3D_PT_Guide_Panel(bpy.types.Panel):
  bl_space_type = helper.base_data["space"]
  bl_region_type = helper.base_data["region"]
  bl_parent_id = "VIEW3D_PT_Collections_Panel"
  bl_label = "Guides"

  def draw(self, context):
    layout = self.layout
    is_guide_initialized = bpy.data.collections.get("__lets_school_guide__") is not None

    col = layout.column()
    btn = col.column()

    if(is_guide_initialized == False):
      btn.operator(OT_Guide_Init.bl_idname, text=OT_Guide_Init.bl_label, icon="COLLECTION_NEW")
    else:
      col = col.column(align=True)

      row = col.row(align=True)
      row.operator(OT_Guide_Toggle.bl_idname, text="Show All", icon="HIDE_OFF").type = "show_all"
      row.operator(OT_Guide_Toggle.bl_idname, text="Hide All", icon="HIDE_ON").type = "hide_all"

      col.separator()

      guide_collection = bpy.data.collections.get("__lets_school_guide__")
      items = [
        (OT_Guide_Toggle.bl_idname, "Wall", "wall", guide_collection.objects.get("__guide.wall__".lower()) is not None and guide_collection.objects.get("__guide.wall__".lower()).hide_viewport == False),
        (OT_Guide_Toggle.bl_idname, "Upper Wall", "upper_wall", guide_collection.objects.get("__guide.upper_wall__".lower()) is not None and guide_collection.objects.get("__guide.upper_wall__".lower()).hide_viewport == False),
        (OT_Guide_Toggle.bl_idname, "Floor", "floor", guide_collection.objects.get("__guide.floor__".lower()) is not None and guide_collection.objects.get("__guide.floor__".lower()).hide_viewport == False),
        # (OT_Guide_Toggle.bl_idname, "Chair", "chair", guide_collection.objects.get("__guide.chair__".lower()) is not None and guide_collection.objects.get("__guide.chair__".lower()).hide_viewport == False),
        # (OT_Guide_Toggle.bl_idname, "Desk", "desk", guide_collection.objects.get("__guide.desk__".lower()) is not None and guide_collection.objects.get("__guide.desk__".lower()).hide_viewport == False),
      ]
      for item in items:
        col.operator(item[0], text=item[1], depress=item[3], icon="HIDE_OFF" if item[3] else "HIDE_ON").type = item[2]

class VIEW3D_PT_Placement_Panel(bpy.types.Panel):
  bl_space_type = helper.base_data["space"]
  bl_region_type = helper.base_data["region"]
  bl_parent_id = "VIEW3D_PT_Collections_Panel"
  bl_label = "Placement and Render Helper"

  @classmethod
  def poll(cls, context: Context) -> bool:
    return isActiveCollectionScene() == False

  def draw(self, context):
    layout = self.layout
    active_collection = bpy.context.view_layer.active_layer_collection.collection

    col = layout.column()

    if isActiveCollectionScene() == False:
      active_empty = active_collection.objects.get(f"{active_collection.name}.empty")
      active_name = active_collection.name
      if not active_empty:
        col.label(text="Unknown collection")
        col.label(text="Please use 'Create Collection' button")
        return

      # Get the X and Y scale of empty
      scale_x = active_empty.scale[0]
      scale_y = active_empty.scale[1]
      size_x = int(scale_x / 0.5)
      size_y = int(scale_y / 0.5)

      col.label(text=f"Current Size: {size_x}x{size_y}")

      # btn = col.column()
      # btn.scale_y = 1.5
      # btn.operator(OT_Render_Active.bl_idname, text=f"Render '{active_name}'", icon="RENDER_STILL")

      col = layout.column(align=True)
      col.alignment = "EXPAND"
      # col.operator(OT_Resize_Placement.bl_idname, text="Align Camera", icon="VIEW_CAMERA_UNSELECTED", depress=False)
      col.prop(context.scene, "lets_school_helper_align_camera", text="Scale Camera", icon="VIEW_CAMERA_UNSELECTED", toggle=True)
      col.prop(active_empty, "hide_viewport", text="Placement Guide", toggle=True, invert_checkbox=True)
      col.separator()
      for i in range(4):
        row = col.row(align=True)
        row.scale_y = 1.5
        row.alignment = "EXPAND"
        for j in range(6):
          active = i + 1 == size_y and j + 1 == size_x
          row.operator(OT_Resize_Placement.bl_idname, text="", depress=active).size = f"{j+1}x{i+1}"
