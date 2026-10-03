# Synthetic-to-Real Construction Activity Recognition

**Can synthetic video teach a model to recognise what an excavator is doing on a real construction site?**

> **Status:** Phase 0 — repository set-up and pretrained-pipeline sanity check.
> Phase 1 (excavator detector, local training) is next.

---

## Motivation

*(This is the first-person story that appears in my scholarship and supervisor
outreach letters. The details below are true and are mine to tell.)*

For more than ten years I worked in project control and cost engineering on
major road-infrastructure projects in Colombia, including the Toyo and La
Línea tunnels. Idle machinery and unrecorded labour were measured mostly by
manual reports — slow, incomplete and hard to audit. This project is my
attempt to replace that manual process with an objective, video-based record
of what machines and workers are actually doing, so productivity control and
public-works transparency can rest on evidence instead of paperwork.

---

## Research questions

1. Can action-recognition models trained mainly on synthetic, automatically
   labelled video recognise excavator activities in **real** site footage?
2. How much real labelled video can synthetic video replace while keeping
   accuracy on real sites?
3. Which synthetic factors — lighting, weather, camera viewpoint, background,
   photorealism — reduce the synthetic-to-real gap the most?
4. *(Exploratory)* Can generative video models add useful variation by
   synthesising transitions between two keyframes?

---

## Scope

The first version studies **one machine — the excavator — and five
activities**: digging, swinging, dumping, travelling and idle. Workers and
other machines follow once this pipeline is proven.

---

## Pipeline

```
Scenario design  →  Synthetic clips   →  Train models   →  Real-site test
(Blender rig +      (labels made          (video action       (sim-to-real
 scripted acts)       free by engine)      models)              gap)
        ↑                                       ↑                    │
        └──────────── adjust randomisation & realism ────────────────┘
```

A small real labelled test set is mixed in during training to measure how
much real data the synthetic clips can replace.

---

## Method

- **Baseline (this repo's current stage):** YOLO detection + ByteTrack
  tracking, with simple motion rules to flag active vs. idle. This is the
  foundation the Phase 1 excavator detector builds on.
- **Main models (from Phase 5):** SlowFast, X3D and VideoMAE, pre-trained on
  Kinetics and fine-tuned on synthetic excavator clips.
- **Synthetic pipeline (Phase 3):** site scenes built in Blender with a rigged
  excavator model and scripted activities; lighting, weather, camera angle and
  background randomised; bounding boxes and per-frame activity labels exported
  automatically — no manual labelling.
- **Evaluation (Phase 4–5):** a small real test set (100–150 excavator clips,
  labelled in CVAT) from public construction video. Train with increasing
  shares of real data and measure frame- and video-level mean Average
  Precision, per activity.

---

## Data

| Stage | Data | Status |
|---|---|---|
| Phase 0 (this commit) | Pretrained COCO model, public sample image | Done |
| Phase 1 | Public construction images (SODA, MOCS) — to ground an excavator detector before any synthetic data exists | Next |
| Phase 3 | Synthetic excavator clips, generated in Blender | Planned |
| Phase 4 | 100–150 real excavator clips, labelled in CVAT | Planned |

All datasets are public, or generated synthetically. No real footage filmed
by me is used without consent; identifiable individuals are avoided and faces
are blurred where relevant.

---

## Compute

Local development on a MacBook Pro (M4 Pro) via PyTorch MPS / Metal
Performance Shaders; free Google Colab / Kaggle GPUs for heavier training.

---

## How to run this notebook

1. Open `notebooks/01_pretrained_demo.ipynb` in Google Colab:
   [Open in Colab](https://colab.research.google.com/github/icmoralesb/synthetic-data-for-construction-activity-recognition/blob/main/notebooks/01_pretrained_demo.ipynb)
2. Set the runtime to GPU (*Runtime → Change runtime type → T4 GPU*).
3. Runtime → Run all. It installs Ultralytics, loads a pretrained model, and
   runs detection on a sample image and on a construction photo you upload.

Local install:

```bash
pip install -r requirements.txt
```

---

## Roadmap

- [x] **Phase 0** — repo + pretrained-pipeline sanity check *(this commit)*
- [ ] **Phase 1** (2–12 Oct 2026) — foundations + excavator detector, local training, tracking, active/idle demo
- [ ] **Phase 2** (8–28 Oct 2026) — literature review + novelty check
- [ ] **Phase 3** (15–29 Oct 2026) — synthetic pipeline in Blender (~2,000 clips)
- [ ] **Phase 4** (1–8 Nov 2026) — real test set: 100–150 excavator clips labelled in CVAT
- [ ] **Phase 5** (12–19 Nov 2026) — experiments and ablations (synthetic-only, real-only, mixed ratios)
- [ ] **Phase 6** (20 Nov – 10 Dec 2026) — paper writing (6–8 pages, LaTeX)
- [ ] **★ Repository citable** (3 Dec 2026) — release v1.0: generator, dataset sample, results
- [ ] **★ arXiv preprint submitted** (13 Dec 2026, buffer to 10 Jan 2027)

---

## Author

Iván Camilo Morales Buitrago — civil / cost engineer moving into applied
computer vision for construction, applying for a research master's at the
University of Technology Sydney.
GitHub: [@icmoralesb](https://github.com/icmoralesb)

## Licence

MIT — see [LICENSE](LICENSE).
