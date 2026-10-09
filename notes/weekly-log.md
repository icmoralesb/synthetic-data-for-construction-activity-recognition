# Weekly log — Research Track 2027

Newest week on top. One entry per week, written on Sunday (10–15 minutes).
Keep personal and legal matters out of this file: the repository is public.

---

## Week 2 · Mon 05 oct - Sun 11-oct-26

**Hours:** planned 16 · done 24

**Done**
- 

**Results (numbers)**
- 

**What I learned**
- Using cross-entropy formulation, we can reach faster the global minimum of the cost function.
- How transfer learning works. A big computer vision model, like YOLO, can be enhanced with additional knowledge on top with less computational effort.
- Automated recognition of construction workers and machinery has been deployed using different methods grouped in: kinematic-based methods, audio-based methods and vision-based methods.
- One of the biggest gap to develop vision-based methods is the lack of data: images and videos. Additional the dataset used to train visual-based methods are under controlled conditions.

**Problems / blockers**
- 

**Decisions (and why)**
- 

**Next week: top 3**
1. 
2. 
3. 

---

## Week 1 · Thu 01 Oct – Sun 04 Oct

**Hours:** planned 10 · done 18

**Done**
- Phase 0: repository on GitHub (README, pretrained demo notebook, requirements, MIT licence).
- Environment: Miniforge, PyTorch with MPS (GPU confirmed), Ultralytics.
- Dataset: Excavators (Roboflow v3, CC BY 4.0) documented in DATASETS.md.
- First training run: YOLOv8s, 5 epochs, on MPS.
- Evaluation on the validation split; sample predictions; EXPERIMENTS.md entry.
- Plan v2: theory track rebuilt on one book (Understanding Deep Learning).
- Readings: 

**Results (numbers)**
- YOLOv8s, 5 epochs, validation: mAP50 0.863, mAP50-95 0.630, P 0.945, R 0.737.

**What I learned**
- Working method in environments: using Miniforge you can create an environment dedicated to your laboratory tests. Packages and programs are installed without interact with the default MAC set up
- How to start my own repository account in Git Hub.

**Problems / blockers**
- New terminology and new methologies.

**Decisions (and why)**
- Blender for the synthetic pipeline (free, constantly updated).
- One theory book only: mixed books and notation were slowing me down.
- Email Prof. Álvarez after Phase 1, with working results to show.

**Next week: top 3**
1. First transfer learning process based on excators, dump trucks and wheel loaders detection.
2. Fully understand training deep learning networks including: regularization, backpropagation and stochastic gradient descent.
3. 
