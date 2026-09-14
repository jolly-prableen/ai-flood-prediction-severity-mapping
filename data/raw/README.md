# IFI-Impacts raw data

The real India Flood Inventory-Impacts (IFI-Impacts) dataset is not included in this repository yet.

Obtain it from the official Zenodo record only:

https://zenodo.org/records/11275211

Place the downloaded, unmodified CSV files in this directory. Expected files from the official record are:

- `India_Flood_Inventory_v3.csv` - event-level flood inventory
- `District_FloodImpact.csv` - district-level impact aggregates
- `District_FloodedArea.csv` - district-level flooded-area information

Do not rename, merge, synthesize, or replace these files with another flood dataset. After placing the files here, inspect them before preprocessing:

```powershell
$env:PYTHONPATH='.'
python -m src.datasets.inspect_ifi --input-dir data/raw --output results/dataset_inspection.json
```

The current repository has no raw IFI files, so no real-data training, metrics, or checkpoints have been produced.
