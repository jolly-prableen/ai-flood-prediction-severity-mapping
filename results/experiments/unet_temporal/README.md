# U-Net Temporal Experiment Status

## Status

**NOT TRAINED.** No legitimate raster dataset with genuine temporal sequences and matching flood masks is available in the repository or selected for download.

This experiment directory is a status record only. It contains no model checkpoint and no segmentation metric.

## Existing architectures

- `U-Net + ConvLSTM`: expected input `(batch, time, channels, height, width)`; output `(batch, classes, height, width)`.
- `Attention U-Net + LSTM`: expected input `(batch, time, channels, height, width)`; output `(batch, classes, height, width)`.

## Dataset decision

Sen1Floods11 and FloodNet were reviewed as legitimate segmentation candidates. Both provide imagery and masks, but neither provides the genuine repeated temporal sequences required by the requested ConvLSTM/LSTM experiment. No images or masks were downloaded, copied, synthesized, or stacked.

## Preprocessing and augmentation

Not executed. There is no valid local image/mask dataset to preprocess. No resizing, normalization, mask operation, CLAHE, or augmentation was performed.

## Split and leakage

Not created. A valid future split must be grouped by scene/event/location and must prevent related observations from crossing train, validation, and test partitions.

## Loss and training

Not selected or run. No BCE, Dice, combined loss, early stopping, or training configuration was executed for these models.

## Evaluation

No IoU, Dice/F1, precision, recall, pixel accuracy, confusion matrix, qualitative result, or inference result was generated. Regression metrics from the existing Member 2 baseline are not comparable to segmentation metrics and are intentionally excluded here.

## Future completion gate

Training may begin only after a real dataset manifest proves:

- image-to-mask matching;
- genuine time-ordered sequences;
- channel and resolution metadata;
- event/location grouping;
- leakage-safe splits;
- sufficient train/validation/test sequence counts.
