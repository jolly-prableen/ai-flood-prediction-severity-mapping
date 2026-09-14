# Chronological Split Validation Report

## 1. Temporal Partitions

| Split | Start Date | End Date | Samples | Positives (1) | Unknowns (NaN) | Districts | Mean Severity Score |
|---|---|---|---|---|---|---|---|
| Train | 2015-01-04 | 2020-12-27 | 157,126 | 11,269 (7.17%) | 145,857 | 502 | 48.19 |
| Val | 2021-01-03 | 2022-06-26 | 39,156 | 1,421 (3.63%) | 37,735 | 502 | 53.7 |
| Test | 2022-07-03 | 2023-12-31 | 39,658 | 1,495 (3.77%) | 38,163 | 502 | 47.1 |

## 2. Leakage Protections

- **Strict Chronological Separation**: Training observations strictly precede Validation, which strictly precedes Test.
- **Zero Temporal Overlap**: No forecast window from Train overlaps Validation or Test.
- **Equal Spatial Representation**: All 502 verified districts are present in every weekly cutoff across all three splits.
