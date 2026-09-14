# Member 2 Limitations

1. The current baseline uses only `Population` and `Parmanent_Water`.
2. The target is `Corrected_Percent_Flooded_Area`, so this is a limited district flooded-area regression baseline, not a complete flood forecasting system.
3. No rainfall, DEM, satellite time series, river, land-cover, or other environmental predictors are used.
4. The dataset has 720 district rows and a 503/108/109 split; it is not a district-week forecasting frame.
5. The three neural models remain underfit under the project's diagnosis criteria.
6. The controlled experiment produced only modest changes. CNN + Transformer improved MAE but degraded RMSE and R², so its protected baseline remains preferable.
7. Error increases for high actual flooded-area values.
8. Permutation sensitivity is a predictive sensitivity diagnostic, not SHAP and not causal feature importance.
9. U-Net + ConvLSTM and Attention U-Net + LSTM are implemented but not trained. No valid temporal raster/image sequence and mask dataset was available.
10. Segmentation metrics and qualitative segmentation examples do not exist.
11. Future rainfall and richer spatiotemporal modeling require a separately approved dataset and experiment.
