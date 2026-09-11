# Phase 3 Duplicate Analysis

No rows were removed for duplication. Repeated district-year combinations were retained because the inventory is event-level and a district can experience multiple events in one year.

## District_FloodImpact.csv

- Exact duplicate rows: 0 (0.0000%). Recommended treatment: retain all nonduplicates; no action required.
- District-year and district-event checks: not applicable because this is a district-level aggregate table with no year or event identifier.

## District_FloodedArea.csv

- Exact duplicate rows: 0 (0.0000%). Recommended treatment: retain all nonduplicates; no action required.
- District-year and district-event checks: not applicable because this is a district-level aggregate table with no year or event identifier.

## India_Flood_Inventory_v3.csv

- Exact duplicate rows: 0 (0.0000%). Recommended treatment: retain all nonduplicates; no action required.
- Duplicate district-year combinations: 823 combinations affecting 2581 rows (37.5364%). Examples: `[{"district": "Nagaon", "year": 2022, "count": 25}, {"district": "Cachar", "year": 2022, "count": 23}, {"district": "Baksa", "year": 2023, "count": 20}, {"district": "Thiruvananthapuram", "year": 2021, "count": 14}, {"district": "Baksa", "year": 2022, "count": 13}, {"district": "Itanagar", "year": 2022, "count": 12}, {"district": "South Goa", "year": 2022, "count": 12}, {"district": "Gadchiroli", "year": 2022, "count": 12}, {"district": "Nagpur", "year": 2022, "count": 12}, {"district": "Washim", "year": 2022, "count": 11}]`. Recommended treatment: retain until event semantics are defined.
- Duplicate district-event combinations: 0 repeated UEI rows. Recommended treatment: retain unique UEI records; investigate only if a future source revision creates repeated UEIs.
- Geographic records with different flood-event information: repeated district-year groups contain multiple UEIs and are therefore treated as separate event observations, not deleted duplicates.
