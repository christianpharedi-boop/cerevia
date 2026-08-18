# CEREVIA V1.3 Proteomics Domain Transplant

V1.3 is an architecture transplant test, not a neuroscience feature. The adapter consumes a compact protein-level expression table derived from the public `tidyproteomics` repository and maps it to the shared CEREVIA chain:

> **Raw assay → immutable artifact → transformation → quantification → analysis → inference → claim → finding**

The public source is the `hela_proteins` expression table from [`jeffsocal/tidyproteomics`](https://github.com/jeffsocal/tidyproteomics), a package for quantitative proteomic post-analysis [1] [2]. The repository commit used for the fixture is recorded in adapter metadata, and the checked-in subset has its own content identity through the normal CEREVIA artifact mechanism.

## Adapter boundary

The proteomics adapter understands protein identifiers, control/knockdown abundance columns, finite-value quality checks, mean abundance, and log2 response ratios. It does not implement a second provenance system, identity mechanism, verifier, claim framework, mutable database, AI interpretation layer, or replacement evidence graph.

The adapter uses the same `Artifact.derive`, `ArtifactCatalog`, manifest, bundle verifier, Sentinel attack suite, Ed25519 attestation, transparency log, revocation registry, and Observatory contracts used by the neuroscience proof.

## Acceptance criterion

The transplant is accepted only if the shared trust semantics remain unchanged. In the proof, the same 13 Sentinel attacks are detected, the independent bundle verifier returns `VERIFIED`, attestation and transparency-log checks succeed, revocation of `proteomics-raw-assay-001` propagates to `proteomics-finding-001`, and Observatory answers `impact_of()` without understanding peptides, spectra, proteins, or abundance matrices.

A qualified claim remains a qualified claim. The descriptive result demonstrates evidence plumbing and dependency integrity; it does not establish a biological conclusion or population-level effect.

## Reproduce

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/transplants/proteomics_proof.py \
  examples/transplants/data/hela_proteins_subset.csv
```

The generated bundle and Sentinel output are local proof artifacts and are ignored by Git. The compact source fixture remains committed so the proof can be repeated independently.

## References

[1]: https://github.com/jeffsocal/tidyproteomics "tidyproteomics source repository"
[2]: https://jeffsocal.github.io/tidyproteomics/ "tidyproteomics documentation"
