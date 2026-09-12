# SMOTE & Class Imbalance Policy

## 1. Core Principles
1. **Split First**: Synthetic sample generation (SMOTE or similar) must **NEVER** be applied before chronological dataset splitting.
2. **Training-Only Execution**: SMOTE is applied exclusively to the **training partition** (or within inner cross-validation folds).
3. **Purity of Evaluation**: Validation and Test sets must never be oversampled, downsampled, or synthetically perturbed. They must reflect the true, unadulterated distribution of observations.
4. **Negative-Sample Prerequisite**: SMOTE creates interpolations between minority samples and requires verified majority/negative samples. In the current observation frame, unverified non-events remain `UNKNOWN` (`NaN`) per the negative observation framework. SMOTE should only be triggered if a verified negative sampling strategy is approved.
