# Excavator 3D model — source and licence

**Title:** Excavator
**Author:** kurtismedia (Sketchfab)
**Source:** https://sketchfab.com/3d-models/excavator-f2a569f2a2f64a079cc353fa4d4a74f1
**Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0) — https://creativecommons.org/licenses/by/4.0/
**Licence text:** LICENSE-CC-BY-4.0.txt (in this folder)
**Downloaded:** 2026-10-22, original format (.blend)
**NoAI tag:** none on the model page on 2026-10-22
**Model file:** not stored in Git (size); download it from the source link above.

## Attribution line (use it in the README, the dataset and the paper)

"Excavator" by kurtismedia (https://sketchfab.com/3d-models/excavator-f2a569f2a2f64a079cc353fa4d4a74f1), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Modified for this project: rigged and animated in Blender to generate synthetic training video.

## Changes made in this project

- (add one line per change, with the date — for example: "2026-10-22: added a cab-swing bone")

## Parts check (fill in after opening the file in Blender 4.2.1)

| Part | Separate object or bone? | Pivot at the real joint? | Notes |
|---|---|---|---|
| Upper structure (cab) — swing | Bone | Yes | |
| Boom | Bone | Yes | |
| Stick (arm) | Bone | Yes | |
| Bucket | Bone | Yes | |
| Tracks — travel | Bone | Yes | |
| Hydraulic cylinders follow the joints | Bone | Yes | |

- **Height at the cab (N panel → Item → Dimensions):** ____ m (a 20-tonne excavator is about 3 m)
- **Triangles (Overlays → Statistics):** ____ (the Sketchfab page says about 667,000)
- **Decision:** keep / replace with the fallback model

## Control map

| Activity | Control to move | How |
|---|---|---|
| Dig | Sphere + CO: Bucket | Sphere down and towards the cab; rotate CO: Bucket to curl the bucket |
| Swing | Sphere | Along a circle around the cab; the cab follows on its own |
| Dump | Sphere + CO: Bucket | Sphere up and out; rotate CO: Bucket to open the bucket |
| Travel | CO: Master Movement | Move the whole machine |
| Idle | None | Nothing moves |

Swing is automatic: Pivot Main follows the sphere trhough a constraint. Do not totate it by hand.
