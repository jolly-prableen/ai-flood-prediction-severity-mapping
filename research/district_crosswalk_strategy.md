# District Boundary and Crosswalk Strategy

## Geometry source

Use the **DataMeet India Community Maps Project, Census 2011 district boundaries** as the initial reproducible geometry source:

- Project page: https://projects.datameet.org/maps/districts/
- Census 2011 directory: https://github.com/datameet/maps/tree/master/Districts/Census_2011
- Main shapefile: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp
- Projection file: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.prj

## Known attributes and limitations

The documented attributes are `DISTRICT`, `ST_NM`, `ST_CEN_CD`, `DT_CEN_CD`, and `censuscode`. The projection file declares geographic WGS 84 coordinates. The layer is a Census 2011 reference, not a current or time-varying boundary series.

The project page states that the data were scraped from ECI polling-station locations and warns about pre-delimitation boundaries, shifts, and incorrect or missing names in some areas. The district-specific page states CC BY 2.5 India; attribution and the exact applicable license must be rechecked at acquisition time because the repository README also contains a general CC BY 4.0 statement.

**LGD status:** LGD codes are not listed in the boundary attributes. `DT_CEN_CD` and `censuscode` must not be called LGD codes. Their Census-code meaning is distinct unless an explicit crosswalk proves equivalence.

## Crosswalk design

1. Acquire the boundary component set and inspect the DBF fields before any spatial join.
2. Obtain the official Local Government Directory (LGD) district/state code reference from the Ministry of Panchayati Raj or its current official portal. Record its download date, version, identifiers, and usage terms.
3. Build a versioned crosswalk containing boundary state/district names, Census codes, LGD codes where available, IFI `state_codes`, IFI `district_lgd_codes`, and validity dates.
4. Match codes only when the source documentation establishes their semantics. Use names only as a manually reviewed fallback with state context.
5. Treat boundary changes as temporal: a 2011 geometry may not represent a district in 1967 or 2023. Decide whether the project uses a fixed 2011 geography or historical boundary versions.
6. Record one-to-many and many-to-one changes rather than forcing a single current district identity.

## Final Phase 9 status

The original DataMeet boundary components are available under `data/external/boundaries/raw/`. The review crosswalk is `data/derived/district_crosswalk.csv`, with the validation details in `results/data_quality/district_crosswalk_validation.md`.

The crosswalk preserves exact-name candidates, normalized candidates requiring verification, and unmatched IFI/boundary names. It does not certify any mapping because the state context in IFI is multi-value and the 2011 boundary vintage does not establish historical equivalence across 1967–2023.

## Official LGD reference

The Government of India Local Government Directory is available at https://lgdirectory.gov.in/. Its public description identifies it as the authoritative directory of land regions and local governments and exposes district LGD-code views/downloads. It is the correct source to investigate for a future versioned crosswalk.

No LGD file was downloaded in Phase 9. No relationship between the LGD codes and DataMeet `DT_CEN_CD` or `censuscode` has been established. Those Census fields must not be relabeled as LGD fields.

## Phase 9C status

The manually supplied official workbook `data/external/boundaries/lgd/All_Districtof_India_2026-09-11_23-48-36.xlsx` was inspected without modification. It contains 784 district records, unique LGD `District Code` values, and unique state-plus-district combinations. The workbook explicitly labels `District Code` as the district field in the official “All Districts of India” report; this is the LGD district code and is not assumed equal to Census identifiers.

The review comparison is `results/data_quality/ifi_lgd_census_comparison.csv`, with inspection details in `results/data_quality/lgd_reference_inspection.md`. It records exact-name candidates, normalized candidates, unmatched IFI/LGD records, Census boundary candidates, state-context notes, and historical limitations. No final `district_crosswalk.csv` was created or changed in Phase 9C.

The LGD workbook has 638 nonzero unique `Census 2011 Code` values overlapping boundary `censuscode` values and 70 nonzero unique `Census 2001 Code` values overlapping them. These overlaps are evidence for a future verification investigation, not proof that the fields are equivalent.