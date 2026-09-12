# Member 1 Target Contract (Final Specification)

**Project**: AI-Based Flood Prediction and Flood Severity Mapping for Disaster Management  
**Role**: Member 1 — Data + Research Lead $\to$ Member 2 — Modeling Lead  
**Branch**: `member1-data`  
**Date**: 2026-09-12  

---

## 1. Executive Status & Categorization

| Target Variable | Target Type | Status | Role in M2 Baseline | Notes |
|---|---|---|---|---|
| **`Corrected_Percent_Flooded_Area`** | Continuous Regression ($0\text{–}100\%$) | **`APPROVED (TARGET ONLY)`** | **Primary Active Target** | Current M2 modeling target. Provenance verified; strictly target-only. |
| **`Flood_Binary`** | Binary Classification ($\{0, 1\}$) | **`PROVISIONAL`** | *Not in M2 Baseline* | IFI positives verified (1.0); non-events remain `NaN` pending GFM satellite data. |
| **`Severity_Score`** | Continuous Composite ($0\text{–}100$) | **`PROVISIONAL`** | *Not in M2 Baseline* | Training-fitted duration-fatality scaler. Labeled demonstration output. |
| **`Severity_Class`** | Multi-class Ordinal ($0\text{–}3$) | **`PROVISIONAL`** | *Not in M2 Baseline* | Thresholded severity rubric. Labeled demonstration output. |

---

## 2. CURRENT APPROVED M2 TARGET CONTRACT

### Primary Target: `Corrected_Percent_Flooded_Area`

```python
TARGET_COL = "Corrected_Percent_Flooded_Area"
```

- **Target Definition**: Net percentage of district geographical area inundated by floodwaters, adjusted for baseline permanent water surface.
- **Mathematical Provenance**: A mathematical verification across all 732 rows in `data/raw/District_FloodedArea.csv` confirmed:
  $$\text{Corrected\_Percent\_Flooded\_Area} = |\text{Percent\_Flooded\_Area} - \text{Parmanent\_Water}| \quad (\text{exact on } 732 / 732 \text{ rows})$$
- **Observed Distribution**:
  - Minimum: $0.0000734\%$
  - Median: $1.22247\%$
  - Mean: $2.71344\%$
  - Maximum: $23.62193\%$
  - Missing Values: Exactly $0$ missing values ($732 / 732$ present).
- **Target Invariant**:
  - **TARGET ONLY**: Must NEVER be used as a predictive feature. Using it as an input creates complete circular target leakage.
  - **Known Limitation**: The table represents an all-time/multi-year historical aggregate without dynamic weekly timestamps. It is preserved specifically as Member 2's existing baseline target for the hackathon.

---

## 3. ADDITIONAL PLANNED TARGETS (Documented Separately)

*These targets are part of the extended prediction infrastructure and are NOT forced into the existing M2 baseline.*

### A. `Flood_Binary` (Provisional Binary Prediction Target)
- **Definition**: Binary indicator of flood occurrence in the 7-day forecast horizon $[C+1, C+7]$ following cutoff $C$.
  $$\text{Flood\_Binary} = \begin{cases} 1.0 & \text{if a verified IFI event overlaps } [C+1, C+7] \\ \text{NaN} & \text{if unobserved / no IFI report (coverage unknown)} \\ 0.0 & \text{only when independent satellite non-detection is proven} \end{cases}$$
- **Negative Label Policy**:
  - **Absence of an IFI event record is NEVER interpreted as proof of no flood (0.0)**.
  - Doing so creates catastrophic false negatives in rural/remote areas due to reporting bias.
  - Because Copernicus GFM Sentinel-1 observations are unacquired, zero false negatives were created ($0.0 \text{ count} = 0$). All unobserved rows explicitly remain `NaN`.

### B. `Severity_Score` (Provisional Continuous Severity Target)
- **Definition**: Continuous composite impact score normalized to $[0, 100]$:
  $$\text{Severity\_Score} = 100 \times \left(0.4 \cdot \tilde{D} + 0.6 \cdot \tilde{F}\right)$$
  where $\tilde{D}$ is min-max scaled $\log(1 + \text{duration\_days})$ and $\tilde{F}$ is min-max scaled $\log(1 + \text{fatalities})$.
- **Training-Only Normalization**: Bounds fitted strictly on training years (2015–2020) and saved in `results/checkpoints/severity_scaler.json`.
- **Status**: Kept strictly **PROVISIONAL / DEMONSTRATION OUTPUT** until multi-year ground-truth calibration is finalized.

### C. `Severity_Class` (Provisional Categorical Severity Target)
- **Definition**: 4-tier categorical disaster classification:
  - Class 0: `NO_FLOOD` ($\text{Severity\_Score} = 0.0$ / satellite-verified negative)
  - Class 1: `MODERATE` ($0.0 < \text{Severity\_Score} \le 33.3$)
  - Class 2: `SEVERE` ($33.3 < \text{Severity\_Score} \le 66.7$)
  - Class 3: `CATASTROPHIC` ($\text{Severity\_Score} > 66.7$)
- **Status**: Kept strictly **PROVISIONAL / DEMONSTRATION OUTPUT**.
