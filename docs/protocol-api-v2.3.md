# CEREVIA V2.3 Protocol API

The V2.3 Protocol API is a thin HTTP interface over the frozen Evidence Core, Sentinel, and Observatory contracts. It does not create new evidence semantics, accounts, a mutable scientific database, a hosted data repository, or a cloud custody layer.

## Boundary

The API reads configured protocol artifacts from an out-of-band bundle path or verifies a transient bundle supplied in a request. It does not write evidence, rewrite manifests, persist uploaded bundles, or silently cache participant data. The later Institutional Exchange API remains a separate boundary for signed package operations, key lifecycle, and audit workflows.

> **Same core contracts. Different interface.**

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/verify` | Verify a transient bundle and optional Sentinel result. |
| `POST` | `/verify/bundle` | Alias for the explicit bundle-verification operation. |
| `GET` | `/findings/{id}` | Return a finding, claim reference, verification state, and current status. |
| `GET` | `/findings/{id}/lineage` | Return lineage node IDs, nodes, and graph edges. |
| `GET` | `/findings/{id}/evidence` | Return the claim and supporting evidence references/hashes. |
| `GET` | `/findings/{id}/verification` | Return independent verification and optional Sentinel status. |
| `GET` | `/findings/{id}/history` | Return time-aware transparency and revocation history. |
| `POST` | `/impact` | Compute downstream invalidation impact for an artifact. |
| `GET` | `/revocations` | List configured revocation records, optionally filtered by subject. |
| `GET` | `/attestations` | List configured attestations, optionally filtered by subject. |
| `GET` | `/health` | Report read-only service status and the separate exchange boundary. |

The query endpoints require `CEREVIA_BUNDLE_PATH` and optionally `CEREVIA_SENTINEL_PATH`. They load the configured files per request. The verification endpoints accept a JSON body shaped as `{ "bundle": {...}, "sentinel": {...} }` and perform transient verification.

When a Sentinel payload is supplied, client-provided summary fields are returned only under `sentinel.client_reported`. They are never emitted as server-verified top-level fields. The API independently verifies the signed attestation, binds it to the submitted bundle and specification, and verifies the hash-linked transparency log; those results appear under `sentinel.server_verified`.

`GET /findings/{id}/verification` returns a bundle verification report explicitly scoped to the requested finding lineage. The frozen verifier still validates the serialized bundle as a whole; the response names that scope rather than implying a separate verifier for one artifact.

Authentication is intentionally not implemented in this pre-pilot read-only boundary. The `/health` response identifies `institutional_exchange_api` as a separate future boundary. Before deployment beyond controlled validation, a future release must add authenticated access, authorization policy, and audit requirements without placing credentials or sensitive scientific payloads in the trust layer.

## Run locally

Install the API extras and start the read-only service:

```bash
pip install -e '.[api]'
export CEREVIA_BUNDLE_PATH=examples/substrate_stress_tests/cross_domain_bundle.json
uvicorn cerevia.api:app --host 127.0.0.1 --port 8000
```

Then inspect the machine-readable contract at `/docs` or call:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/findings/cross-domain-finding-001/lineage
curl -X POST http://127.0.0.1:8000/impact \
  -H 'content-type: application/json' \
  -d '{"artifact_id":"proteomics-raw-assay-001"}'
```

A missing configured bundle returns `503`; an unknown finding or artifact returns `404`; malformed protocol objects return `400` or `422`. These are interface errors around existing protocol results, not new scientific status values.

## References

[1]: https://github.com/christianpharedi-boop/cerevia "CEREVIA reference implementation"
[2]: https://github.com/christianpharedi-boop/cerevia/blob/main/docs/observatory.md "CEREVIA Observatory contracts"
[3]: https://github.com/christianpharedi-boop/cerevia/blob/main/docs/institutional-exchange-v2.1.md "CEREVIA Institutional Exchange Profile"
