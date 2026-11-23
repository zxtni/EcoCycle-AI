# EcoCycle AI model card

## Photo scanner

The v3 runtime uses the same ONNX weights and suppresses duplicate boxes around the same object across scales. The optional **Search for small items** mode checks nine overlapping tiles on suitable images. A controlled three-bottle composite produced two localized plastic detections on standard mode and three on detailed mode. The composite uses different sizes of one held-out bottle photograph. Scores displayed in the interface are model confidence scores, with the highest scores shown as 99%+.

On the same 36 annotated TACO street photos, v2 found 2 correctly localized objects, v3 standard found 2, and v3 detailed found 3. These counts require the correct material and a box intersection-over-union of at least 0.50. Detailed mode emitted 10 boxes, of which 3 matched the annotations. This small sample illustrates the remaining gap on real street photos.

V3 standard mode scored **399/521 correct (76.6%)** on the published target-material holdout, with **431/521 (82.7%)** coverage. It returned a target label on 45 of 207 out-of-scope photos. The detailed mode has only the street and controlled composite results above. These results do not support a general accuracy improvement over the original runtime.

The v2 runtime uses the same ONNX weights with a second pass over four overlapping crops for larger photos with fewer than two accepted detections. A controlled regression scene assembled from a held-out plastic photo produced two separate detections in v2 and none in v1. This is a synthetic test of scale and position. The dataset metrics below are for v1. V2 performance on cluttered user photos remains unmeasured.

The scanner displays electronic objects as **Electronics**. A user must confirm that they are discarding the device for recycling before the app records e-waste. Small wearables and composite eyewear are outside the app’s validated item coverage.

The scanner helps a citizen log a recyclable they can photograph up close. The API runs both bundled ONNX networks on CPU. It returns a material, score and normalized box for each accepted item. A user reviews the result before logging weight.

### How it learned

Ultralytics YOLOv8n proposes regions containing familiar items such as bottles, tableware and electronic devices. When it finds no candidate, a border-color estimate can locate one isolated foreground object. The system passes each crop to Google's MobileNetV2. We froze its image features and fitted a class-balanced multinomial logistic regression layer to distinguish plastic, glass, metal, e-waste and an internal “other” class. The exported material network includes softmax. Its score describes the classifier's preference among training labels. Confidence calibration has not been measured. [YOLOv8](https://docs.ultralytics.com/models/yolov8/) · [MobileNetV2](https://huggingface.co/google/mobilenet_v2_1.0_224)

Training used 4,159 photographs and 7,061 views, counting full images and qualifying foreground crops. The source training sets contained 352 glass, 286 metal, 347 plastic, 2,393 electronics and 781 other images after cross-split byte-identical photographs were removed. Cardboard, paper and trash supplied negative examples. Electronic examples covered batteries, keyboards, mice, phones, circuit boards, players, printers, televisions, microwaves and washing machines. The published validation partition was kept separate. Training used the published training partitions only. Source partitions could still contain near-duplicates or views of the same item. No user photos or synthetic images were used to train this head. [TrashNet, Thung and Yang](https://github.com/garythung/trashnet) · [E Waste Image Dataset, Tamrakar](https://www.kaggle.com/datasets/akshat103/e-waste-image-dataset)

### Measured results

We ran the shipped scan function on the published test partitions. The end-to-end top-label accuracy across the four target materials was **400 / 521 = 76.8%**. Abstentions count as misses. Coverage was **423 / 521 = 81.2%**. The test included another 207 out-of-scope images, of which 186 were rejected and 21 received a target label. [Measured confusion counts](backend/vision_assets/metrics.json)

| Intended material | Test images | Top label correct | Abstained | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Glass | 82 | 60 | 10 | 73.2% |
| Metal | 68 | 41 | 21 | 60.3% |
| Plastic | 73 | 53 | 15 | 72.6% |
| E-waste | 298 | 246 | 52 | 82.6% |

We separately tested localization on **36 TACO street photographs**, selected before inference with seed 417. Each photograph contained one annotated target object. We sampled 12 images each for glass, metal and plastic. The scanner emitted four boxes. One had the correct material and intersection-over-union of at least 0.50, giving **25.0% precision and 2.8% recall** at the shipped threshold. IoU measures how much the predicted and annotated rectangles overlap. This small external test exposed poor sensitivity to small, scattered and obscured street litter. TACO contributed no training examples. We did not measure box accuracy on electronics because the electronic test photos have only image labels. [TACO](https://github.com/pedropro/TACO) · [Image-level reference boxes and predictions](backend/vision_assets/street_metrics.json)

### Intended use and limits

Frame one cleanly visible object against a contrasting background. YOLO can propose multiple objects when it recognizes them. The fallback supplies at most one region. Reflections, shadows, transparent objects, visually similar glass and plastic, and crowded scenes can mislead the classifier. Training backgrounds and the large share of electronics differ from the material mix in a real municipal collection. The scanner cannot identify resin codes, verify that electronics are broken, determine economic value from appearance, or prove that a user recycled something.

Tiny or blurry images return a retake state. Candidates with a material score below 0.62 and candidates labeled “other” are omitted. Some unsupported items can still receive confident scores. User corrections are stored for review. They do not update the model automatically.

### Reproduction

Use a separate Python 3.12 environment with the training dependencies. The first run downloads checksum-verified source archives and the original MobileNet conversion. Both shipped models already exist for normal app operation.

```sh
python -m pip install -r backend/vision_tools/requirements.txt
python -m backend.vision_tools.train ../ecocycle-model-cache
python -m backend.vision_tools.street_test ../ecocycle-model-cache
```

Training uses a frozen feature extractor, balanced classes, `C=0.35` and seed 417. The original split and download pins are in the trainer. The training script writes the material ONNX file, the measured counts and a correctly recognized held-out plastic photo for the interactive demo. The packaged example is `plastic103.jpg` from TrashNet. Selecting a successful example makes the demo repeatable. The evaluation above includes every eligible test image. [Training script](backend/vision_tools/train.py) · [Asset attribution and licenses](backend/vision_assets/NOTICE.md)

## Weekly hotspot forecast

Seasonal ridge regression uses 66,876 recorded Austin recycling loads aggregated into 286 weeks, then allocates them to simulated Bengaluru wards. The chronological test had 312 ward-week rows. MAE was 1,564.57 kg and RMSE was 2,144.14 kg. The reported errors apply to synthetic ward allocations. See [data, splits and reproducibility](docs/forecast-method.md).
