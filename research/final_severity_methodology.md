# Final Severity Methodology & Component Registry

## Status
Frozen methodology for Severity_Score and Severity_Class construction.

---

## 1. Resolution of `Corrected_Percent_Flooded_Area` Provenance

### Verification Findings
A rigorous mathematical audit of all 732 rows in `data/raw/District_FloodedArea.csv` verified that:
$$\text{Corrected\_Percent\_Flooded\_Area} = |\text{Percent\_Flooded\_Area} - \text{Parmanent\_Water}| \quad (\text{exact match on } 732/732 \text{ rows})$$

### Provenance Evaluation
1. **Mathematical Meaning**: The variable subtracts `Parmanent_Water` from `Percent_Flooded_Area` to isolate temporary inundation from permanent water bodies. For 36 districts where permanent water exceeded observed flooded area (likely due to seasonal drying below reference baseline), the absolute difference $|P - W|$ was taken.
2. **Temporal Resolution**: The table `District_FloodedArea.csv` is an **all-time static district summary** covering the entire historical study period without date, month, year, or event timestamps.
3. **Leakage Evaluation**:
   - Using this variable as a **predictive feature** for dynamic weekly flood forecasting constitutes severe **target leakage** (multi-year future flood extents leaking into historical antecedent windows).
   - Using it as a **dynamic weekly target** is invalid because it has no temporal variance across weeks.
4. **Methodological Decision**:
   - **DEFERRED** as a predictive feature (prohibited from canonical feature order).
   - **DEFERRED** as a weekly regression target.
   - Preserved only for Member 2's existing baseline comparison in its isolated module.

---

## 2. Frozen Severity Component Registry

The dynamic Severity_Score for positive district-week flood events is constructed strictly from verifiable event-level outcome variables:

| Component | Source Column | Unit | Transformation | Missing Handling | Training-Fitted Normalization |
|---|---|---|---|---|---|
| `duration_days` | `ifi_event_clean.csv` | Days ($\ge 1$) | $\ln(1 + \text{duration\_days})$ | Exclude 17 contradictory dates; complete in 100% of 2015–2023 events | Min-Max scaling fitted on Train period only |
| `human_fatality` | `ifi_event_clean.csv` | Count ($\ge 0$) | $\ln(1 + \text{human\_fatality})$ | Preserved as missing when unrecorded; indicator `has_fatality_record` | Min-Max scaling fitted on Train period only |

---

## 3. Normalization and Composite Score Formula

All scaling parameters $(\min, \max)$ are fitted exclusively on the **training period (2015–2020)**.

For any positive event $e$ in the forecast window:
$$z_{\text{duration}} = \frac{\ln(1 + \text{duration}) - \min_{\text{train}}(\ln(1 + \text{duration}))}{\max_{\text{train}}(\ln(1 + \text{duration})) - \min_{\text{train}}(\ln(1 + \text{duration}))}$$

$$z_{\text{fatality}} = \frac{\ln(1 + \text{fatalities}) - \min_{\text{train}}(\ln(1 + \text{fatalities}))}{\max_{\text{train}}(\ln(1 + \text{fatalities})) - \min_{\text{train}}(\ln(1 + \text{fatalities}))}$$

Composite Score:
- If fatalities are recorded:
  $$\text{Severity\_Score} = 100 \times (0.5 \times z_{\text{duration}} + 0.5 \times z_{\text{fatality}})$$
- If fatalities are unrecorded:
  $$\text{Severity\_Score} = 100 \times z_{\text{duration}}$$

For verified non-events / unflooded observations:
$$\text{Severity\_Score} = 0.0$$

---

## 4. Severity Class Definition

`Severity_Class` is derived directly from the frozen `Severity_Score`:

| Class | Label | Score Threshold | Meaning |
|---|---|---|---|
| 0 | `NO_FLOOD` | $\text{Severity\_Score} = 0$ | Verified non-event / unflooded district-week |
| 1 | `MODERATE` | $0 < \text{Severity\_Score} \le 33.3$ | Short duration, minimal or no recorded fatalities |
| 2 | `SEVERE` | $33.3 < \text{Severity\_Score} \le 66.6$ | Multi-day inundation, moderate casualties |
| 3 | `CATASTROPHIC` | $\text{Severity\_Score} > 66.6$ | Prolonged disaster event, high casualty/impact counts |

---

## 5. Leakage and Isolation Safeguards
- All severity components are post-event impacts and must **NEVER** enter predictive feature tensors.
- Normalization parameters must never be fitted using validation, test, or inference data.
