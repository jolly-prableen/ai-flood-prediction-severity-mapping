# Member 2 U-Net Temporal Dataset Decision

## Decision

**No dataset was selected or downloaded for temporal U-Net training.** The repository contains no raster/image files, genuine flood-mask files, or temporal image sequences. Consequently, `U-Net + ConvLSTM` and `Attention U-Net + LSTM` remain **NOT TRAINED**.

The existing IFI-Impacts CSVs are event/district tables and cannot supply image tensors or pixel masks. No IFI-derived mask or temporal sequence was fabricated.

## Architecture contract reviewed

- `UNetConvLSTM` expects `(batch, time, channels, height, width)` and returns `(batch, classes, height, width)`.
- `AttentionUNetLSTM` expects `(batch, time, channels, height, width)` and returns `(batch, classes, height, width)`.
- Both implementations contain real temporal recurrence, but a valid experiment requires multiple genuinely time-ordered observations for the same scene/event/location.
- A single image, repeated image, or random stack of unrelated images is not a valid temporal sequence.
- Binary mask targets would need spatial shape compatible with the output, normally `(batch, 1, height, width)` or an explicitly documented binary-mask encoding.

## Public datasets evaluated for suitability

### Sen1Floods11

- Official repository: https://github.com/cloudtostreet/Sen1Floods11
- Dataset access documented through the official repository's `gs://sen1floods11/` bucket.
- Publication: Bonafilia, Tellman, Anderson, Issenberg, *Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1*, CVPR Workshops 2020.
- Documented raster dimensions: 512 x 512 chips at 10 m ground resolution.
- S1 imagery: 2 bands, VV and VH, Float32.
- S2 imagery: 13 bands, UInt16.
- QC layer: 1-band Int16 ground-truth water/flood labeling with `-1` no-data, `0` not water, `1` water.
- Event metadata includes event ID, location, Sentinel-1 date, Sentinel-2 date, orbit, and chip counts.
- Suitability: valid for spatial segmentation if downloaded and split by event, but the documented metadata provides one acquisition per event/chip rather than genuine repeated temporal sequences for the same scene.
- Decision: not suitable for the requested ConvLSTM/LSTM temporal experiment without inventing or improperly stacking time.

### FloodNet Supervised v1.0

- Official repository: https://github.com/BinaLab/FloodNet-Supervised_v1.0
- Publication: Rahnemoonfar et al., *FloodNet: A High Resolution Aerial Imagery Dataset for Post Flood Scene Understanding*, IEEE Access 2021.
- Documented size: 2,343 UAS images with semantic segmentation labels.
- Imagery was collected after Hurricane Harvey.
- Documented labels include flooded/non-flooded buildings and roads, water, vegetation, vehicles, pools, and other classes.
- Suitability: valid for spatial semantic segmentation, but the documented collection is a post-event image dataset and does not provide genuine temporal sequences for the requested recurrent temporal models.
- Decision: not suitable for the requested ConvLSTM/LSTM temporal experiment.

## Current repository audit

- No `.tif`, `.nc`, `.h5`, or equivalent raster dataset is present.
- No image/mask dataset loader exists under `src/datasets/`.
- No mask preprocessing pipeline exists.
- No event-grouped spatial split exists.
- No genuine temporal sequence manifest exists.
- No segmentation training/evaluation run was performed.

## Required future evidence before training

A future dataset must provide:

1. Legitimate raster/image files and matching genuine masks.
2. Scene/event/location identifiers.
3. At least two or more real time-ordered observations per sequence, with timestamps.
4. A reproducible event/location-grouped split preventing scene/event leakage.
5. Documented channel meanings, spatial resolution, mask encoding, no-data policy, and geographic coverage.
6. Enough sequences for train, validation, and test evaluation.

Until those requirements are met, temporal segmentation metrics must remain unavailable.
