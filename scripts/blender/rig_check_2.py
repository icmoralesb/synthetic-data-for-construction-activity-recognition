# rig_check_2.py - Why the lift misses and why the bucket twists (a test; it changes nothing)
# Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0. Blender 4.2.
# Safety: no internet, no files read or written, nothing saved, no keyframes made.
# It puts the sphere back at rest at the end. Close Blender with "Don't Save".

import bpy
import math
from mathutils import Matrix, Vector

arm = bpy.data.objects["Armature"]
bones = arm.pose.bones
sphere = bones["CO: Bucket"]
cab = bones["Pivot Point Main"]
lines = []

# ---------- 1. How the rig is set up ----------
ik = bones["Stick"].constraints["IK"]
pole = ik.pole_target.name if ik.pole_target else "none"
lines.append(f"IK solver: {arm.pose.ik_solver}")
lines.append(f"IK on Stick: chain {ik.chain_count}, use tail {ik.use_tail}, "
             f"stretch {ik.use_stretch}, iterations {ik.iterations}, pole {pole}")
for name in ("Boom", "Stick"):
    b = bones[name]
    for ax in "xyz":
        if getattr(b, "use_ik_limit_" + ax):
            limit = (f"limited from {math.degrees(getattr(b, 'ik_min_' + ax)):.0f} "
                     f"to {math.degrees(getattr(b, 'ik_max_' + ax)):.0f} deg")
        else:
            limit = "not limited"
        lines.append(f"  {name} {ax}: locked {getattr(b, 'lock_ik_' + ax)}, {limit}")
cr = bones["Bucket Main"].constraints["Copy Rotation"]
lines.append(f"Copy Rotation on Bucket Main: owner {cr.owner_space}, target {cr.target_space}, "
             f"mix {cr.mix_mode}, copies x {cr.use_x} y {cr.use_y} z {cr.use_z}, "
             f"order {cr.euler_order}, influence {cr.influence:.2f}")
lt = cab.constraints["Locked Track"]
lines.append(f"Locked Track on Pivot Point Main: track {lt.track_axis}, lock {lt.lock_axis}")
for name in ("CO: Bucket", "Bucket Main", "Stick"):
    m = (arm.matrix_world @ bones[name].bone.matrix_local).to_3x3().normalized()
    x, y = m.col[0], m.col[1]
    lines.append(f"  {name} rest axes: X ({x.x:.2f}, {x.y:.2f}, {x.z:.2f}), "
                 f"Y ({y.x:.2f}, {y.y:.2f}, {y.z:.2f})")

# ---------- 2. Start clean; same geometry as dig_swing.py ----------
if arm.animation_data:
    arm.animation_data.action = None
sphere.location = (0, 0, 0)
sphere.rotation_euler = (0, 0, 0)
rest = arm.matrix_world @ sphere.bone.matrix_local
rest_inv = rest.inverted()
axes = rest.to_3x3().normalized()
start = rest.translation.copy()
centre = arm.matrix_world @ cab.bone.head_local
flat = Vector((start.x - centre.x, start.y - centre.y, 0))
r0 = flat.length
bearing0 = math.atan2(flat.y, flat.x)
left = Vector((0, 0, 1)).cross(flat.normalized())


# ---------- 3. Tools (the same as in dig_swing.py, with two small changes) ----------
def place(d_reach, d_height, swing_deg=0):
    a = bearing0 + math.radians(swing_deg)
    r = r0 + d_reach
    return Vector((centre.x + r * math.cos(a), centre.y + r * math.sin(a), start.z + d_height))


def set_sphere(position, curl_deg=0, spin_deg=0):
    sphere.location = rest_inv @ position
    spin = Matrix.Rotation(math.radians(spin_deg), 3, 'Z')
    curl = Matrix.Rotation(math.radians(curl_deg), 3, left)
    sphere.rotation_euler = (axes.transposed() @ spin @ curl @ axes).to_euler('XYZ', sphere.rotation_euler)


def measure():
    bpy.context.view_layer.update()
    rig = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    bucket = rig.pose.bones["Bucket Main"].matrix
    stick = rig.pose.bones["Stick"].matrix
    pin = rig.matrix_world @ bucket.translation
    return pin, stick.to_quaternion().inverted() @ bucket.to_quaternion()


def angle_between(q1, q2):
    return math.degrees(2 * math.acos(min(1.0, abs(q1.dot(q2)))))


def gap_cm(d_reach, d_height):
    set_sphere(place(d_reach, d_height))
    return (measure()[0] - place(d_reach, d_height)).length * 100


# ---------- 4. Reach map: where can the arm put the bucket pin? ----------
reaches = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
lines.append("")
lines.append("Reach map: gap in cm between bucket pin and sphere ('.' = reached, gap under 2 cm)")
lines.append("reach change (m):     " + "".join(f"{d:6.1f}" for d in reaches))
for d_height in [2.5, 2.0, 1.5, 1.0, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0]:
    cells = ""
    for d_reach in reaches:
        g = gap_cm(d_reach, d_height)
        cells += "     ." if g < 2 else f"{g:6.0f}"
    lines.append(f"height change {d_height:+4.1f} m:" + cells)

# ---------- 5. Highest lift the arm reaches at the lift reach (-0.5 m) ----------
d_height = 2.5
while d_height > 0 and gap_cm(-0.5, d_height) >= 2:
    d_height = round(d_height - 0.1, 1)
lift_max = d_height
lines.append("")
lines.append(f"Highest lift reached at reach change -0.5 m: height change {lift_max:+.1f} m "
             f"(bucket pin at height z = {start.z + lift_max:.2f} m)")

# ---------- 6. Twist test: three ways to swing; which keeps the bucket in line? ----------
lift_test = min(1.6, lift_max - 0.2)
old_mix = cr.mix_mode
lines.append("")
lines.append("Twist test: how far the bucket turns against the stick (deg)")
lines.append("  A = as now, sphere not turned;  B = sphere turned with the swing;  "
             "C = mix set to 'AFTER', sphere not turned")
for name, d_reach, d_height, curl in (("rest pose, curl 0 ", 0, 0, 0),
                                       ("lift pose, curl 60", -0.5, lift_test, 60)):
    for swing in (45, 90):
        result = []
        for mix, spin in ((old_mix, 0), (old_mix, swing), ("AFTER", 0)):
            cr.mix_mode = mix
            set_sphere(place(d_reach, d_height), curl, 0)
            reference = measure()[1]
            set_sphere(place(d_reach, d_height, swing), curl, spin)
            result.append(angle_between(reference, measure()[1]))
        cr.mix_mode = old_mix
        lines.append(f"  {name}, swing {swing}: A {result[0]:5.1f} | B {result[1]:5.1f} | C {result[2]:5.1f}")

# Does mix 'AFTER' change how the bucket looks at rest?
set_sphere(start)
look_now = measure()[1]
cr.mix_mode = "AFTER"
look_after = measure()[1]
cr.mix_mode = old_mix
lines.append(f"  At rest, 'AFTER' turns the bucket by {angle_between(look_now, look_after):.1f} deg "
             "(0 = it looks the same)")

# ---------- 7. Back to rest, and write the report ----------
set_sphere(start)
measure()
text = bpy.data.texts.get("rig_check_2") or bpy.data.texts.new("rig_check_2")
text.clear()
text.write("\n".join(lines))
