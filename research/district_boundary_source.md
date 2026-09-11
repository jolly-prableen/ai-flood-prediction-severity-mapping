# District Boundary Source

## Recommended source

Use the **DataMeet India Community Maps Project, Census 2011 district boundaries** as the initial reproducible boundary source:

- Project page: https://projects.datameet.org/maps/districts/
- Repository: https://github.com/datameet/maps/tree/master/Districts/Census_2011
- GitHub directory API: https://api.github.com/repos/datameet/maps/contents/Districts/Census_2011
- Shapefile component directory: https://github.com/datameet/maps/tree/master/Districts/Census_2011
- Main geometry file: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp
- Projection file: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.prj

This is a reliable, documented community GIS source rather than a direct government data portal. Its documentation attributes district names and extent to the Census of India Administrative Atlas 2011 and describes the broader district-map provenance. The source should therefore be treated as a 2011 reference boundary layer, not as a current administrative-boundary guarantee.

## Dataset details

| Item | Finding |
|---|---|
| Format | ESRI Shapefile: `2011_Dist.shp`, `.shx`, `.dbf`, `.prj`, plus spatial index files |
| Version/date | Census 2011 layer; the repository does not provide a precise publication date for this directory |
| CRS | WGS 84 geographic coordinates, as documented by `2011_Dist.prj` (`GCS_WGS_1984`, degree units; commonly represented as EPSG:4326) |
| District field | `DISTRICT` |
| State field | `ST_NM` |
| Census identifiers | `ST_CEN_CD`, `DT_CEN_CD`, and `censuscode` |
| LGD codes | Not documented in the published attribute list; availability is currently unverified and must not be assumed |
| License | The district page specifies Creative Commons Attribution 2.5 India. The repository README has a general CC BY 4.0 statement, so the district-specific page should be checked at the time of redistribution and attribution should include DataMeet and the linked source |

The published documentation also warns that some boundaries are pre-delimitation, some names or extents have issues, and some state-specific boundaries may be shifted. Those warnings are material for a flood map covering multiple years.

## Acquisition result

The six original Shapefile components were downloaded from the accessible DataMeet GitHub directory into `data/external/boundaries/raw/`:

- `2011_Dist.shp`
- `2011_Dist.shx`
- `2011_Dist.dbf`
- `2011_Dist.prj`
- `2011_Dist.sbn`
- `2011_Dist.sbx`

The acquired layer contains 641 polygon features and 631 distinct district names. It has 35 state names, 93 multipart geometries, no empty geometries, and no non-finite coordinates. Full polygon validity/self-intersection testing requires a GIS engine and remains pending.

## Planned join approach

No boundary file was downloaded in Phase 2. Before using it in a later phase:

1. Download the complete Shapefile component set from the Census 2011 directory and inspect the DBF fields and record counts.
2. Preserve the original boundary files under `data/external/` without editing them.
3. Prefer a verified crosswalk from IFI `State_Codes` and `District_LGD_Codes` to boundary identifiers. The boundary documentation lists Census codes, not LGD codes, so a code crosswalk must be obtained or established and independently checked.
4. Only use normalized district names as a fallback, paired with state context and a manually reviewed exception table. The IFI inventory stores comma-separated district and state lists, and the two district tables currently have `Dist_Name` but no state field.
5. Record boundary vintage, CRS, source URL, attribution, and any unmatched or ambiguous records before any spatial join.

Until that verification is complete, the boundary layer must not be treated as a safe merge key for the IFI data.