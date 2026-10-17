# Synthetic-to-Real Construction Activity Recognition

**Can synthetic video teach a model to recognise what an excavator is doing on a real construction site?**

> **Status:** Phase 1 complete (tag `v0.1-phase1`): excavator detector,
> ByteTrack tracking and a rule-based active/idle demo.
> Next: Phase 3, the synthetic video pipeline in Blender.

---

## Motivation

For more than ten years I worked in project control and cost engineering on
major road-infrastructure projects in Colombia, including the Toyo and La
Línea tunnels. Idle machinery and unrecorded labour were measured mostly by
manual reports — slow, incomplete and hard to audit. This project is my
attempt to replace that manual process with an objective, video-based record
of what machines and workers are actually doing, so productivity control and
public-works transparency can rest on evidence instead of paperwork.

---

## Research questions

The December 2026 preprint answers questions 1 and 2 and gives a first answer
to question 4. Question 5 belongs to the thesis stage.

1. **Transfer.** Can video models trained mainly on Blender-generated,
   automatically labelled clips recognise five excavator activities in real
   site footage, and where do they fail?
2. **Real-data savings.** Under a fixed training budget, how does accuracy on
   real footage change when real clips replace synthetic ones, and how many
   real labelled clips does a large synthetic set save?
3. **What closes the gap.** Which generation factors matter most: domain
   randomisation (viewpoint, lighting, weather, background, distractors) or
   generative realism enhancement of the rendered clips?
4. **Specialist or generalist.** On the same real test set, how does the
   synthetic-trained model compare with a zero-shot vision-language model, and
   with a pre-trained video model fine-tuned on real clips only, in accuracy,
   speed and cost?
5. **Activities as crews (thesis stage).** Does modelling an operation as
   interacting resources, starting with an excavator and the trucks it loads,
   recognise operation states better than separate machine models?

---

## Scope

The first version studies **one hydraulic excavator and five activities**:
digging, swinging, dumping, travelling and idle. The trucks it loads follow in
the thesis, and workers and materials later.

---

## Pipeline

```
Scenario design  →  Synthetic clips   →  Train models   →  Real-site test
(Blender rig +      (labels made          (video action       (sim-to-real
 scripted acts)       free by engine)      models)              gap)
        ↑                                       ↑                    │
        └──────────── adjust randomisation & realism ────────────────┘
```

Synthetic clips and a pool of real training clips are mixed under a fixed
training budget. Every model is scored on the same held-out real test set.

---

## Method

- **Baseline (Phase 1, done):** YOLOv8s excavator detector, ByteTrack
  tracking, and a motion rule that labels each moment as active or idle.
- **Synthetic generator (Phase 3):** site scenes built in Blender with a
  rigged excavator performing scripted work cycles. BlenderProc renders the
  clips and exports per-frame labels (activity, bounding box, mask, joint
  angles), so no manual labelling is needed. Camera viewpoint, lighting,
  weather, terrain, background, motion blur and video compression are
  randomised per clip. Target: about 2,000 clips of 2 to 4 seconds.
- **Realism enhancement (research question 3):** a structure-conditioned
  diffusion model (ControlNet approach) refines rendered frames while keeping
  their labels.
- **Recognition models (Phase 5):** X3D and VideoMAE, pre-trained on Kinetics
  and fine-tuned on tracked excavator clips.
- **Comparison models (research question 4):** a zero-shot vision-language
  model run locally (for example Qwen2.5-VL), and a VideoMAE model fine-tuned
  on real clips only.
- **Evaluation:** one held-out real test set, split by source video. Macro-F1
  over the five activities is the main metric. Every configuration runs with
  at least three random seeds, reported as mean ± standard deviation, with 95%
  bootstrap confidence intervals that resample whole source videos.

---

## Data

| Phase | Data | Status |
|---|---|---|
| Phase 0 | Pretrained COCO model, public sample image | Done |
| Phase 1 | Excavators dataset (Roboflow Universe, version 3, CC BY 4.0), three classes: excavator, dump truck, wheel loader. Two public test videos (Pexels, Pixabay) for tracking and the active/idle rule | Done |
| Phase 3 | About 2,000 synthetic excavator clips (2 to 4 s), generated in Blender | Planned |
| Phase 4 | About 800 real clips (2 to 4 s) cut from at least 45 minutes of public video from 20 or more sources; activity start and end times labelled by hand; split by source video into about 400 test, 300 training-pool and 100 validation clips | Planned |

All data is public or synthetic. Real footage is used only when its licence
allows research use, or with site permission. Identifiable people are avoided
and faces are blurred where relevant. Video sources are listed in
[EXPERIMENTS.md](EXPERIMENTS.md).

---

## Phase 1 results

Full settings and observations for every run are in
[EXPERIMENTS.md](EXPERIMENTS.md).

**1. Excavator detector (6 Oct 2026).** YOLOv8s pretrained on COCO,
fine-tuned for 5 epochs; validation split of 267 images.

| Class | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|
| all | 426 | 0.945 | 0.737 | 0.863 | 0.630 |
| EXCAVATORS | 36 | 0.884 | 0.694 | 0.797 | 0.532 |
| dump truck | 212 | 0.971 | 0.622 | 0.832 | 0.630 |
| wheel loader | 178 | 0.980 | 0.893 | 0.959 | 0.727 |

The validation split holds only 36 excavator instances, so the excavator
scores are noisy.

**2. Tracking (9 Oct 2026).** ByteTrack on a 25-second public excavator
video. The excavator was detected in every frame with no class flicker, but a
duplicate box on the same machine created a second track ID for 5 seconds,
and the track then continued under the new ID. A machine-hours count would
have counted two machines.

**3. Active/idle rule (14 Oct 2026).** The motion score is the change in the
tracked box (centre, width and height) over half a second, divided by the box
diagonal. Threshold τ = 0.02; minimum durations 1.5 s active and 2.0 s idle.
On a 23.6-second fixed-camera clip of a working excavator, the rule labelled
all scored time as active, with no false idle. Idle detection is not tested
yet, because the clip has no idle period.

**Open issues**
- Retrain the detector for 50 epochs and compare with the 5-epoch run.
- Duplicate boxes appeared in both videos: test confidence 0.25 and the
  50-epoch detector.
- Calibrate τ on a longer fixed-camera clip that includes idle periods.

---

## Compute

Local development and training on a MacBook Pro (Apple M4 Pro) with PyTorch
MPS (Metal Performance Shaders); free Google Colab or Kaggle GPUs for heavier
training.

---

## How to run

**Phase 0 notebook (Google Colab)**

1. Open `notebooks/01_pretrained_demo.ipynb` in Google Colab:
   [Open in Colab](https://colab.research.google.com/github/icmoralesb/synthetic-data-for-construction-activity-recognition/blob/main/notebooks/01_pretrained_demo.ipynb)
2. Set the runtime to GPU (*Runtime → Change runtime type → T4 GPU*).
3. *Runtime → Run all*. It installs Ultralytics, loads a pretrained model, and
   runs detection on a sample image and on a construction photo you upload.

**Phase 1 (local)**

```bash
conda env create -f environment.yml
conda activate construction-cv
python scripts/active_idle_B.py
```

Set the paths to the trained weights and to the video at the top of
`scripts/active_idle_B.py`. Model weights and videos are not stored in this
repository, because of their size and licences. Without conda, install the
packages with `pip install -r requirements.txt`.

---

## Roadmap

- [x] **Phase 0** (1 Oct 2026) — repository and pretrained-pipeline sanity check
- [x] **Phase 1** (October 2026, tag `v0.1-phase1`) — excavator detector, tracking, active/idle demo
- [ ] **Phase 2** (8–28 Oct 2026) — literature review and novelty check
- [ ] **Phase 3** (15–29 Oct 2026) — synthetic pipeline in Blender (about 2,000 clips)
- [ ] **Phase 4** (1–8 Nov 2026) — real data: about 800 clips from long public videos
- [ ] **Phase 5** (9–19 Nov 2026) — experiments: synthetic only, real-data replacement and savings curves, zero-shot comparison
- [ ] **Phase 6** (20 Nov – 10 Dec 2026) — paper writing (6–8 pages, LaTeX)
- [ ] **★ Repository citable** (3 Dec 2026) — release v1.0: generator, dataset sample, results
- [ ] **★ arXiv preprint submitted** (13 Dec 2026, buffer to 10 Jan 2027)

---

## Use of AI tools

Parts of the code and documentation in this repository, including the Phase 0
notebook, were drafted with the help of an AI assistant (Claude, by
Anthropic). I ran every script and notebook myself, and all reported results
come from my own runs.

---

## Author

Iván Camilo Morales Buitrago — civil and cost engineer moving into applied
computer vision for construction, preparing a research master's application
for 2027.
GitHub: [@icmoralesb](https://github.com/icmoralesb)

## Licence

MIT — see [LICENSE](LICENSE).
