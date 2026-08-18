# CEREVIA V2.1 Institutional Exchange Profile

V2.1 operationalizes exchange between institutions without requiring either institution to trust the other’s execution environment. The exchange layer signs protocol metadata and references evidence out of band by content hash. It is not a data warehouse and does not become the custodian of participant-level scientific payloads.

> **Here is the evidence package. Verify it yourself.**

## Institutional exchange envelope

An `ExchangePackage` contains only the following trust-visible fields:

| Field | Purpose |
|---|---|
| `sender_institution_id` and `recipient_institution_id` | Explicit exchange participants. |
| `signer_key_id` | Key lifecycle reference used to validate the signature. |
| `bundle_sha256` | Content identity of the separately exchanged CEREVIA bundle. |
| `bundle_locator` | Out-of-band location or exchange handle; it is not fetched by the trust layer. |
| `protocol_metadata` | Protocol and bundle version identifiers. |
| `policy` | Access class, retention, verification, revocation, audit, domain, and privacy requirements. |
| `revocation_snapshot` | Sender’s declared revocation-check status at exchange time. |
| `audit_head` | Hash-chain position for the exchange audit history. |
| `signature` | Ed25519 signature over all unsigned envelope fields. |

Raw observations, participant identifiers, biological measurements, and other sensitive payloads are not copied into the envelope. The bundle may be stored in a separately governed repository, object store, or restricted exchange channel.

## Governance contracts

The profile defines key ownership and rotation through `InstitutionKeyRing`. Active keys may sign; retired keys are rejected for new verification. Rotation records preserve the prior key identifier and effective time. The profile also requires a retention deadline and supports `public`, `restricted`, and `confidential` access classes.

A recipient may require bundle verification, revocation-status inspection, audit-chain integrity, and domain allow-listing. These checks are policy decisions represented in the signed package; they do not change the Evidence Core or V1.6 interoperability semantics.

## Audit and revocation

`AuditLog` is an append-only hash chain for package preparation, receipt, verification, key rotation, and other institution-defined events. A recipient validates both the chain and the package’s declared audit head. Revocation is represented as a required snapshot status rather than as an implicit trust assumption. The recipient still independently verifies the received bundle and may apply its own current Sentinel/Observatory state.

## Blind exchange proof

The reference proof simulates Institution A sending a cross-domain bundle to Institution B. Institution B verifies the signed envelope, bundle content identity, independent bundle verification, domain policy, retention, revocation snapshot, and audit history. The proof then rotates Institution A’s key, accepts the new signer, and rejects a package signed with the retired key.

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/institutional_pilot/institutional_exchange_proof.py
PYTHONPATH=. python3 -m unittest tests.test_institutional_exchange -v
```

The institutional profile is an operational exchange contract, not legal, ethics, privacy, or records-management advice. Real deployments must map these fields to their own approved governance policies and data-protection controls.

## References

[1]: https://github.com/christianpharedi-boop/cerevia "CEREVIA reference implementation"
[2]: https://github.com/christianpharedi-boop/cerevia/blob/main/docs/evidence-interoperability-v1.md "CEREVIA V1.6 Evidence Interoperability Specification"
