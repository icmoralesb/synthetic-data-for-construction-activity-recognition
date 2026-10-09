## 2026-10-09 - Excavator video tracked with ByteTrack

**Setup**
- Model: best.pt (experiment 2026-10-06), 5-epochs
- Tracker: ByteTrack,`conf=0.1`
- Video link: https://www.pexels.com/video/excavator-in-action-at-construction-site-35647503/
- Video: 15106480_1920_1080_50fps.mp4, 00:00:25

**Observations**
Video tracking of one (01) active excavator which is moving material from one side to another. The length of the video is 25 seconds with 1272 frames. The model detected:

- 0:00 to 0:14 : (01) excavators detected, id=1.
- 0:14 to 0:19 : (02) excavators detected, id=1, id=14.
- 0:19 to 0:25 : (01) excavators detected, id=14.

As we can see, the model detected one adittional machine during 2 seconds with 2 different id's. Moreover, the model never lost the track and zero class flicker. Time processing: 2.2ms per frame. 
 


## 2026-10-06 - Evaluation of YOLOv8s, 5 epochs

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


