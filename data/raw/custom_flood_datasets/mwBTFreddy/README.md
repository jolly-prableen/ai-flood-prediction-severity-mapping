# mwBTFreddy - Sample Subset (Subset1)

Satellite images and building-damage annotations for Cyclone Freddy (Malawi),
packaged by kuyeseraAi.

## Dataset name
mwBTFreddy (Malawi building damage from Cyclone Freddy) - Sample Subset1

## Source URL
- Zenodo record: https://zenodo.org/records/14190390
- DOI: 10.5281/zenodo.14190390
- Paper: https://arxiv.org/abs/2505.01242
- Code/repo: https://github.com/kuyeseraAi/mwBTFreddy
- License: CC-BY-4.0

## Number of image pairs
10 image pairs = 10 `pre_disaster` images + 10 `post_disaster` images
(20 TIF images total, 1024x1024 pixels), each paired with one JSON annotation
file (20 JSON files total).

## Pre / post image meaning
For each disaster location, an image pair shows the same area of Chilobwe /
Blantyre, Malawi before (`.tif` ending `_pre_disaster`) and after
(`.tif` ending `_post_disaster`) Cyclone Freddy in early 2023. The pre image is
the reference/baseline state; the post image is the damaged state used to
detect building damage.

## JSON annotation meaning
Each JSON file (same base name as its image) contains:
- `metadata`: disaster (`malawi-cyclone`), disaster type (`cyclone`), image name
  and dimensions, and the image catalog id.
- `features.lng_lat`: a list of building footprints expressed as WKT polygons in
  longitude/latitude coordinates. Each footprint has properties
  `feature_type` (building) and `subtype` (damage label) which follow the
  xView2 damage scale, here one of: `no-damage`, `major-damage`, `destroyed`.

In this sample subset the 1,274 annotated buildings break down as:
no-damage 1,266, destroyed 7, major-damage 1.

## Sample subset - not the full dataset
This folder contains **Subset1 only** (20 images), which is the small sample
published as mwBTFreddy version 1.0. The full mwBTFreddy dataset has 696 images
and a much larger size; it is NOT downloaded here. This sample must not be
treated as the full training corpus.