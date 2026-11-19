# render_gif.py - Render the dig-and-swing animation as pictures for a GIF (version 3, 5 Nov 2026)
# Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0. Blender 4.2.
# Run it AFTER dig_swing.py (test 3), in the same Blender session (it uses the keyframes and the pit ground
# that dig_swing.py made).
# Safety: no internet, nothing saved in the .blend file. Close Blender with "Don't Save".
# It WRITES files into OUT_DIR (inside your project's data/ folder, which Git ignores):
#   PREVIEW = True : one test picture at each key frame of the dig and the swing, 1 extra picture from the
#                    simple "Workbench" engine, and render_info.txt
#   PREVIEW = False: one PNG for every second frame
# In memory only, it adds a camera and a sun, hides the bones' display shapes,
# and turns off the compositor and the video sequencer for this render.
#
# Changes from version 2:
# - new folder gif_test3/;
# - the camera moved back and up, so the longer reach of test 3, the pit and the higher lift fit in the picture
#   (checked on paper on 5 Nov 2026: every part of the machine and the pit stays inside 87% of the picture);
# - the preview pictures are the key frames that dig_swing.py stored (start, reach, lower, fill, curl, lift, mid swing, end);
# - the ground with the pit comes from dig_swing.py and is left where it is; a flat ground is made only
#   when there is none.
# Changes from version 1 (whose 4 test pictures were plain grey):
# - the compositor and the video sequencer are switched off, so the picture is the 3D scene itself;
# - the sky colour is set on every Background node, whatever its name;
# - the ground sits under the tracks, not under the bones' display shapes (which reached z = -3.02);
# - the bones' display shapes ("Custom Shape: ...") are hidden from the render;
# - render_info.txt records what the scene had before these changes.

import os
import bpy
from mathutils import Vector

# ---------- 1. Settings: change only these ----------
# The project folder is two levels above the .blend file (assets/excavator/excavator_1.blend),
# so the script works on any computer, wherever the project folder is.
if not bpy.data.filepath:
    raise RuntimeError("Open assets/excavator/excavator_1.blend first, then run this script.")
PROJECT = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "..", ".."))
OUT_DIR = os.path.join(PROJECT, "data", "renders", "gif_test3")
WIDTH, HEIGHT = 640, 360       # picture size in pixels
STEP = 2                       # render every 2nd frame: 25 fps becomes 12.5 pictures per second
CAMERA_AT = Vector((17.0, -18.0, 9.0))    # in front of the machine and to its left, raised
LOOK_AT = Vector((1.5, -3.0, 2.5))        # between the pit and the raised bucket of the swing
LENS_MM = 35
PREVIEW = False                # True: test pictures only, to check the camera; False: render all

scene = bpy.context.scene
arm = bpy.data.objects["Armature"]
info = []

# ---------- 2. Stop if dig_swing.py has not been run ----------
if not (arm.animation_data and arm.animation_data.action):
    raise RuntimeError("No animation found: run dig_swing.py first, in this same Blender session.")

# ---------- 3. Record the scene's settings before we change them ----------
seq = scene.sequence_editor
info.append(f"Before: compositor nodes {scene.use_nodes}, use compositing {scene.render.use_compositing}, "
            f"use sequencer {scene.render.use_sequencer}, "
            f"sequencer strips {len(seq.sequences_all) if seq else 0}")
if seq:
    for s in seq.sequences_all:
        info.append(f"  strip: {s.name} | type {s.type} | channel {s.channel} | frames {s.frame_final_start}-{s.frame_final_end}")
info.append(f"Before: world {scene.world.name if scene.world else 'none'}, nodes "
            + (", ".join(f"{n.name} ({n.type})" for n in scene.world.node_tree.nodes)
               if scene.world and scene.world.use_nodes else "none"))
for vl in scene.view_layers:
    info.append(f"View layer {vl.name}: used for rendering {vl.use}")
for coll in bpy.data.collections:
    info.append(f"Collection {coll.name}: hidden in renders {coll.hide_render}, objects {len(coll.objects)}")
info.append(f"Film transparent before: {scene.render.film_transparent}")

# ---------- 4. Render the 3D scene itself ----------
scene.render.use_compositing = False      # no compositor nodes on top of the picture
scene.render.use_sequencer = False        # no video-editing strips instead of the picture
scene.render.film_transparent = False     # draw the sky, not a see-through background

# ---------- 5. Hide the bones' display shapes; find the ground under the tracks ----------
scene.frame_set(1)
bpy.context.view_layer.update()
lowest = None
for ob in scene.objects:
    if ob.name.startswith("Custom Shape:"):
        ob.hide_render = True                 # a drawing aid for the bones, not part of the machine
        continue
    if ob.type == 'MESH' and not ob.name.startswith("GIF"):
        for corner in ob.bound_box:
            z = (ob.matrix_world @ Vector(corner)).z
            lowest = z if lowest is None else min(lowest, z)
ground_z = lowest if lowest is not None else 0.0

# ---------- 6. Camera (made once, reused on later runs) ----------
cam = bpy.data.objects.get("GIF Camera")
if cam is None:
    cam = bpy.data.objects.new("GIF Camera", bpy.data.cameras.new("GIF Camera"))
    scene.collection.objects.link(cam)
cam.rotation_mode = 'XYZ'
cam.location = CAMERA_AT
cam.rotation_euler = (LOOK_AT - CAMERA_AT).to_track_quat('-Z', 'Y').to_euler()   # point the camera at LOOK_AT
cam.data.lens = LENS_MM
cam.data.clip_start, cam.data.clip_end = 0.1, 500.0
scene.camera = cam
bpy.context.view_layer.update()
info.append(f"Camera looks along {tuple(round(v, 2) for v in cam.matrix_world.to_3x3() @ Vector((0, 0, -1)))}")

# ---------- 7. Light and sky ----------
if not any(ob.type == 'LIGHT' for ob in scene.objects):
    sun = bpy.data.objects.new("GIF Sun", bpy.data.lights.new("GIF Sun", type='SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (0.8, 0.2, 0.6)
    scene.collection.objects.link(sun)
if scene.world is None:
    scene.world = bpy.data.worlds.new("GIF World")
scene.world.use_nodes = True
for node in scene.world.node_tree.nodes:
    if node.type == 'BACKGROUND':
        node.inputs["Color"].default_value = (0.62, 0.72, 0.82, 1.0)   # pale sky
        node.inputs["Strength"].default_value = 1.0

# ---------- 8. Ground: the pit ground from dig_swing.py, or else a flat 80 m square under the tracks ----------
ground = bpy.data.objects.get("GIF Ground")
if ground is None:
    mesh = bpy.data.meshes.new("GIF Ground")
    mesh.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("GIF Ground", mesh)
    scene.collection.objects.link(ground)
    soil = bpy.data.materials.get("GIF Soil") or bpy.data.materials.new("GIF Soil")
    soil.use_nodes = True
    soil.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.28, 0.20, 1.0)
    mesh.materials.append(soil)
    ground.location = (0, 0, ground_z)
    info.append("Ground: flat (no pit ground from dig_swing.py test 3)")
else:
    info.append("Ground: 'GIF Ground' from dig_swing.py, left where it is")

# ---------- 9. Render settings ----------
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'       # the fast engine in Blender 4.2
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
scene.frame_step = STEP
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 10. Render (Blender is busy until it finishes) ----------
if PREVIEW:
    keys = scene.get("dig_swing_keys")                 # the key frames stored by dig_swing.py
    if keys:
        frames = sorted({int(k) for k in keys})
    else:
        frames = sorted({1, max(1, scene.frame_end // 7), scene.frame_end * 2 // 3, scene.frame_end})
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(OUT_DIR, f"preview_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    eevee = scene.render.engine                      # one extra picture with the simplest engine
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.frame_set(1)
    scene.render.filepath = os.path.join(OUT_DIR, "preview_workbench_0001.png")
    bpy.ops.render.render(write_still=True)
    scene.render.engine = eevee
    with open(os.path.join(OUT_DIR, "render_info.txt"), "w") as f:
        f.write("\n".join(info + [f"Ground height used: z = {ground_z:.2f} m"]))
else:
    scene.render.filepath = os.path.join(OUT_DIR, "frame_")
    bpy.ops.render.render(animation=True)

# ---------- 11. Report: a text inside Blender ----------
prefix = "preview_" if PREVIEW else "frame_"
written = sorted(f for f in os.listdir(OUT_DIR) if f.startswith(prefix) and f.endswith(".png"))
report = [
    "RENDER FOR GIF - " + ("PREVIEW (test pictures)" if PREVIEW else "ALL PICTURES"),
    f"{len(written)} PNG pictures in {OUT_DIR}",
    f"Ground height used: z = {ground_z:.2f} m",
] + info
text = bpy.data.texts.get("render_gif_report") or bpy.data.texts.new("render_gif_report")
text.clear()
text.write("\n".join(report))
