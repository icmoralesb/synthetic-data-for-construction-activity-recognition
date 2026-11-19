# dig_swing.py - Dig and swing with random speed (test 3, 5 Nov 2026)
# Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0. Blender 4.2.
# Safety: no internet, nothing saved in the .blend file. It changes only the open file in memory (keyframes,
# one constraint setting, and a ground with a pit). It WRITES one small text file, REPORT_FILE (inside your
# project's data/ folder, which Git ignores), so that Claude can read the report directly.
# Close Blender with "Don't Save".
#
# Changes from test 2, after the preview pictures of 4 Nov 2026 and the rig read from the .blend file on 5 Nov 2026:
# - The bucket's curl now stays inside its real range. At rest, this model's bucket is almost fully closed:
#   it can close only 22.75 deg more before its back plate (Bucket Tray) touches the stick, and it can open
#   146 deg before the bucket cylinder is fully closed. Test 2 asked for +30 deg (fill) and +60 deg (lift),
#   so the bucket turned through the stick.
# - The dig has five phases (reach, lower, fill, curl, lift), designed from where the teeth must be.
# - A pit in front of the machine, so the bucket digs into soil we can see. In test 2 the bucket went
#   1 m under a flat ground, and only the teeth showed above it.
# - New checks at every frame: the curl range, the strokes of the three hydraulic cylinders, the bucket
#   links, and the bucket and the stick against the ground and the pit. At the key frames: real mesh
#   contact between the bucket and the stick.
# - Updated twice on 5 Nov 2026 after checking the side-view drawings against site practice:
#   when the bucket is full, the operator closes it until its TIP LINE (bucket pin -> teeth tip) is level,
#   and keeps it level through the lift and the swing. Then the opening of the bucket faces up, so even wet
#   sand or muddy clay stays in. (Level TEETH were not enough: the opening still leaned 43 deg towards the
#   machine, and wet material would pour out.) So a new "curl" phase closes the full bucket in the pit, and
#   new checks hold the tip line level at every frame from the end of the curl to the end of the swing.

import os
import bpy
import math
import random
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# ---------- 1. Settings: change only these ----------
SEED = 1               # same seed = same random speeds; another seed = new speeds
FPS = 25               # frames per second, the same as our real video B
REACH_S = (1.5, 2.5)   # seconds: the arm goes out and up, and the bucket opens
LOWER_S = (1.0, 2.0)   # seconds: the bucket goes down into the pit, teeth first
FILL_S = (2.0, 4.0)    # seconds: the stick drags the bucket through the soil towards the cab; the bucket closes
CURL_S = (0.6, 1.2)    # seconds: the full bucket closes until its tip line is level, still in the pit
LIFT_S = (1.5, 3.0)    # seconds: the bucket rises out of the pit with its tip line kept level
SWING_S = (3.0, 6.0)   # seconds: the loaded swing
SWING_DEG = 90         # swing angle in degrees; positive = to the operator's left
# End of each dig phase, measured from the START pose: (reach change m, height change m, bucket curl deg from rest).
# Curl: negative = the bucket opens, positive = it closes. Designed on 5 Nov 2026 from where the teeth must be.
# Two angles, both seen from the side; 0 deg = level, pointing at the machine; +90 = straight up; -90 = straight down:
#   "tip line" = the line from the bucket pin to the teeth tip;
#   "teeth"    = the direction the teeth point (in this bucket always 38.5 deg above the tip line).
REACH = (5.0, 2.1, -76)     # teeth tip 7.9 m in front of the swing axis, 1.0 m above the ground; tip line -54, teeth -16
LOWER = (4.6, 0.25, -113)   # teeth at the far end of the pit, 1.2 m below the ground; tip line -75, teeth -36 (into the soil)
FILL = (3.3, -0.35, -96)    # teeth dragged 2.4 m towards the cab, 1.0 m below the ground; tip line -35, teeth +3
CURL = (3.0, 0.2, -63)      # bucket full and closed: tip line 0 (level), teeth +38; opening faces up; still in the pit
LIFT = (1.25, 2.75, -70)    # bucket out of the pit, tip line still 0, its lowest point 1.9 m above the ground
TIP_LINE_TOLERANCE = 5.0    # from the end of the curl to the end of the swing, tip line within 5 deg of level
# The bucket's real range against the stick, measured from the model on 5 Nov 2026 (curl from rest, degrees):
CURL_LIMITS = (-146.0, 22.75)   # open: the bucket cylinder is fully closed; close: the bucket's back touches the stick
CURL_MARGIN = 5.0               # stay this far from both limits
# The pit: distances along the arm's direction at the start, from the swing axis (metres)
PIT_NEAR, PIT_FAR = 4.3, 10.4
PIT_HALF_WIDTH = 1.3            # the bucket is 1.5 m wide: 0.55 m of room on each side
PIT_DEPTH = 1.2
CUT = 0.30                      # the bucket may cut this far into the pit floor (that is the digging)
# Our safety margins for the hydraulic cylinders (our choice, not from a standard):
ROD_OVERLAP = 0.15              # at full extension, keep at least 0.15 m of the rod inside the barrel
ROD_BOTTOM = 0.05               # at full retraction, keep the rod end 0.05 m from the barrel bottom
# The project folder is two levels above the .blend file (assets/excavator/excavator_1.blend),
# so the script works on any computer, wherever the project folder is.
if not bpy.data.filepath:
    raise RuntimeError("Open assets/excavator/excavator_1.blend first, then run this script.")
PROJECT = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "..", ".."))
REPORT_FILE = os.path.join(PROJECT, "data", "renders", "dig_swing_report.txt")

# ---------- 2. The rig (names read from the .blend file) ----------
arm = bpy.data.objects["Armature"]
scene = bpy.context.scene
sphere = arm.pose.bones["CO: Bucket"]      # the control sphere: the only thing we animate
cab = arm.pose.bones["Pivot Point Main"]   # turns the cab by itself: we only measure it
cr = arm.pose.bones["Bucket Main"].constraints["Copy Rotation"]   # gives the bucket its curl
# Each cylinder: (bone at the barrel's pin, barrel object, bone at the rod's pin, rod object)
CYLINDERS = {
    "boom cylinder": ("Main Arm Pivot 2", "Main Hydraulic Arm", "Main Arm Pivot 1", "Main Hydraulic Piston"),
    "stick cylinder": ("Boom Pivot 1", "Boom Hydraulic Arm", "Boom Pivot 2", "Boom Hydraulic Piston"),
    "bucket cylinder": ("Stick Pivot 1", "Stick Hydraulic Arm", "Stick Pivot 2", "Stick Hydraulic Piston"),
}
BUCKET_PARTS = ["Bucket Tray", "Bucket Side", "Bucket Front", "Bucket Liner", "Bucket Claw"]   # all follow Bucket Main
STICK_PARTS = ["Stick Arm 1", "Stick Arm 2"]                                                  # both follow Stick
rng = random.Random(SEED)

# ---------- 3. Start clean, and fix the bucket's constraint in memory ----------
scene.render.fps = FPS
scene.render.fps_base = 1
if arm.animation_data:
    arm.animation_data.action = None       # unlink keyframes from an earlier run
sphere.location = (0, 0, 0)                # sphere back to its rest place
sphere.rotation_euler = (0, 0, 0)          # and to its rest angle
old_mix = cr.mix_mode
cr.mix_mode = "AFTER"                      # "After Original": keep the bucket's own turn, add the curl on top
scene.frame_set(1)
bpy.context.view_layer.update()

# ---------- 4. Geometry at rest (world coordinates, metres) ----------
rest = arm.matrix_world @ sphere.bone.matrix_local   # rest place and axes of the sphere
rest_inv = rest.inverted()
axes = rest.to_3x3().normalized()                     # the sphere's own axes
start = rest.translation.copy()                       # the sphere's rest position
centre = arm.matrix_world @ cab.bone.head_local       # a point on the swing axis
flat = Vector((start.x - centre.x, start.y - centre.y, 0))
r0 = flat.length                                      # reach at the start
bearing0 = math.atan2(flat.y, flat.x)                 # direction of the arm at the start
left = Vector((0, 0, 1)).cross(flat.normalized())     # the machine's left-right axis
c2 = np.array([centre.x, centre.y])                   # the same directions as plain numbers, for the pit
f2 = np.array([flat.normalized().x, flat.normalized().y])
l2 = np.array([left.x, left.y])

# The ground: the lowest point of the machine at rest (the tracks), the same rule as render_gif.py.
ground_z = None
for ob in scene.objects:
    if ob.type == 'MESH' and not ob.name.startswith(("Custom Shape:", "GIF")):
        for corner in ob.bound_box:
            z = (ob.matrix_world @ Vector(corner)).z
            ground_z = z if ground_z is None else min(ground_z, z)


def soil(name, rgb):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
    return m


# A ground of 80 m x 80 m with a box-shaped pit in front of the machine (made again on every run).
def make_ground():
    old = bpy.data.objects.get("GIF Ground")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    g, b, big = ground_z, ground_z - PIT_DEPTH, 40.0
    n, fa, w = PIT_NEAR, PIT_FAR, PIT_HALF_WIDTH

    def pt(d, s, z):                                  # (distance forward, distance to the left, height) -> world
        p = c2 + f2 * d + l2 * s
        return (float(p[0]), float(p[1]), z)
    quads = [  # four ground pieces around the hole, then the pit floor and its four walls
        [(-big, -big, g), (n, -big, g), (n, big, g), (-big, big, g)],
        [(fa, -big, g), (big, -big, g), (big, big, g), (fa, big, g)],
        [(n, -big, g), (fa, -big, g), (fa, -w, g), (n, -w, g)],
        [(n, w, g), (fa, w, g), (fa, big, g), (n, big, g)],
        [(n, -w, b), (fa, -w, b), (fa, w, b), (n, w, b)],
        [(n, -w, g), (n, w, g), (n, w, b), (n, -w, b)],
        [(fa, w, g), (fa, -w, g), (fa, -w, b), (fa, w, b)],
        [(fa, -w, g), (n, -w, g), (n, -w, b), (fa, -w, b)],
        [(n, w, g), (fa, w, g), (fa, w, b), (n, w, b)],
    ]
    verts = [pt(*c) for q in quads for c in q]
    faces = [tuple(range(4 * i, 4 * i + 4)) for i in range(len(quads))]
    mesh = bpy.data.meshes.new("GIF Ground")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(soil("GIF Soil", (0.15, 0.09, 0.05)))        # the ground (darker: 0.36 looked almost white)
    mesh.materials.append(soil("GIF Soil Dug", (0.07, 0.04, 0.025)))   # fresh, darker soil in the pit
    for i, poly in enumerate(mesh.polygons):
        poly.material_index = 0 if i < 4 else 1
    mesh.update()
    ground = bpy.data.objects.new("GIF Ground", mesh)
    scene.collection.objects.link(ground)


make_ground()


# ---------- 5. Tools ----------
# World position from a reach change, a height change and a swing angle.
def place(d_reach, d_height, swing_deg=0):
    a = bearing0 + math.radians(swing_deg)
    r = r0 + d_reach
    return Vector((centre.x + r * math.cos(a), centre.y + r * math.sin(a), start.z + d_height))


# Put the sphere at a world position with a bucket curl; add keyframes if a frame is given.
def set_sphere(position, curl_deg, frame=None):
    sphere.location = rest_inv @ position
    curl = Matrix.Rotation(math.radians(curl_deg), 3, left)
    sphere.rotation_euler = (axes.transposed() @ curl @ axes).to_euler('XYZ', sphere.rotation_euler)
    if frame is not None:
        sphere.keyframe_insert("location", frame=frame)
        sphere.keyframe_insert("rotation_euler", frame=frame)


# Let Blender move the rig, then read what we check.
def measure():
    bpy.context.view_layer.update()
    rig = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    bones = rig.pose.bones
    world = rig.matrix_world
    bucket = bones["Bucket Main"].matrix
    stick = bones["Stick"].matrix
    turn = bones[cab.name].matrix.to_3x3() @ cab.bone.matrix_local.to_3x3().inverted()
    # the bucket links: D (pin on the stick), C (joint where the cylinder pushes), B (pin on the bucket)
    d_pin = world @ bones["Bucket Arm 1"].head
    c_pin = world @ bones["Bucket Arm 2"].head
    b_pin = world @ bones["Bucket Arm 2"].tail
    hinge_axis = (world.to_3x3() @ bucket.to_3x3()).col[0].normalized()
    return {
        "pin": world @ bucket.translation,                                   # the bucket pin
        "rel": stick.to_quaternion().inverted() @ bucket.to_quaternion(),    # the bucket seen from the stick
        "cab": math.degrees(math.atan2(turn[1][0], turn[0][0])),
        "bucket_world": world @ bucket,
        "cyl": {name: ((world @ bones[p1].head) - (world @ bones[p2].head)).length
                for name, (p1, _, p2, _) in CYLINDERS.items()},
        "bend": (c_pin - d_pin).cross(b_pin - c_pin).dot(hinge_axis),        # which side the links bend to
        "link_gap": (b_pin - world @ bucket @ Vector((0, bones["Bucket Main"].length, 0))).length,
    }


# Angle in degrees between two orientations.
def angle_between(q1, q2):
    return math.degrees(2 * math.acos(min(1.0, abs(q1.dot(q2)))))


# Signed curl from rest: the turn of the bucket against the stick, about the bucket's hinge (its X axis).
def curl_of(rel):
    axis, angle = (rel_rest.inverted() @ rel).to_axis_angle()
    return math.degrees(angle) * (1 if axis.x >= 0 else -1)


# Slow in, slow out: 0 -> 0, 0.5 -> 0.5, 1 -> 1, with zero speed at both ends.
def ease(t):
    return (1 - math.cos(math.pi * t)) / 2


# The vertices of a part, in world coordinates, as an N x 3 table of numbers.
LOCAL = {}


def world_points(name):
    ob = bpy.data.objects[name]
    if name not in LOCAL:
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        LOCAL[name] = co.reshape(-1, 3)
    m = np.array(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world)
    return LOCAL[name] @ m[:3, :3].T + m[:3, 3]


# How far the lowest point of some parts is above the level it may reach (negative = too low).
# Outside the pit that level is the ground; inside the pit it is the pit floor minus `cut`.
def clearance(parts, cut):
    worst = None
    for name in parts:
        p = world_points(name)
        rel = p[:, :2] - c2
        d, s = rel @ f2, rel @ l2
        in_pit = (d >= PIT_NEAR) & (d <= PIT_FAR) & (np.abs(s) <= PIT_HALF_WIDTH)
        level = np.where(in_pit, ground_z - PIT_DEPTH - cut, ground_z)
        low = float((p[:, 2] - level).min())
        worst = low if worst is None else min(worst, low)
    return worst


# Number of touching triangle pairs between the bucket and the stick (real meshes, with modifiers).
def contacts():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {}
    for name in BUCKET_PARTS + STICK_PARTS:
        ob = bpy.data.objects[name].evaluated_get(depsgraph)
        me = ob.to_mesh()
        trees[name] = BVHTree.FromPolygons([ob.matrix_world @ v.co for v in me.vertices],
                                           [tuple(p.vertices) for p in me.polygons])
        ob.to_mesh_clear()
    return sum(len(trees[b].overlap(trees[s])) for b in BUCKET_PARTS for s in STICK_PARTS)


# The tip line and the teeth direction (see section 1), and the teeth tip's height above the ground.
def bucket_angles(m):
    out = Vector((m["pin"].x - centre.x, m["pin"].y - centre.y, 0)).normalized()   # away from the machine

    def side_angle(v):                           # side-view angle: 0 = level towards the machine, +90 = up
        return math.degrees(math.atan2(v.z, -(v.x * out.x + v.y * out.y)))
    tip = m["bucket_world"] @ tip_in_bucket
    tooth = m["bucket_world"].to_3x3() @ tooth_in_bucket
    return side_angle(tip - m["pin"]), side_angle(tooth), tip.z - ground_z


# ---------- 6. Rest measurements, and the rig check ----------
m0 = measure()                                  # the rig at rest
rel_rest = m0["rel"]
start_cm = (m0["pin"] - start).length * 100     # bucket pin against sphere, in cm
bend_rest = m0["bend"]
# The teeth tip: the claw vertex farthest from the bucket pin, kept in the bucket's own frame.
# The tooth direction: from the middle of the tooth's base to its tip (the tooth is 0.25 m long).
claw = world_points("Bucket Claw")
far = claw[np.argmax(np.linalg.norm(claw - np.array(m0["pin"]), axis=1))]
base = claw[np.linalg.norm(claw - far, axis=1) > 0.15].mean(axis=0)
tip_in_bucket = m0["bucket_world"].inverted() @ Vector(far.tolist())
tooth_in_bucket = (m0["bucket_world"].to_3x3().inverted() @ Vector((far - base).tolist())).normalized()
# Each cylinder's allowed length, from its barrel and rod meshes: the rod must stay inside the barrel.
stroke = {}
rig0 = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
for name, (p1, barrel, p2, rod) in CYLINDERS.items():
    a = np.array(rig0.matrix_world @ rig0.pose.bones[p1].head)
    b = np.array(rig0.matrix_world @ rig0.pose.bones[p2].head)
    u = (b - a) / np.linalg.norm(b - a)                       # along the cylinder, from the barrel pin
    barrel_along = (world_points(barrel) - a) @ u             # barrel: from its pin towards the rod pin
    rod_along = (world_points(rod) - b) @ (-u)                # rod: from its pin towards the barrel pin
    stroke[name] = (barrel_along.min() + rod_along.max() + ROD_BOTTOM,
                    barrel_along.max() + rod_along.max() - ROD_OVERLAP)
contacts_rest = contacts()
# Rig check: with "After Original", a swing must not twist the bucket.
set_sphere(place(0, 0, SWING_DEG), 0)           # move the sphere round by the swing angle
m1 = measure()
test_twist = angle_between(m0["rel"], m1["rel"])
set_sphere(start, 0)                            # back to rest


# ---------- 7. Random speed: draw a duration for each phase ----------
def frames_for(range_s):
    return max(1, round(rng.uniform(*range_s) * FPS))


n_reach = frames_for(REACH_S)
n_lower = frames_for(LOWER_S)
n_fill = frames_for(FILL_S)
n_curl = frames_for(CURL_S)
n_lift = frames_for(LIFT_S)
n_swing = frames_for(SWING_S)
f_reach = 1 + n_reach
f_lower = f_reach + n_lower
f_fill = f_lower + n_fill
f_curl = f_fill + n_curl
f_lift = f_curl + n_lift        # last frame of the dig
f_end = f_lift + n_swing        # last frame of the swing


def swing_at(frame):
    t = (frame - f_lift) / n_swing                       # 0 at the start of the swing, 1 at the end
    return SWING_DEG * ease(t)                           # slow in, slow out


# The dig pose at any frame: eased straight-line steps between the phase ends.
START = (0.0, 0.0, 0.0)
dig_steps = [(1, f_reach, START, REACH), (f_reach, f_lower, REACH, LOWER),
             (f_lower, f_fill, LOWER, FILL), (f_fill, f_curl, FILL, CURL), (f_curl, f_lift, CURL, LIFT)]


def dig_at(frame):
    for a, b, p, q in dig_steps:
        if frame <= b:
            e = ease((frame - a) / (b - a))
            return tuple(p[i] + (q[i] - p[i]) * e for i in range(3))
    return LIFT


def designed(frame):                             # (target position, designed curl) at any frame
    if frame <= f_lift:
        d_reach, d_height, curl = dig_at(frame)
        return place(d_reach, d_height), curl
    return place(LIFT[0], LIFT[1], swing_at(frame)), LIFT[2]


# ---------- 8. Keyframes: one key at every frame ----------
for frame in range(1, f_end + 1):
    target, curl = designed(frame)
    set_sphere(target, curl, frame=frame)
scene.frame_start = 1
scene.frame_end = f_end
f_mid = f_lift + n_swing // 2
scene["dig_swing_keys"] = [1, f_reach, f_lower, f_fill, f_curl, f_lift, f_mid, f_end]   # render_gif.py previews these

# ---------- 9. Checks ----------
# 9a. At EVERY frame: reach gap, curl range, cylinder strokes, bucket links, ground and pit.
curl_ok = (CURL_LIMITS[0] + CURL_MARGIN, CURL_LIMITS[1] - CURL_MARGIN)
worst = {"gap": (0.0, 1), "curl_min": (0.0, 1), "curl_max": (0.0, 1),
         "bucket_ground": (9.0, 1), "stick_ground": (9.0, 1), "link_gap": (0.0, 1),
         "tip_drop": (0.0, f_fill), "tip_level": (0.0, f_curl)}
highest_tip = None               # during the curl: the highest tip line so far
cyl_seen = {name: [9.0, 0.0] for name in CYLINDERS}
link_flips = []
for frame in range(1, f_end + 1):
    scene.frame_set(frame)
    m = measure()
    target, _ = designed(frame)
    gap = (m["pin"] - target).length * 100
    curl = curl_of(m["rel"])
    if gap > worst["gap"][0]:
        worst["gap"] = (gap, frame)
    if curl < worst["curl_min"][0]:
        worst["curl_min"] = (curl, frame)
    if curl > worst["curl_max"][0]:
        worst["curl_max"] = (curl, frame)
    for name, length in m["cyl"].items():
        cyl_seen[name] = [min(cyl_seen[name][0], length), max(cyl_seen[name][1], length)]
    if m["bend"] * bend_rest <= 0:
        link_flips.append(frame)
    if m["link_gap"] * 100 > worst["link_gap"][0]:
        worst["link_gap"] = (m["link_gap"] * 100, frame)
    gb = clearance(BUCKET_PARTS, CUT)
    gs = clearance(STICK_PARTS, 0.0)
    if gb < worst["bucket_ground"][0]:
        worst["bucket_ground"] = (gb, frame)
    if gs < worst["stick_ground"][0]:
        worst["stick_ground"] = (gs, frame)
    if f_fill <= frame <= f_curl:                # full bucket closing: its tip line may only go up
        tl = bucket_angles(m)[0]
        highest_tip = tl if highest_tip is None else max(highest_tip, tl)
        if highest_tip - tl > worst["tip_drop"][0]:
            worst["tip_drop"] = (highest_tip - tl, frame)
    if frame >= f_curl:                          # lift and swing: the tip line must stay level
        tl = bucket_angles(m)[0]
        if abs(tl) > abs(worst["tip_level"][0]):
            worst["tip_level"] = (tl, frame)

every_frame = []
ok = worst["gap"][0] < 2
every_frame.append(f"IK reach: largest gap {worst['gap'][0]:.1f} cm at frame {worst['gap'][1]}" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = ok
ok = curl_ok[0] <= worst["curl_min"][0] and worst["curl_max"][0] <= curl_ok[1]
every_frame.append(f"Bucket curl from rest: {worst['curl_min'][0]:.1f} (frame {worst['curl_min'][1]}) to "
                   f"{worst['curl_max'][0]:.1f} deg (frame {worst['curl_max'][1]}); allowed {curl_ok[0]:.1f} to {curl_ok[1]:.1f}"
                   + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok
for name, (lo, hi) in cyl_seen.items():
    ok = stroke[name][0] <= lo and hi <= stroke[name][1]
    every_frame.append(f"{name}: length {lo:.2f} to {hi:.2f} m; the rod stays in the barrel from "
                       f"{stroke[name][0]:.2f} to {stroke[name][1]:.2f} m" + (" -> OK" if ok else " -> PROBLEM"))
    all_ok = all_ok and ok
ok = not link_flips and worst["link_gap"][0] < 2
every_frame.append(f"Bucket links: bend side flipped at {len(link_flips)} frames"
                   + (f" (first {link_flips[0]})" if link_flips else "")
                   + f"; largest gap at the bucket's link pin {worst['link_gap'][0]:.1f} cm" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok
ok = worst["bucket_ground"][0] > -0.02
every_frame.append(f"Bucket against the ground (and {CUT:.2f} m under the pit floor): smallest clearance "
                   f"{worst['bucket_ground'][0]:.2f} m at frame {worst['bucket_ground'][1]}" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok
ok = worst["stick_ground"][0] > -0.02
every_frame.append(f"Stick against the ground and the pit floor: smallest clearance "
                   f"{worst['stick_ground'][0]:.2f} m at frame {worst['stick_ground'][1]}" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok
ok = worst["tip_drop"][0] <= 1.0
every_frame.append(f"Curl (frames {f_fill}-{f_curl}): the full bucket's tip line went back down by at most "
                   f"{worst['tip_drop'][0]:.1f} deg (frame {worst['tip_drop'][1]}); allowed 1" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok
ok = abs(worst["tip_level"][0]) <= TIP_LINE_TOLERANCE
every_frame.append(f"Lift and swing (frames {f_curl}-{f_end}): tip line furthest from level {worst['tip_level'][0]:+.1f} deg "
                   f"at frame {worst['tip_level'][1]}; allowed +/-{TIP_LINE_TOLERANCE:.0f}" + (" -> OK" if ok else " -> PROBLEM"))
all_ok = all_ok and ok

# 9b. Key frames: target reached, cab angle, signed curl, tip line, teeth, teeth height, bucket-stick contact, twist.
checks = [(f_reach, "arm out, bucket open", REACH, 0),
          (f_lower, "teeth at the far end of the pit", LOWER, 0),
          (f_fill, "end of the fill", FILL, 0),
          (f_curl, "bucket closed, tip line level", CURL, 0),
          (f_lift, "lifted, swing starts", LIFT, 0),
          (f_mid, "middle of swing", LIFT, swing_at(f_mid)),
          (f_end, "end of swing", LIFT, SWING_DEG)]
results = []
rel_lift = None
for frame, name, pose, cab_expected in checks:
    scene.frame_set(frame)
    m = measure()
    miss_cm = (m["pin"] - place(pose[0], pose[1], cab_expected)).length * 100
    cab_now = m["cab"] - m0["cab"]
    curl_now = curl_of(m["rel"])
    if frame == f_lift:
        rel_lift = m["rel"]
    twist = angle_between(rel_lift, m["rel"]) if frame > f_lift else None
    tip_deg, teeth_deg, tip_h = bucket_angles(m)
    touch = contacts()
    ok = (miss_cm < 2 and abs(cab_now - cab_expected) < 2 and abs(curl_now - pose[2]) < 3
          and touch <= contacts_rest and (twist is None or twist < 3))
    all_ok = all_ok and ok
    results.append(f"frame {frame} ({name}): misses sphere by {miss_cm:.1f} cm; cab {cab_now:.1f} deg "
                   f"(expected {cab_expected:.1f}); curl {curl_now:.1f} deg (expected {pose[2]:.1f}); "
                   f"tip line {tip_deg:+.0f} deg, teeth {teeth_deg:+.0f} deg; teeth tip {tip_h:+.2f} m from the ground; "
                   f"bucket-stick contacts {touch} (at rest {contacts_rest})"
                   + (f"; twist {twist:.1f} deg" if twist is not None else "")
                   + (" -> OK" if ok else " -> PROBLEM"))
scene.frame_set(1)
all_ok = all_ok and start_cm < 2 and test_twist < 3


# ---------- 10. Report: a text inside Blender, and the same text in REPORT_FILE ----------
def sec(n):
    return n / FPS


report = [
    f"DIG AND SWING TEST 3 - seed {SEED}, {FPS} fps, {f_end} frames ({sec(f_end):.2f} s)",
    f"Rig fix in memory: Copy Rotation on Bucket Main, mix {old_mix} -> {cr.mix_mode} (file not saved)",
    f"World points: sphere at rest ({start.x:.2f}, {start.y:.2f}, {start.z:.2f}), "
    f"swing axis point ({centre.x:.2f}, {centre.y:.2f}, {centre.z:.2f}); reach {r0:.2f} m",
    f"Ground z = {ground_z:.2f} m; pit {PIT_NEAR}-{PIT_FAR} m in front of the swing axis, "
    f"{2 * PIT_HALF_WIDTH:.1f} m wide, {PIT_DEPTH} m deep (object 'GIF Ground', in memory)",
    f"Start: bucket pin {start_cm:.1f} cm from the sphere" + (" -> OK" if start_cm < 2 else " -> PROBLEM"),
    f"Rig check: sphere moved {SWING_DEG} deg round -> cab turned {m1['cab'] - m0['cab']:.1f} deg, "
    f"bucket twisted {test_twist:.1f} deg against the stick" + (" -> OK" if test_twist < 3 else " -> PROBLEM"),
    "",
    f"Dig: reach {sec(n_reach):.2f} s + lower {sec(n_lower):.2f} s + fill {sec(n_fill):.2f} s"
    f" + curl {sec(n_curl):.2f} s + lift {sec(n_lift):.2f} s = {sec(n_reach + n_lower + n_fill + n_curl + n_lift):.2f} s",
    f"Swing: {SWING_DEG} deg in {sec(n_swing):.2f} s (average {abs(SWING_DEG) / sec(n_swing):.1f} deg/s,"
    f" top {math.pi / 2 * abs(SWING_DEG) / sec(n_swing):.1f} deg/s)",
    "",
    "Labels (frame 1 starts at 0.00 s)",
    "activity,first_frame,last_frame,start_s,end_s",
    f"dig,1,{f_lift},0.00,{sec(f_lift):.2f}",
    f"swing,{f_lift + 1},{f_end},{sec(f_lift):.2f},{sec(f_end):.2f}",
    "",
    "Checks at every frame",
] + every_frame + ["", "Checks at the key frames"] + results + [
    "RESULT: " + ("all checks passed" if all_ok else "a check failed - send me this report")]

text = bpy.data.texts.get("dig_swing_report") or bpy.data.texts.new("dig_swing_report")
text.clear()
text.write("\n".join(report))
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
with open(REPORT_FILE, "w") as f:
    f.write("\n".join(report))
