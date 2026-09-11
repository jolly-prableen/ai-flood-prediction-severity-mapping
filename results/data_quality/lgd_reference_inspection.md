# LGD Reference Inspection

- Filename: `All_Districtof_India_2026-09-11_23-48-36.xlsx`
- SHA-256: `9fc84d7b0c7b031c0d70f1e936b059b4f5d54460e28cc935308ebf306fc2af5f`
- Sheet names: `['allDistrictofIndia']`
- Active sheet rows: **784**
- Active sheet columns: **7** (two internal normalization columns were used only in memory)
- Original columns: `['State Code', 'State Name (In English)', 'District Code', 'District Name(In English)', 'Census 2001 Code', 'Census 2011 Code', 'S.No.']`

## Official fields

- `State Code`: official LGD state code field.
- `State Name (In English)`: official LGD state name.
- `District Code`: official LGD district code. The report title and portal page identify this as the district LGD-code report; it is not assumed equal to any Census code.
- `District Name(In English)`: official LGD district name.
- `Census 2001 Code`: Census reference field supplied by LGD.
- `Census 2011 Code`: Census reference field supplied by LGD.

## Quality checks

- Full duplicate rows: **0**
- Missing values: **{'State Code': 0, 'State Name (In English)': 0, 'District Code': 0, 'District Name(In English)': 0, 'Census 2001 Code': 0, 'Census 2011 Code': 0, 'S.No.': 0}**
- Duplicate LGD district codes: **0**
- Duplicate state + district combinations: **0**
- Unique district records: **784**
- Unique states: **36**
- District Code range: **1–796**

## Comparison counts

- IFI district names: **882**
- IFI names with exact LGD district-name candidates: **679**
- IFI names requiring normalization: **10**
- IFI names unmatched to LGD: **193**
- LGD districts unmatched to IFI by normalized district name: **99**
- LGD/Census name-pair candidates in comparison: **547 rows**
- Ambiguous IFI mappings with multiple comparison rows: **7 district names**
- Historical boundary concerns: all comparison rows are marked `HISTORICAL_REVIEW_REQUIRED` because IFI spans 1967–2023 while the Census boundary layer is a 2011 reference.

## Interpretation limits

The workbook is an official current LGD district reference, not a historical 1967–2023 boundary crosswalk. Its Census 2001/2011 fields are reference columns; this inspection does not certify that either equals the DataMeet `censuscode`, and it does not create an IFI-code relationship. Exact names are candidates only; normalized names, state context, and historical identity require manual verification.

Review comparison: `results/data_quality/ifi_lgd_census_comparison.csv`
