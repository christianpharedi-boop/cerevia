# External source note: USGS Earthquake Catalog API

Source URL: https://earthquake.usgs.gov/fdsnws/event/1/

The USGS Earthquake Catalog API documents the FDSN Event Web Service and supports GeoJSON output. Its time parameters use ISO-8601 timestamps, with UTC assumed when no timezone is specified. The documentation describes spatial-temporal parameters including latitude/longitude bounds and magnitude filtering.

The CEREVIA V1.4 fixture was fetched from:

https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01T00:00:00&endtime=2024-01-02T00:00:00&minmagnitude=5&limit=5&orderby=time

The checked-in fixture contains 5 GeoJSON features and has SHA-256:

`35b1e508bcdbea69976098d9f3499836934c88b36ecef503a2d52f6b460c3d95`
