## 07-nov-26 - First synthetic clip: dig and swing in Blender (test 3)

**Question**
Can the Blender generator produce one dig and one loaded swing that a real excavator could perform, with an activity label in every frame?

**Expected**
- The bucket pin reaches its target at every frame.
- Every joint stays inside the machine's physical limits (hydraulic cylinder strokes, bucket range against the stick).
- The full bucket keeps its tip line (bucket pin to teeth tip) level during the lift and the swing.
- Labels: dig, then swing.

**Setup**
- Model: "Excavator" by kurtismedia (Sketchfab), CC BY 4.0; the file is not stored in this repository (see `assets/excavator/SOURCE.md`).
- Blender 4.2, Eevee Next renderer, 640 x 360 pixels.
- Scripts: `scripts/blender/dig_swing.py` (test 3), `render_gif.py` (version 3), `make_gif_labels.py`.
- Device: Apple M4 Pro.

**Settings**
- Seed 1, 25 frames per second. Phase durations drawn at random: reach 1.5-2.5 s, lower 1.0-2.0 s, fill 2.0-4.0 s, curl 0.6-1.2 s, lift 1.5-3.0 s, swing 3.0-6.0 s.
- Phase ends (reach change in m, height change in m, bucket curl in degrees from rest): reach (5.0, 2.1, -76), lower (4.6, 0.25, -113), fill (3.3, -0.35, -96), curl (3.0, 0.2, -63), lift (1.25, 2.75, -70); then a 90-degree swing to the left.
- Limits measured from the model: bucket curl from -146 degrees (bucket cylinder fully closed) to +22.75 degrees (the bucket's back touches the stick), used with a 5-degree margin; cylinder strokes from the barrel and rod meshes, with at least 0.15 m of rod inside the barrel and 0.05 m from the barrel bottom.
- Pit 4.3-10.4 m in front of the swing axis, 2.6 m wide, 1.2 m deep; the bucket may cut 0.30 m into the pit floor.
- Rendered every second frame: 180 pictures; GIF at 12.5 pictures per second.

**Results** (from `data/renders/dig_swing_report.txt`: "RESULT: all checks passed")

| Check (every frame) | Result | Allowed |
|---|---|---|
| Bucket pin against its target | largest gap 0.0 cm | under 2 cm |
| Bucket curl from rest | -112.9 to 0.0 degrees | -141.0 to +17.8 degrees |
| Boom cylinder length | 2.50-3.43 m | 2.46-3.99 m |
| Stick cylinder length | 3.33-4.52 m | 2.94-5.00 m |
| Bucket cylinder length | 2.76-3.54 m | 2.41-3.98 m |
| Bucket links folded to the wrong side | 0 frames | 0 |
| Bucket clearance to the ground or pit floor | 0.04 m (frame 176) | above 0 |
| Stick clearance to the ground or pit floor | 0.32 m (frame 1) | above 0 |
| Tip line during the lift and swing (frames 195-360) | at most +2.1 degrees from level | 5 degrees |
| Bucket twist against the stick during the swing | 0.5 degrees | under 3 degrees |

- Durations: dig 10.00 s (reach 1.64, lower 1.84, fill 3.52, curl 0.76, lift 2.24 s); swing 90 degrees in 4.36 s (average 20.6 degrees/s, top 32.4 degrees/s).
- Labels: dig = frames 1-251 (0.00-10.04 s); swing = frames 252-360 (10.04-14.40 s).

**Observations**
- In the 180 pictures the bucket digs into the pit, closes until its tip line is level, lifts out and swings; no part passes through another, and the machine stays inside the picture.

**History: tests 1 and 2**
- Test 1: the lift target was inside the arm's inner reach limit (boom length minus stick length = 3.74 m; the target was 3.32 m from the boom foot), so the bucket pin missed it by 42 cm. A 90-degree swing also twisted the bucket 32.8 degrees against the stick; setting the bucket's Copy Rotation mix to "After Original" (in memory only) removed the twist (0.0 degrees, `rig_check_2.py`, 3 Nov).
- Test 2 (3-4 Nov): every check passed, but the preview pictures showed the bucket passing through the stick. The curl values (+30 and +60 degrees) were measured from the rest pose, which is the transport pose with the bucket almost fully closed: only +22.75 degrees of closing were left. At frame 42 the bucket pin was 1.0 m under a flat ground, so only the teeth showed. Lesson: test 2 checked that the rig did what we asked, not that what we asked was physically possible.
- Test 3 changes: limits measured from the model and checked at every frame; a pit; a separate curl phase; and the carry rule from site practice (tip line level, so wet material does not spill). A carry with level teeth was designed first and rejected after review, because the opening would still lean 43 degrees towards the machine.

**Interpretation**
- Answer: yes, for one dig and one swing. Every frame passed the physical checks, and the labels come from the script, not from a person.
- The closest margin is the bucket's cut into the pit floor at the end of the fill (0.26 m of the 0.30 m allowed). Other seeds change only the speed, not the path, so this margin stays the same.

**Limitations**
- One machine, one camera, one seed, two activities; the bucket is empty (no soil model); no bounding boxes or masks yet; the far edge of the ground shows at the top right.
- The limits come from the model's own geometry, which may differ from a real excavator of the same size.

**Next steps**
- Export bounding boxes and masks for every frame.
- Randomise camera, lighting, weather and background.
- Add the dump, travel and idle activities, then render the first batch of clips.


## 14-oct-26 - Active vs. idle from tracked-box movement

**Question**
On a fixed-camera clip, does the motion rule (τ = 0.02, minimum durations 1.5 s active and 2.0 s idle) label the state of an excavator (active or idle) correctly over time?

**Expected**
- The detector finds the excavator in every frame.
- The excavator keeps one track ID for the whole clip.
- The rule labels the whole clip as active, because the excavator works without stopping.

**Setup**
- Model: best.pt (experiment 06-oct-26), 5 epochs
- Tracker: ByteTrack, `conf=0.1`
- Video: 161126-822582239_medium.mp4
	- Duration: 23.6 s (589 frames)
	- Resolution: 3840 x 2160
	- Frame rate: 25 frames per second
	- Camera: fixed
	- Link: https://pixabay.com/videos/excavator-building-hall-work-161126/
	- Published date: 1-may-23
	- License: Pixabay Content License (not CC0: content uploaded to Pixabay after 9 January 2019 is under Pixabay's own licence)
- Device: Apple M4 Pro (MPS)

**Settings**
- Script: active_idle_B.py
- Tau (τ): 0.02 (threshold on the motion score)
- Minimum durations: active 1.5 s, idle 2.0 s

**Observations**
- One real excavator, fixed camera.
- The excavator was tracked in all 589 frames: no gaps, no class flicker.
- Duplicate box: ID 2 appeared on the same excavator in the first 13 frames (0 to 12, which is 0.5 s); after that only ID 1 remained, until the last frame (588).
- The excavator worked during the whole clip and never stopped for more than a moment.

**Results**
- Segments: one active segment from 0.5 s to 23.6 s (23.1 s). Idle: 0 s (0%).
- The first 0.5 s has no score, because the rule needs half a second of history before it can compare positions.
- Motion score: from 0.002 to 0.186 (median 0.049).
- Main peaks: 2.7 s (0.13), 9.2 s (0.19, the highest), and three similar peaks at 18.4, 20.6 and 22.0 s (about 0.13).
- Main lows: 5.2 s (0.014), 11.2 s (0.008) and 16.0 s (0.002, the lowest).
- The score fell below τ four times:

| Dip | Time         | Duration | Lowest score |
|-----|--------------|----------|--------------|
| 1   | 5.0–5.4 s    | 0.3 s    | 0.014        |
| 2   | 11.1–11.3 s  | 0.2 s    | 0.008        |
| 3   | 15.5–16.8 s  | 1.2 s    | 0.002        |
| 4   | 21.2–21.4 s  | 0.2 s    | 0.016        |

  All four dips are shorter than the 2.0 s minimum idle duration, so the rule kept them as active.

- Box changes (ID 1, from B_tracks.csv, smoothed over 0.5 s):

| Period         | Box width                   | Box centre (x)            | Box height              |
|----------------|-----------------------------|---------------------------|-------------------------|
| 0 to 7 s       | about the same (940–1000 px) | about the same            | 513 → 737 px (taller)   |
| 7 to 11 s      | 940 → 546 px (narrower)     | about 160 px to the left  | 737 → 476 px (shorter)  |
| 11 to 16.8 s   | about the same (505–563 px) | about the same            | 476 → 571 px            |
| 16.8 to 23.6 s | 510 → 929 px (wider)        | about 170 px to the right | 571 → 801 px (taller)   |

**Interpretation**
- Answer to the question: partly yes. For active time the rule worked: there was no false idle on a clip where the excavator never stops. Idle detection was not tested, because the clip has no idle period.
- Expected 1 was met: the excavator was detected in all 589 frames.
- Expected 2 was partly met: the main track kept one ID (ID 1) for the whole clip, but the detector drew a second box (ID 2) on the same excavator for the first 0.5 s. The same happened on 09-oct-26, so it is a pattern, not chance.
- Expected 3 was met: the whole clip was labelled active.
- The four dips were short slow moments, not pauses. The minimum idle duration did what it was designed to do: it stopped short slow moments from becoming idle periods.
- The motion score measures how much the box changes, not in which direction. A rising score means faster movement and a falling score means slower movement; the score alone cannot tell opening the arm from closing it, or digging from dumping.
- Hypothesis (from the box changes; not yet checked in the video): the clip shows one work cycle.
	- 0 to 7 s: digging and lifting the bucket (the box grows taller while its width and centre stay about the same).
	- 7 to 11 s: swing (the box becomes narrower and moves left; this is the fastest change in the clip, which is why the highest score is at 9.2 s).
	- 11 to 16.8 s: dumping, then a short pause (the box hardly changes; the score is nearly zero at 16.0 s).
	- 16.8 to 23.6 s: swing back (the reverse of 7 to 11 s: the box becomes wider and moves right).

**Limitations**
- The clip is short (23.6 s) and the excavator never stops, so idle detection could not be tested and τ could not be calibrated, because calibration needs examples of both states.
- One clip, one machine, one camera view.

**Next steps**
- Watch the video at 0–7 s, 7–11 s, 11–16.8 s and 16.8–23.6 s, write what is seen under Observations, then keep or correct the hypothesis.
- Rerun on a fixed-camera clip of 1 to 3 minutes with at least one idle period of several seconds, then calibrate τ.
- Duplicate-box test (open since 09-oct-26): rerun with `conf=0.25` and with the 50-epoch detector. Does the second box disappear?


## 09-oct-26 - Excavator video tracked with ByteTrack

**Setup**
- Model: best.pt (experiment 06-oct-26), 5 epochs
- Tracker: ByteTrack,`conf=0.1`
- Video: 15106480_1920_1080_50fps.mp4 (pexel.com), 00:00:25
- Device: Apple M4 Pro (MPS)

**Observations**
- One real excavator, continuously detected for the whole clip (no gaps, no class flicker).
- ID switch: the excavator was id=1 from 0:00 to 0:14, then a second box (id=14) appeared from 0:14 to 0:19, and from 0:19 only id=14 remained. A machine-hours system would count two machines.
- Cause to verify: duplicate box on the same excavator. Track IDs reached 14, which suggests many short-lived tracks, probably from low-confidence boxes (conf=0.1).
- Inference: 2.2 ms per frame on MPS.

**Next step**
- Rerun with conf=0.25 and compare: does the ID switch disappear?
- Repeat the test with the 50-epoch detector, since a stronger detector gives the tracker cleaner boxes.
- If the switch remains, tune ByteTrack (track_buffer, match_thresh). 


## 06-oct-26 - Evaluation of YOLOv8s, 5 epochs

**Setup**
- Model: YOLOv8s (pretrained on COCO), run `excavator_v8s_e5`, weights `best.pt`.
- Data: Excavators (Roboflow, v3, CC BY 4.0), validation split (267 images).
- Device: Apple M4 Pro (MPS).

**Results**

| Class        | Instances | P     | R     | mAP50 | mAP50-95 |
|--------------|-----------|-------|-------|-------|----------|
| all          | 426       | 0.945 | 0.737 | 0.863 | 0.630    |
| EXCAVATORS   | 36        | 0.884 | 0.694 | 0.797 | 0.532    |
| dump truck   | 212       | 0.971 | 0.622 | 0.832 | 0.630    |
| wheel loader | 178       | 0.980 | 0.893 | 0.959 | 0.727    |

**Observations**
- Precision (0.945) is much higher than recall (0.737): at its balanced threshold the model rarely gives false alarms but misses about a quarter of the machines. Dump truck has the lowest recall (0.622).
- EXCAVATORS has the lowest mAP50 (0.797), but only 36 validation instances, so this estimate is noisy. The target class of the project is the minority class in this dataset.
- Confusion matrix at the default val threshold (conf = 0.001): 52% of real excavators (19/36), 33% of dump trucks and 26% of wheel loaders were correctly classified, with thousands of background false positives. Probably caused by low-confidence boxes, since mAP50 (0.863) shows the confident predictions are mostly correct.

**Next step**
- Count instances per class in the training split.
- Retrain with identical settings except epochs = 50 and patience = 15, then compare with this run.
