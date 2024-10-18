# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Let's School Helper",
    "author": "mbaharip",
    "description": "A collection of tools to help when creating Let's School assets",
    "blender": (4, 0, 0),
    "version": (0, 0, 1),
    "location": "View3D > Sidebar > Let's School Helper",
}

import bpy
import importlib
import json

with open("config.json", "r") as json_file:
    config = json.load(json_file)

def get_config(key):
    return config[key]
def update_config(key, value):
    config[key] = value
    with open("config.json", "w") as json_file:
        json.dump(config, json_file, indent=2)

class Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    default_local_folder: bpy.props.StringProperty(
        name="Local Mods Folder",
        description="The default Local Mods folder (LocalLow/Pathea Games/LetsSchool/LocalMods)",
        subtype="DIR_PATH",
        get=lambda self: get_config('local_folder'),
        set=lambda self, value: update_config('local_folder', value)
    )
    default_steam_folder: bpy.props.StringProperty(
        name="Workshop Folder",
        description="The default Steam Workshop folder (SteamLibrary/steamapps/workshop)",
        subtype="DIR_PATH",
        get=lambda self: get_config('steam_folder'),
        set=lambda self, value: update_config('steam_folder', value)
    )
    default_export_path: bpy.props.StringProperty(
        name="Export Path",
        description="The path to export files to",
        subtype="DIR_PATH",
        get=lambda self: get_config('export_path'),
        set=lambda self, value: update_config('export_path', value)
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "default_local_folder")
        layout.label(text="Default to Windows local mods folder", icon="INFO")

        layout.separator()

        layout.prop(self, "default_steam_folder")
        layout.label(text="Make sure to select the 'workshop' folder", icon="INFO")

        layout.separator()

        layout.prop(self, "default_export_path")

# Get all modules in the func folder with these classes
# Add more classes to the tuple if needed
used_subclasses = (bpy.types.Operator, bpy.types.Panel)

def get_module(name:str):
    try:
        print(f"Getting module '.func.{name}'")
        module = importlib.import_module(f".func.{name}", package=__package__)

        ops_and_views = [
            item for item in module.__dict__.values() if isinstance(item, type) and issubclass(item, used_subclasses)
        ]
        return tuple(ops_and_views)
    except Exception as e:
        print(f"Failed to get module '.func.{name}'")
        print(f"Error: {e}")
        return None

regQueue = (
    Preferences,
)

# Do this to add load order
moduleArray = [
    get_module("mods_folder"),
    get_module("collections"),
    get_module("exporters"),
]
for item in moduleArray:
    print(item)
    if item is not None:
        regQueue += item


def register():
    print("Registering Let's School Helper")
    # Register the UI
    for cls in regQueue:
        bpy.utils.register_class(cls)

    print("Let's School Helper successfully registered")

def unregister():
    print("Unregistering Let's School Helper")

    # Unregister the UI
    for cls in reversed(regQueue):
        bpy.utils.unregister_class(cls)

    print("Let's School Helper successfully unregistered")

if __name__ == "__main__":
    register()
