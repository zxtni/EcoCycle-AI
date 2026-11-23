# Phone-photo detector pilot

The scanner needs to locate an object before the material model can classify its crop. A separate object-recognition pilot checks both parts using annotated real photos. It covers bottles, hands, laptops, sunglasses and watches. The public watch class contains watches of unspecified type. A bottle label does not establish plastic or glass, and identifying electronics cannot determine whether a device is being discarded.

## Dataset and method

The pilot samples bounding boxes in the Open Images public splits using seed 417. The official validation partition fits the pilot head and the official test partition measures it. Each partition samples up to one box per image and object class. The pipeline excludes depictions and grouped annotations, removes cross-partition image-ID or exact-file matches, and downloads only selected photos. Public dataset images stay in the local cache. [Open Images annotations and photo download](https://storage.googleapis.com/openimages/web/download_v7.html)

A frozen MobileNetV2 encoder embeds annotated object crops. A regularized logistic regression head learns the five categories. Test accuracy on annotated crops measures classification with a correct box already supplied. A separate audit checks whether the existing scanner proposes a box matching each test annotation at IoU 0.50, before material classification. [MobileNetV2 source](https://github.com/tensorflow/models/tree/master/research/slim/nets/mobilenet)

## Measured results

The head fit 120 annotated crops and classified **57 of 60 held-out annotated crops correctly (95%)**. The scanner region audit used the same 60 held-out annotations.

| Object | Candidate correct with supplied crop | Existing full-frame box match | Existing detailed box match |
| --- | ---: | ---: | ---: |
| Bottle | 12/12 | 8/12 | 9/12 |
| Human hand | 11/12 | 0/12 | 0/12 |
| Laptop | 12/12 | 11/12 | 11/12 |
| Sunglasses | 12/12 | 0/12 | 0/12 |
| Watch | 10/12 | 7/12 | 7/12 |

The sunglasses result points to region localization as the next training target. With a supplied box, the candidate classified all 12 sunglasses crops correctly. The existing detailed scanner found no matching region in those 12 cases. Hand is an out-of-scope category for the waste scanner. Neither the crop score nor the proposal counts measure end-to-end material accuracy.

## Reproduce

Use the separate Python 3.12 training environment described in [the model card](../MODEL_CARD.md).

```sh
python -m pip install -r backend/vision_tools/requirements.txt
python -m backend.vision_tools.scene_pilot .tools/openimages
```

The cache contains the image IDs used for fitting and testing in `scene-pilot-metrics.json`, and the candidate weights in `object-head-candidate.npz`. The app does not load this candidate. The small, balanced sample measures a pilot workload. Exact duplicate removal cannot rule out near-duplicate images or the same physical item photographed twice.

## Validate with phone scenes

Start with the original mixed photo, the laptop photo and additional photos of separate objects in different lighting. Keep shots of the same physical object together in a single split. Annotate one box per object and mark the material only where it is known. Keep mixed-material and uncertain items labeled separately. Keep a small untouched test set of whole scenes for measuring both missed objects and incorrect material labels before changing the production model.

## V4 object detector

The release fine-tunes the official YOLOv8n Open Images checkpoint for four epochs at 384 pixels with its first ten modules frozen. It updates the detector on **95 annotated photos**, uses **25 separate photos** for checkpoint selection and evaluates on **60 Open Images test photos** held out from fine-tuning. Mosaic augmentation supplies mixed layouts during training. The frozen backbone and small fitting sample limit adaptation to new phone-camera conditions. [Ultralytics Open Images models](https://docs.ultralytics.com/datasets/detect/open-images-v7/) · [Training benchmark](../backend/vision_assets/scene-detector-metrics.json)

With correct item name and IoU at least 0.50, the pretrained checkpoint matched 20/60 annotations. The fine-tuned checkpoint matched 40/60. The app exposes four of the five trained object categories and treats hands as out of scope. Its exported CPU ONNX detector measured:

| Recognized object | Standard scan | Search for small items |
| --- | ---: | ---: |
| Bottle | 7/12 | 8/12 |
| Laptop | 8/12 | 9/12 |
| Sunglasses | 10/12 | 10/12 |
| Watch | 6/12 | 8/12 |
| **Total correct names and boxes** | **31/48 (64.6%)** | **35/48 (72.9%)** |

Both columns require a localization match at IoU 0.50 and the correct category. Each image supplies one sampled annotation for scoring. The metrics do not characterize all false positives in these photos or predict performance on the original user scene. A watch prediction does not distinguish ordinary watches from smartwatches. The material classifier still produces the material estimates shown in the separate result list. [ONNX runtime benchmark](../backend/vision_assets/scene-runtime-metrics.json)

### Reproduce the detector training

Run the pilot first to cache the selected JPEGs. Use Python 3.12 with the pilot dependencies and install PyTorch 2.7.1, torchvision 0.22.1 and Ultralytics 8.3.200 in the training environment. Download [the pinned YOLOv8n checkpoint](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-oiv7.pt) into the cache. The trainer validates the checkpoint checksum before loading it.

```sh
python -m backend.vision_tools.fit_scene_detector .tools/openimages .tools/detector-fit .tools/openimages/yolov8n-oiv7.pt
```

The training command writes the chosen CPU ONNX graph and measured validation and holdout results. Replacing the app artifact requires rerunning the runtime and API checks. [Asset provenance and license](../backend/vision_assets/NOTICE.md)

```sh
python -m backend.vision_tools.audit_scene_runtime .tools/openimages
node scripts/check.mjs
```

### Demonstrate the two result types

Sign in, open **Scan waste**, and upload the held-out sunglasses example. In standard mode it shows **Objects recognized** and a sunglasses box. The sample does not generate a material estimate until the user picks a material. [Open Images sunglasses photo](https://open-images-dataset.s3.amazonaws.com/test/97be1d6bd32aec1b.jpg)

Upload the held-out bottle example and switch between **Material boxes** and **Object boxes**. The preview and the separate result lists let the reviewer demonstrate the difference between identifying an item and estimating what it is made of. [Open Images bottle photo](https://open-images-dataset.s3.amazonaws.com/test/f351efbc9ae278f1.jpg)
