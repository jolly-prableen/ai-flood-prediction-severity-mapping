# IFI v3 Detailed Inspection

Generated from every CSV currently present in `data/raw/`. Raw files were read only and were not modified. No merge, cleaning, imputation, split, augmentation, or modeling was performed.

## Dataset dimensions and coverage

### `District_FloodImpact.csv`

- Rows: 732
- Columns: 5
- Duplicate rows: 0
- Unique states: 0
- Unique districts: 726
- Date/year coverage: `{}`
- Identifier columns: `none detected by name`
- Categorical columns: `Dist_Name`
- Numerical columns: `Human_fatality, Human_injured, Population, Mean_Flood_Duration`

| Column | dtype | missing | missing % | unique | minimum | maximum |
|---|---|---:|---:|---:|---|---|
| Dist_Name | str | 0 | 0.0% | 726 |  |  |
| Human_fatality | int64 | 0 | 0.0% | 234 | 0 | 1726 |
| Human_injured | int64 | 0 | 0.0% | 85 | 0 | 671 |
| Population | int64 | 0 | 0.0% | 732 | 7110 | 13403998 |
| Mean_Flood_Duration | float64 | 11 | 1.5027% | 36 | 1.0 | 35.0 |

### `District_FloodedArea.csv`

- Rows: 732
- Columns: 4
- Duplicate rows: 0
- Unique states: 0
- Unique districts: 726
- Date/year coverage: `{}`
- Identifier columns: `none detected by name`
- Categorical columns: `Dist_Name`
- Numerical columns: `Percent_Flooded_Area, Parmanent_Water, Corrected_Percent_Flooded_Area`

| Column | dtype | missing | missing % | unique | minimum | maximum |
|---|---|---:|---:|---:|---|---|
| Dist_Name | str | 0 | 0.0% | 726 |  |  |
| Percent_Flooded_Area | float64 | 0 | 0.0% | 730 | 0.001739235 | 32.6562 |
| Parmanent_Water | float64 | 0 | 0.0% | 673 | 0.0 | 29.67097127 |
| Corrected_Percent_Flooded_Area | float64 | 0 | 0.0% | 730 | 7.34e-05 | 23.62192797 |

### `India_Flood_Inventory_v3.csv`

- Rows: 6876
- Columns: 23
- Duplicate rows: 0
- Unique states: 46
- Unique districts: 882
- Date/year coverage: `{"Start Date": {"valid_count": 6856, "invalid_count": 0, "minimum": "1967-07-02", "maximum": "2023-09-12", "minimum_year": 1967, "maximum_year": 2023}, "End Date": {"valid_count": 6856, "invalid_count": 0, "minimum": "1967-07-08", "maximum": "2023-09-12", "minimum_year": 1967, "maximum_year": 2023}}`
- Identifier columns: `Unnamed: 0, UEI, Event Souce ID, District_LGD_Codes, State_Codes`
- Categorical columns: `UEI, Start Date, End Date, Main Cause, Districts, State, Human Displaced, Animal Fatality, Description of Casualties/injured, Extent of damage , Event Source, District_LGD_Codes, State_Codes`
- Numerical columns: `Unnamed: 0, Duration(Days), Location, Latitude, Longitude, Severity, Area Affected, Human fatality, Human injured, Event Souce ID`

| Column | dtype | missing | missing % | unique | minimum | maximum |
|---|---|---:|---:|---:|---|---|
| Unnamed: 0 | int64 | 0 | 0.0% | 6876 | 563 | 7438 |
| UEI | str | 0 | 0.0% | 6876 |  |  |
| Start Date | str | 20 | 0.2909% | 3685 |  |  |
| End Date | str | 20 | 0.2909% | 3693 |  |  |
| Duration(Days) | float64 | 19 | 0.2763% | 62 | 1.0 | 365.0 |
| Main Cause | str | 31 | 0.4508% | 580 |  |  |
| Location | float64 | 6876 | 100.0% | 1 |  |  |
| Districts | str | 59 | 0.8581% | 2893 |  |  |
| State | str | 0 | 0.0% | 82 |  |  |
| Latitude | float64 | 6876 | 100.0% | 1 |  |  |
| Longitude | float64 | 6876 | 100.0% | 1 |  |  |
| Severity | float64 | 6876 | 100.0% | 1 |  |  |
| Area Affected | float64 | 6876 | 100.0% | 1 |  |  |
| Human fatality | float64 | 3106 | 45.1716% | 184 | 1.0 | 5000.0 |
| Human injured | float64 | 5818 | 84.6131% | 63 | 1.0 | 2000.0 |
| Human Displaced | str | 6754 | 98.2257% | 24 |  |  |
| Animal Fatality | str | 6305 | 91.6958% | 248 |  |  |
| Description of Casualties/injured | str | 3609 | 52.4869% | 2488 |  |  |
| Extent of damage  | str | 3121 | 45.3898% | 3613 |  |  |
| Event Source | str | 0 | 0.0% | 1 |  |  |
| Event Souce ID | float64 | 6876 | 100.0% | 1 |  |  |
| District_LGD_Codes | str | 304 | 4.4212% | 2483 |  |  |
| State_Codes | str | 258 | 3.7522% | 66 |  |  |

## Relationship and key assessment

- Inventory district and state fields contain comma-separated values; they are not one-row-per-district keys.
- `Districts` and `Dist_Name` are possible name-based candidates only after tokenization and normalization, and require state context because names are not unique globally.
- `District_LGD_Codes` and `State_Codes` occur in the inventory but have no corresponding fields in the current district tables.
- No merge was performed.

## Quality and anomaly findings

- `District_FloodImpact.csv`: no numeric-range or date-year violations detected by the conservative checks.
- `District_FloodedArea.csv`: no numeric-range or date-year violations detected by the conservative checks.
- `India_Flood_Inventory_v3.csv`: no numeric-range or date-year violations detected by the conservative checks.
- `India_Flood_Inventory_v3.csv` duplicate district-year check: `{"available_rows": 6797, "duplicate_combination_count": 823, "duplicate_row_count": 1758, "examples": [{"districts": "Nagaon", "year": 2022, "count": 25}, {"districts": "Cachar", "year": 2022, "count": 23}, {"districts": "Baksa", "year": 2023, "count": 20}, {"districts": "Thiruvananthapuram", "year": 2021, "count": 14}, {"districts": "Baksa", "year": 2022, "count": 13}, {"districts": "Itanagar", "year": 2022, "count": 12}, {"districts": "South Goa", "year": 2022, "count": 12}, {"districts": "Gadchiroli", "year": 2022, "count": 12}, {"districts": "Nagpur", "year": 2022, "count": 12}, {"districts": "Washim", "year": 2022, "count": 11}, {"districts": "Nizamabad", "year": 2022, "count": 11}, {"districts": "Wayanad ", "year": 2013, "count": 10}, {"districts": "Karimnagar", "year": 2022, "count": 10}, {"districts": "Dhemaji ", "year": 2023, "count": 10}, {"districts": "Dibrugarh ", "year": 2023, "count": 10}, {"districts": "Thiruvananthapuram", "year": 2020, "count": 9}, {"districts": "Dima Hasao", "year": 2022, "count": 9}, {"districts": "Darrang", "year": 2022, "count": 9}, {"districts": "Kamrup", "year": 2022, "count": 9}, {"districts": "Marigaon", "year": 2022, "count": 9}]}`
- `India_Flood_Inventory_v3.csv` name variants after normalization: `{"State": {"normalized_names_with_multiple_spellings": 1, "examples": {"uttarpradesh": ["Uttar Pradesh", "Uttar pradesh"]}}, "Districts": {"normalized_names_with_multiple_spellings": 13, "examples": {"kanpurnagar": ["Kanpur Nagar", "Kanpur nagar"], "howrah": ["Howrah", "howrah"], "kashmirvalley": ["Kashmir Valley", "Kashmir valley"], "south24parganas": ["South 24 Parganas", "South 24 Parganas*"], "southsalmaramancacharmankachar": ["South Salmara Mancachar - Mankachar", "South Salmara Mancachar- Mankachar"], "nalgonda": ["Nalgonda", "nalgonda"], "purbabardhaman": ["Purba Bardhaman", "Purba bardhaman"], "northwest": ["North West", "North west"], "kanpurnagardehat": ["Kanpur nagar Dehat", "Kanpur nagar-Dehat"], "partsofuttarpradesh": ["& Parts of Uttar Pradesh", "Parts of Uttar Pradesh"], "partsofhimachalpradesh": ["& Parts of Himachal Pradesh", "Parts of Himachal Pradesh"], "davangere": ["Davangere", "Davangere\ufffd\ufffd\ufffd\ufffd"], "sasnagar": ["S.A.S Nagar", "S.A.S Nagar*"]}}}`

## Relationship results

```json
{
  "common_exact_columns": {
    "District_FloodImpact.csv & District_FloodedArea.csv": [
      "Dist_Name"
    ],
    "District_FloodImpact.csv & India_Flood_Inventory_v3.csv": [],
    "District_FloodedArea.csv & India_Flood_Inventory_v3.csv": []
  },
  "candidate_keys": [
    {
      "fields": [
        "Districts",
        "Dist_Name"
      ],
      "status": "possible after tokenization and name normalization; ambiguous and not a safe merge key alone"
    },
    {
      "fields": [
        "District_LGD_Codes"
      ],
      "status": "identifier-like in inventory only; no corresponding field in current district tables"
    },
    {
      "fields": [
        "State_Codes"
      ],
      "status": "identifier-like in inventory only; no corresponding field in current district tables"
    },
    {
      "fields": [
        "State",
        "Dist_Name"
      ],
      "status": "state context is needed, but current district tables have no state column"
    }
  ],
  "name_comparisons": [
    {
      "inventory_field": "Districts",
      "district_table_field": "Dist_Name",
      "table_rows": 732,
      "inventory_distinct_tokens": 882,
      "table_distinct_names": 726,
      "exact_name_matches": 639,
      "normalized_name_matches": 647,
      "unmatched_table_names": [
        "Ahmadabad",
        "Ahmadnagar",
        "Alipurduar",
        "Anantapur",
        "Aravalli",
        "Badgam",
        "Baloda Bazar",
        "Bametara",
        "Bandipore",
        "Bangalore",
        "Baramula",
        "Baudh",
        "Bid",
        "Bidar",
        "Buldana",
        "Chittaurgarh",
        "Dadra & Nagar Haveli",
        "Daman",
        "Darjiling",
        "Davanagere",
        "Debagarh",
        "Dhaulpur",
        "Diu",
        "Dohad",
        "East District",
        "Faizabad",
        "Firozpur",
        "Gariaband",
        "Gondiya",
        "Hardwar",
        "Hoshangabad",
        "Jalor",
        "Jayashankar",
        "Jhargram",
        "Kamrup Metropolitan",
        "Kanpur Dehat",
        "Kodarma",
        "Kondagaon",
        "Koriya",
        "Lahul & Spiti",
        "Lakshadweep",
        "Leh",
        "Medinipur West",
        "Morigaon",
        "Nabarangapur",
        "Nicobars",
        "North  & Middle Andaman",
        "North  District",
        "North Twenty Four Pargan*",
        "Osmanabad"
      ],
      "candidate_key": "normalized district name only; not unique or sufficient without state context"
    },
    {
      "inventory_field": "Districts",
      "district_table_field": "Dist_Name",
      "table_rows": 732,
      "inventory_distinct_tokens": 882,
      "table_distinct_names": 726,
      "exact_name_matches": 639,
      "normalized_name_matches": 647,
      "unmatched_table_names": [
        "Ahmadabad",
        "Ahmadnagar",
        "Alipurduar",
        "Anantapur",
        "Aravalli",
        "Badgam",
        "Baloda Bazar",
        "Bametara",
        "Bandipore",
        "Bangalore",
        "Baramula",
        "Baudh",
        "Bid",
        "Bidar",
        "Buldana",
        "Chittaurgarh",
        "Dadra & Nagar Haveli",
        "Daman",
        "Darjiling",
        "Davanagere",
        "Debagarh",
        "Dhaulpur",
        "Diu",
        "Dohad",
        "East District",
        "Faizabad",
        "Firozpur",
        "Gariaband",
        "Gondiya",
        "Hardwar",
        "Hoshangabad",
        "Jalor",
        "Jayashankar",
        "Jhargram",
        "Kamrup Metropolitan",
        "Kanpur Dehat",
        "Kodarma",
        "Kondagaon",
        "Koriya",
        "Lahul & Spiti",
        "Lakshadweep",
        "Leh",
        "Medinipur West",
        "Morigaon",
        "Nabarangapur",
        "Nicobars",
        "North  & Middle Andaman",
        "North  District",
        "North Twenty Four Pargan*",
        "Osmanabad"
      ],
      "candidate_key": "normalized district name only; not unique or sufficient without state context"
    }
  ],
  "merge_performed": false
}
```
