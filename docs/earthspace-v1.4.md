# CEREVIA V1.4 Earth/Space Domain Transplant

V1.4 deliberately attacks a different assumption from neuroscience and proteomics. The workflow is spatial-temporal rather than session-based or assay-processing-based:

> **Earth observations → spatial-temporal dataset → transformation → derived product → analysis → inference → claim → finding**

The fixture is a five-event GeoJSON query from the public [USGS Earthquake Catalog FDSN Event Web Service](https://earthquake.usgs.gov/fdsnws/event/1/), queried for 2024-01-01 UTC, magnitude at least 5, with a fixed limit and ordering. The USGS service documents GeoJSON output, ISO-8601 time parameters, latitude/longitude bounds, and spatial-temporal query parameters [1].

## Adapter boundary

The Earth/Space adapter understands GeoJSON `FeatureCollection` records, earthquake coordinates, depth, magnitude, source timestamps, spatial-temporal normalization, and a descriptive cluster summary. It does not implement a second provenance system, identity mechanism, verifier, claim framework, mutable database, AI interpretation layer, or replacement evidence graph.

The adapter reuses the same `Artifact.derive`, `ArtifactCatalog`, manifest, independent bundle verifier, Sentinel attack suite, Ed25519 attestation, transparency log, revocation registry, and Observatory contracts used by neuroscience and proteomics.

## Acceptance criterion

The transplant is accepted only if the trust semantics remain unchanged. The proof must independently verify the bundle, detect all 13 Sentinel attacks, verify the attestation and transparency log, propagate revocation from `earthspace-raw-observations-001` to `earthspace-finding-001`, and let Observatory answer `impact_of()` without understanding seismic hazard, tectonic interpretation, or geospatial domain theory.

The claim is intentionally descriptive and qualified. It records what the declared transformation and summary computed; it is not a seismic hazard forecast or a claim about future earthquakes.

## Reproduce

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/earthspace/earthspace_proof.py \
  examples/earthspace/data/usgs_earthquakes_2024-01-01_m5.json
```

The generated bundle and Sentinel output are ignored local proof artifacts. The fetched GeoJSON fixture remains committed with its query URL and SHA-256 identity available through the normal Git history.

## References

[1]: https://earthquake.usgs.gov/fdsnws/event/1/ "USGS Earthquake Catalog FDSN Event Web Service API Documentation"
