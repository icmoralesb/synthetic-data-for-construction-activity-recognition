## 2026-10-06 - Evaluation of YOLOv8s, 5 epochs

**Setup**
- Model: YOLOv8s (pretrained on COCO), run 'excavator_v8s_e5', weights 'best.pt'
- Data: Excavators (Roboflow, v3, CC BY 4.0), validation split (267 images)
- Device: Apple M4 Pro (MPS)

**Results**

| Class        | Instances | P     | R     | mAP50 | mAP50-95 |
|--------------|-----------|-------|-------|-------|----------|
| all          | 426       | 0.945 | 0.737 | 0.863 | 0.630    |
| EXCAVATORS   | 36        | 0.884 | 0.694 | 0.797 | 0.532    |
| dump truck   | 212       | 0.971 | 0.622 | 0.832 | 0.630    |
| wheel loader | 178       | 0.980 | 0.893 | 0.959 | 0.727    |

**Observations**
- EXACAVATOR class is the weakest one, with 36 instances.
- Confusion matrix (default val threshold): the model finds almost every machine but the class is close to random. EXCAVATOR class predicted 52%, dump truck class predicted 33% and wheel loader 26% of the instances. On background thousands of false positives. Basically the model found the machines but guessing which machine it is. This behavior is largely due to low-confidence boxes (conf=0.001). On the other hand the mAP50=0.863 tell us that the model learnt machines with good results. 
- Results of evaluation in detect mode show us that model learnt very well even though the training procedure was carried out over 5 epochs. Prediction over 84% and 4% of incorrectly labeling.

**Next step**
- Train longer with al least 50 epochs.
