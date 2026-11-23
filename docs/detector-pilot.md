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
