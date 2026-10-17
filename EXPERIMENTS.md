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
