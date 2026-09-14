# Model and Data Compatibility

The repository does not contain a separate implementation plan. This review uses the model list and six-month sequence requirement provided for Phase 4.6:

- U-Net + ConvLSTM
- CNN + LSTM
- CNN + Transformer
- ResNet + BiLSTM
- Attention U-Net + LSTM

## Recommended observation tensor

The strongest candidate is **district-week with a 26-week history**, representing approximately six months. Each time step can contain rainfall summaries and other independently verified pre-cutoff features. A district-week target would require a verified non-event frame and an approved lead time.

## Compatibility by model family

| Model | Data shape implied | Compatibility |
|---|---|---|
| U-Net + ConvLSTM | Spatial grid × time sequence | Requires gridded rainfall and rasterized static layers; district tables alone are insufficient |
| CNN + LSTM | Spatial feature maps or ordered feature sequences × time | Compatible with district-week only after defining spatial representation; raw district names are not numeric spatial inputs |
| CNN + Transformer | Spatial/feature embeddings × time tokens | Compatible with 26 weekly steps, subject to careful masking and chronological design |
| ResNet + BiLSTM | Image/spatial encoder outputs × time sequence | Requires consistent spatial rasters or image tiles; bidirectionality must not use future sequence steps relative to the prediction cutoff |
| Attention U-Net + LSTM | Spatial grid × time sequence | Requires gridded rainfall and aligned boundary/static layers; not supported by current IFI tables alone |

## Important constraint

The six-month sequence length does not determine the forecast horizon. It determines the historical context window. A seven-day lead is a possible weekly design candidate, but remains `REQUIRES TEAM DECISION`.

No model inputs, tensors, sequences, or labels were created in this phase.