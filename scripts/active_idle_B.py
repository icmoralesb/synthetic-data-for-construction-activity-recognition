"""
Phase 1 — active versus idle from the tracked box (rule-based baseline).

Idea in one line: if the excavator's box moves more than a small threshold for at least 1.5 seconds,
the machine is active; if it stays still for at least 2 seconds, it is idle.

Run it from the repository root, inside your conda environment:
    python scripts/active_idle.py

Outputs (in outputs/active_idle/):
    tracks.csv     one row per frame and tracked object (centre, width, height of the box)
    segments.csv   the active and idle periods of the main excavator
    timeline.png   motion score over time, threshold line and idle periods shaded
"""
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------
WEIGHTS = "/Users/icamobu/Downloads/Master_Scholarship/5_Protfolio_CV/data/excavators-roboflow/runs/detect/runs/excavator_v8s_e5/weights/best.pt"  # trained detector
VIDEO = "/Users/icamobu/Downloads/Master_Scholarship/5_Protfolio_CV/data/videos/excavator_02.mp4"  # video 14-oct-26 (wheeled excavator
OUT = Path("outputs/active_idle")

TAU = 0.02                          # threshold: box motion in half a second, as a fraction of the box diagonal
MIN_S = {True: 1.5, False: 2.0}     # minimum durations: an active burst 1.5 s, an idle pause 2 s
                                    # (longer than the 1 s that smoothing spreads a single glitch over)


# ---------------------------------------------------------------- step 1: track and record the boxes
def track_video(weights, video):
    """Run YOLO + ByteTrack and keep, for every frame, the box of every tracked object."""
    from ultralytics import YOLO  # imported here so steps 2-5 can be tested without a model

    model = YOLO(weights)
    rows = []
    for frame, r in enumerate(model.track(source=video, tracker="bytetrack.yaml", stream=True,
                                          persist=True, device="mps", verbose=False)):
        if r.boxes.id is None:            # nothing tracked in this frame
            continue
        ids = r.boxes.id.int().cpu().tolist()
        cls = r.boxes.cls.int().cpu().tolist()
        xywh = r.boxes.xywh.cpu().tolist()  # centre x, centre y, width, height, in pixels
        for tid, c, (cx, cy, w, h) in zip(ids, cls, xywh):
            rows.append((frame, tid, model.names[c], cx, cy, w, h))
    return pd.DataFrame(rows, columns=["frame", "id", "cls", "cx", "cy", "w", "h"])


# ---------------------------------------------------------------- step 2: one excavator, gaps filled
def main_track(tracks, fps):
    """Keep the longest excavator track; fill gaps shorter than one second by interpolation."""
    exc = tracks[tracks["cls"].str.contains("excavator", case=False)]
    pool = exc if len(exc) else tracks
    main_id = pool["id"].value_counts().idxmax()
    d = pool[pool["id"] == main_id].set_index("frame")[["cx", "cy", "w", "h"]].sort_index()
    d = d.reindex(range(d.index.min(), d.index.max() + 1))      # one row per frame, NaN where missing
    return main_id, d.interpolate(limit=int(fps), limit_area="inside")


# ---------------------------------------------------------------- step 3: the motion score
def motion_score(d, fps):
    """Smooth first (jitter cancels out), then compare positions half a second apart (motion adds up).
    The score is divided by the box diagonal, so it means the same for a near or a far excavator."""
    half = max(1, round(fps / 2))
    s = d.rolling(half, center=True, min_periods=1).mean()
    diag = np.sqrt(s["w"] ** 2 + s["h"] ** 2)
    change = s.diff(half).abs().sum(axis=1, min_count=4)        # |dcx| + |dcy| + |dw| + |dh|
    return change / diag


# ---------------------------------------------------------------- step 4: threshold and minimum durations
def runs(states, times, dt):
    """Group consecutive equal states into [state, start_s, end_s] segments."""
    segs, start = [], 0
    for i in range(1, len(states) + 1):
        if i == len(states) or states[i] != states[start]:
            segs.append([bool(states[start]), float(times[start]), float(times[i - 1] + dt)])
            start = i
    return segs


def clean(segs, min_s):
    """Flip the shortest too-short segment, merge it with its neighbours, repeat until none is left.
    This stops the timeline from flickering (the same idea as a thermostat)."""
    while len(segs) > 1:
        short = [k for k, (st, a, b) in enumerate(segs) if b - a < min_s[st]]
        if not short:
            break
        k = min(short, key=lambda k: segs[k][2] - segs[k][1])
        segs[k][0] = not segs[k][0]
        merged = [segs[0]]
        for st, a, b in segs[1:]:
            if st == merged[-1][0]:
                merged[-1][2] = b
            else:
                merged.append([st, a, b])
        segs = merged
    return segs


def classify(score, fps, tau, min_s):
    ok = score.notna()
    t = score.index[ok].to_numpy() / fps
    active = (score[ok] > tau).to_numpy()
    return clean(runs(active, t, 1 / fps), min_s)


# ---------------------------------------------------------------- step 5: timeline and summary
def plot(score, segs, fps, tau, path, title):
    t = score.index.to_numpy() / fps
    fig, ax = plt.subplots(figsize=(12, 3.6))
    ax.plot(t, score.to_numpy(), lw=1, label="motion score")
    ax.axhline(tau, ls="--", color="black", lw=1, label=f"threshold = {tau}")
    for st, a, b in segs:
        if not st:
            ax.axvspan(a, b, color="orange", alpha=0.25, lw=0)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("box motion in 0.5 s\n(fraction of box diagonal)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fps = cv2.VideoCapture(VIDEO).get(cv2.CAP_PROP_FPS) or 30.0
    tracks = track_video(WEIGHTS, VIDEO)
    tracks.to_csv(OUT / "tracks.csv", index=False)

    main_id, d = main_track(tracks, fps)
    score = motion_score(d, fps)
    segs = classify(score, fps, TAU, MIN_S)

    active_s = sum(b - a for st, a, b in segs if st)
    idle_s = sum(b - a for st, a, b in segs if not st)
    pd.DataFrame(segs, columns=["active", "start_s", "end_s"]).to_csv(OUT / "segments.csv", index=False)
    title = (f"Excavator id {main_id}: active {active_s / 60:.1f} min, idle {idle_s / 60:.1f} min "
             f"({100 * idle_s / max(active_s + idle_s, 1e-9):.0f}% idle) — orange = idle")
    plot(score, segs, fps, TAU, OUT / "timeline.png", title)
    print(f"fps {fps:.1f} | tracks {tracks['id'].nunique()} | main id {main_id}")
    print(title)
    print(f"saved {OUT / 'tracks.csv'}, {OUT / 'segments.csv'}, {OUT / 'timeline.png'}")


if __name__ == "__main__":
    main()
