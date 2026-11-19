# scene_check.py - Why are the test pictures plain grey? A list of what is in the scene (a test; it changes nothing)
# Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0. Blender 4.2.
# Safety: no internet, nothing changed in the scene, nothing saved in the .blend file.
# It WRITES one small text file, OUT_FILE below (inside your project's data/ folder, which Git ignores),
# so that Claude can read the report directly. Close Blender with "Don't Save".

import os
import bpy
from mathutils import Vector

# The project folder is two levels above the .blend file (assets/excavator/excavator_1.blend),
# so the script works on any computer, wherever the project folder is.
if not bpy.data.filepath:
    raise RuntimeError("Open assets/excavator/excavator_1.blend first, then run this script.")
PROJECT = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "..", ".."))
OUT_FILE = os.path.join(PROJECT, "data", "renders", "scene_check.txt")

scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
cam = scene.camera
lines = [
    f"Render engine: {scene.render.engine}; view transform: {scene.view_settings.view_transform}",
    f"Unit scale: {scene.unit_settings.scale_length}; unit system: {scene.unit_settings.system}",
    f"World: {scene.world.name if scene.world else 'none'}",
    f"Camera: {cam.name if cam else 'none'}"
    + (f" at {tuple(round(v, 2) for v in cam.matrix_world.translation)}, "
       f"clip {cam.data.clip_start} to {cam.data.clip_end} m, lens {cam.data.lens} mm" if cam else ""),
    "",
    "Objects: name | type | shown in render | location | size (x, y, z) | lowest z | highest z | camera inside its box?",
]
cam_pos = cam.matrix_world.translation if cam else None
for ob in sorted(scene.objects, key=lambda o: o.name):
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    inside = cam_pos is not None and all(lo[i] <= cam_pos[i] <= hi[i] for i in range(3))
    size = hi - lo
    lines.append(f"{ob.name} | {ob.type} | {not ob.hide_render} | "
                 f"({ob.matrix_world.translation.x:.2f}, {ob.matrix_world.translation.y:.2f}, {ob.matrix_world.translation.z:.2f}) | "
                 f"({size.x:.2f}, {size.y:.2f}, {size.z:.2f}) | {lo.z:.2f} | {hi.z:.2f} | {'YES' if inside else 'no'}")

text = bpy.data.texts.get("scene_check") or bpy.data.texts.new("scene_check")
text.clear()
text.write("\n".join(lines))
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
with open(OUT_FILE, "w") as f:
    f.write("\n".join(lines))
