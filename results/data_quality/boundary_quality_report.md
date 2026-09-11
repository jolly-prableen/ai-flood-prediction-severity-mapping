# Boundary Quality Report

Source: DataMeet India Community Maps Project, Census 2011 district boundaries.
Source URL: https://github.com/datameet/maps/tree/master/Districts/Census_2011
Raw files were inspected in place and not modified.

## Structure

- Feature count: **641**
- Geometry types: **{'POLYGON': 641}**
- Bounding box `(xmin, ymin, xmax, ymax)`: **BBox(xmin=68.1862489922762, ymin=6.755952899354297, xmax=97.41529266790748, ymax=37.07826805983657)**
- Multipart geometries: **93**
- Empty geometries: **0**
- Non-finite coordinate values: **0**
- DBF fields: **['DISTRICT', 'ST_NM', 'ST_CEN_CD', 'DT_CEN_CD', 'censuscode']**
- CRS from `.prj`: `GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]`
- The CRS is geographic WGS 84 according to the published `.prj`; EPSG:4326 is the usual equivalent representation.
- Full polygon validity/self-intersection validation was not performed by PyShp; a GIS engine is required for that check.

## Geography and identifiers

- Boundary states represented: **35**
- Boundary districts represented: **631**
- Missing district names: **0**
- Missing state names: **0**
- District-name duplicates: **20 rows**
- State-name duplicates are expected because multiple districts occur in each state.
- Identifier analysis: `[{"field": "ST_CEN_CD", "missing_count": 0, "unique_count": 36, "duplicate_value_count": 32, "duplicate_row_count": 605}, {"field": "DT_CEN_CD", "missing_count": 0, "unique_count": 72, "duplicate_value_count": 50, "duplicate_row_count": 569}, {"field": "censuscode", "missing_count": 0, "unique_count": 641, "duplicate_value_count": 0, "duplicate_row_count": 0}]`
- Published identifier fields are Census-coded fields: `ST_CEN_CD`, `DT_CEN_CD`, and `censuscode`.
- No LGD field was found in the published DBF fields. Census codes are not called LGD codes.

## IFI comparison

- IFI distinct district tokens: **882**
- IFI distinct state tokens: **46**
- Boundary distinct districts: **631**
- Exact boundary-to-IFI district-name matches: **537**
- Normalized matches requiring verification: **22**
- Boundary-only districts: **85**
- IFI-only district tokens: **332**
- The comparison is name-based and does not establish an identifier crosswalk or historical equivalence.
- State/district spelling and historical boundary mismatches require manual review; no fuzzy match was silently accepted.

## Raw checksums

```json
{
  "2011_Dist.dbf": "2c7b03578fdf41a4c4e29941a564fa90bf0b0e4f865f5e54481ef7ac8494eb7d",
  "2011_Dist.prj": "a02a27b1d1982c8516d83398e85a3c8b1aef1713c13ef4d84d7bde17430c07c4",
  "2011_Dist.sbn": "5f9fc6f63f7f3afbb00213e9ec5d9e0f5614acb5ec4b09fb7d8e226ac9a131be",
  "2011_Dist.sbx": "4cfa7e863894118bf929e9eb4b4d97652481ce0f58359f2bb27848a1ae76abcd",
  "2011_Dist.shp": "3636e627a519f67b4615b6a97df48c2b279e8c7b2566d3bfbc3eda1d06e33206",
  "2011_Dist.shx": "12b6028dfac9e3f20686b3d0a44f9d3989acfdb3f3cda853881d1cf2d8579eab"
}
```
