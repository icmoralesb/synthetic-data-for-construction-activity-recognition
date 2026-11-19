# make_gif_labels.py - Put the activity label, the time and the model credit on every rendered picture (8 Nov 2026)
# Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0. The credit line is required by the licence.
# Run it outside Blender, with Python and Pillow, from the project folder:
#     python3 scripts/blender/make_gif_labels.py data/renders/gif_test3 data/renders/gif_labelled
# The first folder holds the frame_####.png pictures from render_gif.py; the second (made if missing) receives
# the labelled copies lab_0001.png, lab_0002.png, ...
# Which frames are "dig" and which are "swing" is read from data/renders/dig_swing_report.txt (its "Labels" lines),
# so the labels always match the animation that was rendered.
# Then make the GIF and the MP4 with ffmpeg (12.5 pictures per second = every second frame of 25 fps):
#     cd data/renders/gif_labelled
#     ffmpeg -framerate 12.5 -i lab_%04d.png -vf "split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a" -loop 0 dig_swing.gif
#     ffmpeg -framerate 12.5 -i lab_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart dig_swing.mp4
# Safety: no internet; it only reads the pictures and the report, and writes new labelled copies.

import glob
import os
import sys
from PIL import Image, ImageDraw, ImageFont

FPS = 25
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "..", "data", "renders", "dig_swing_report.txt")
COLOURS = {"dig": (214, 120, 20), "swing": (30, 100, 180)}


def font(size, bold):
    """A clear sans-serif font on Linux or macOS; Pillow's own font if neither is found."""
    names = (["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "Arial Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else
             ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "Arial.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def read_labels(path):
    """The (activity, first frame, last frame) lines under 'activity,first_frame,...' in the report."""
    labels, inside = [], False
    for line in open(path):
        line = line.strip()
        if line.startswith("activity,first_frame"):
            inside = True
            continue
        if inside:
            parts = line.split(",")
            if len(parts) < 3:
                break
            labels.append((parts[0], int(parts[1]), int(parts[2])))
    if not labels:
        raise RuntimeError(f"No label lines found in {path}: run dig_swing.py first.")
    return labels


src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
labels = read_labels(REPORT)
big, small, tiny = font(22, True), font(13, False), font(10, False)
files = sorted(glob.glob(os.path.join(src, "frame_*.png")))
for i, fpath in enumerate(files, 1):
    f = int(os.path.basename(fpath)[6:10])
    act = next(a for a, first, last in labels if first <= f <= last)
    col = COLOURS.get(act, (60, 60, 60))
    im = Image.open(fpath).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([10, 10, 200, 64], radius=8, fill=(255, 255, 255, 225))
    d.rectangle([10, 10, 18, 64], fill=col)
    d.text((28, 14), act.upper(), font=big, fill=col)
    d.text((28, 42), f"t = {(f - 1) / FPS:5.2f} s   frame {f}", font=small, fill=(40, 40, 40))
    d.rectangle([0, im.height - 20, im.width, im.height], fill=(255, 255, 255, 200))
    d.text((8, im.height - 16), 'Synthetic video made in Blender. Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0, modified.',
           font=tiny, fill=(50, 50, 50))
    im.save(os.path.join(out, f"lab_{i:04d}.png"))
print(len(files), "frames labelled:", ", ".join(f"{a} {first}-{last}" for a, first, last in labels))
