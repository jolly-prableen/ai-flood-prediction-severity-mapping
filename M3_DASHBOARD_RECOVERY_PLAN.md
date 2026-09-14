# M3 Dashboard Recovery — Pre-Modification Plan

Date: 2026-09-12

## A. Recovery source
- **Authoritative copy of the original M3 dashboard UI:** GitHub remote
  `https://github.com/jolly-prableen/ai-flood-prediction-severity-mapping`,
  branch `feature/dashboard-ui`, commit `881b1d9`
  ("Integrate Member 2 API contract: live PyTorch checkpoint loading and baseline schema enforcement"),
  file `src/dashboard/app.py` — the full **"AI Flood Early Warning Dashboard"**
  (Analytics & GIS Overview + Custom Prediction & Retraining Mode).
  A working clone was made at `%TEMP%\opencode\m3_recovery` for read-only inspection.
- VS Code local history (`%APPDATA%\Code\User\History`) holds only the SIMPLIFIED
  `member3-dashboard-ui` snapshots and is NOT the original; it was used to confirm
  that the simplified dashboard replaced the true original.
- `integration/` and the local git clone `ai-flood-prediction-severity-mapping-remote`
  were deleted earlier; the remote GitHub repo is the only intact original.

## B. Problem being fixed
The current `app/app.py` is a **simplified M2-only dashboard** ("IFI Flooded-Area Regression")
that overwrote the original Member 3 dashboard UI during an earlier consolidation.
This plan restores the original M3 UI and wires it to the real Member 2 regression backend
**without fabricating any data**.

## C. Files to RESTORE (from git commit 881b1d9)
| File | Source | Note |
|------|--------|------|
| `app/app.py` | git `src/dashboard/app.py` | Original M3 UI restored (layout, titles, sections preserved). |

## D. Files to ADAPT (existing real M2 pieces kept as-is)
| File | Action |
|------|--------|
| `app/app.py` | Import `from src import backend_api as api` (real M2 adapter) instead of the git-era `sys.path.append("src"); import backend_api`. Prediction results mapped to real keys (`prediction`, `status`, `warnings`) — NOT fabricated `probabilities`/`predictions`. |
| `app/app.py` | KPI cards 1–3 (High Risk Districts, Avg Flood Probability, Peak Rainfall) shown as **Unavailable** (no rainfall/probability outputs exist). KPI 4 (Available Trained Models) uses real `api.get_available_models()`. |
| `app/app.py` | Map + Probability charts replaced with **Unavailable** notices (no validated geographic join key; regression output, not probability). |
| `app/app.py` | Retraining button surfaces the backend's **unavailable** status (real `retrain_model` is disabled in the dashboard). |
| `RUN.md` | Remove `app\demo_app.py` mention; document restored dashboard behavior. |
| `app/demo_app.py` | **DELETE** (broken reconstruction with `continue` outside a loop = SyntaxError; superseded by restored `app/app.py`). Not an M1/M2 artifact. |

## E. Files PRO (protected — MUST remain byte-identical)
- `data/processed/district_flood_area_regression.csv` (720 rows, features `Population`, `Parmanent_Water`, target `Corrected_Percent_Flooded_Area`)
- `data/splits/district_flood_area_split.json` (503/108/109)
- `results/models/cnn_lstm/best_model.pt`, `cnn_transformer/best_model.pt`, `resnet_bilstm/best_model.pt`
- `results/models/*/` artifacts (preprocessing.pkl, feature_schema.json, model_config.json, metrics.json, history.json, training_history.json)
- `results/models/linear_regression/`, `results/models/random_forest_regressor/` artifacts
- `results/final_member2/**`, `results/model_comparison.csv`, `results/training_summary.json`, `results/evaluation/**`
- All M2 inference/training code: `src/inference/**`, `src/models/**`, `src/training/**`, `src/backend_api.py`
- Raw IFI provenance: `data/raw/original_IFIv3_zenodo/**`
- `data/raw/sample_test_input.csv` (current M2-compatible version, KEEP)

SHA-256 baselines for the protected models/artifacts were recorded **before** any change
(see verification step at the end).

## F. Explicitly NOT done
- No modification/deletion/retraining of any M1/M2 artifact.
- No ERA5-Land, rainfall, GFM, or external flood-observation data.
- No fabricated probabilities, risk maps, or retraining claims.
- No redrawing of a new dashboard — the original M3 layout is restored.

## G. Verification done after restoration
1. `py_compile` on `app/app.py` and all changed files.
2. `app/app.py` runs via `streamlit run` (boot check on a free port).
3. `api.get_available_models()` lists 3 trained models; un-trained U-Net models show unavailable.
4. Real checkpoint inference on `data/raw/sample_test_input.csv` for all 3 models.
5. Incompatible data (missing `Population`/`Parmanent_Water`) is rejected, prediction blocked.
6. No fake probabilities/metrics in the restored UI; unsupported sections labeled Unavailable.
7. SHA-256 of every protected model/artifact unchanged from the pre-modification baseline.