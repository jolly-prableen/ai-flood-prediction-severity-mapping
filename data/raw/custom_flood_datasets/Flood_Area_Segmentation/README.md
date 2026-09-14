# Flood Area Segmentation

Small RGB flood-area image segmentation dataset (Kaggle).

## Dataset facts
- **Dataset name:** Flood Area Segmentation
- **Creator:** Faizal Karim
- **Source URL:** https://www.kaggle.com/datasets/faizalkarim/flood-area-segmentation
- **License:** CC0 - Public Domain (as stated in Kaggle dataset metadata)
- **Task:** binary flood-water segmentation (segment the flooded / water region from imagery)
- **Annotation tool:** Label Studio (per dataset description)

## Contents
- `Image/` - flood-area RGB images, 290 JPG files
- `Mask/` - flood-water masks, 290 PNG files
- `metadata.csv` - mapping: each row `Image=<stem>.jpg, Mask=<stem>.png`

## Verified counts
- Image files: **290**
- Mask files: **290**
- Metadata pairs: **290**
- Valid pairs (same stem, both files present): **290**
- Pairs with image/mask dimension mismatch: **7**

The 7 mismatched pairs are:
- `14` (image 1900x1425, mask 1024x630)
- `15` (image 1024x630, mask 1900x1425)
- `2052` (image 1012x490, mask 1200x800)
- `2053` (image 1200x800, mask 1012x490)
- `3059` (image 650x400, mask 1920x1005)
- `1061` (image 660x440, mask 700x389)
- `1079` (image 1024x682, mask 759x422)
`14`/`15` and `2052`/`2053` carry each other's mask geometry (the masks appear swapped relative
to the images); `3059`, `1061`, `1079` have no dimension-consistent counterpart.

## Mask meaning
Masks are 8-bit grayscale (`L`) PNGs. 0 (black) = non-flood background; non-zero pixels =
flood-water region. **Important:** the masks are not strictly binary - all
290 masks contain intermediate gray levels in addition to 0 and 255
(anti-aliased / shaded water masks). Values across all masks span 0-255, and 106
of 290 masks contain the full 0-255 range.
A binarization threshold (e.g., > 0) should be applied before training a binary segmentation model.

## Dimensions
Images and masks share the same pixel dimensions per pair, apart from the 7 mismatches above.
- Image width range: 330 - 5472 px; height range: 219 - 3648 px
- Mask width range: 330 - 5472 px; height range: 219 - 3648 px

## Download
Downloaded via the Kaggle datasets download API (public, no auth required) as a single zip
(~112,072,442 bytes) and extracted verbatim. No files were altered.
