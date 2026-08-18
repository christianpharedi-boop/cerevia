# CEREVIA External Institutional Pilot V2.2

This release prepares, but does not claim to execute, the first external institutional pilot. The repository can generate a governed exchange fixture, provide adversarial variants, and compare two independently produced answer records. A genuine external research group must still run the exchange without privileged access to CEREVIA’s internal implementation or development reasoning.

## Pilot handoff package

The external participant should receive the public V1.6 specification, V2.0 external implementation, V2.1 exchange profile, verification tools, test fixtures, and this acceptance schema. They should independently implement or operate a verifier, receive the out-of-band bundle and signed package, and return only protocol-level answers and failure records. Sensitive scientific payloads remain under the institutions’ own governance.

## Blind exchange scenarios

The prepared proof includes one valid package and three deliberately compromised variants:

| Scenario | Deliberate change | Expected result |
|---|---|---|
| `valid` | No mutation | Authentic package and independently verified bundle. |
| `altered_bundle_hash` | Declared bundle hash changed without resigning | Authentication failure and investigation. |
| `stale_revocation` | Revocation snapshot replaced with unchecked stale state | Signature or revocation-policy failure and investigation. |
| `wrong_recipient` | Recipient identity changed after signing | Signature or recipient-policy failure and investigation. |

The same answer schema is extracted for both simulated institutions, and `compare_answers()` reports field-level disagreements rather than collapsing them into a boolean.

## Independent answer schema

Each participant answers the following fields:

| Field | Meaning |
|---|---|
| `package_authentic` | Whether signer, recipient, signature, policy, retention, audit, and revocation checks pass. |
| `bundle_verified` | Whether the evidence bundle independently verifies. |
| `lineage_node_ids` | Complete observable lineage for the final finding. |
| `claim_statement` | The statement represented by the finding. |
| `uncertainty` | Declared uncertainty information, without inventing new scientific interpretation. |
| `historical_event_count` | Events visible at the requested time boundary. |
| `revoked_source_ids` | Sources considered revoked. |
| `affected_finding_ids` | Findings downstream of revoked sources. |
| `unaffected_finding_ids` | Findings outside the revocation blast radius. |
| `failures` | Explicit verification or policy failures. |

The primary success criterion is **inter-institution agreement**: two independently operated systems produce identical answers for the same protocol artifacts, including after adversarial mutations.

## Reproduce the prepared kit

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/institutional_pilot/pilot_proof.py
PYTHONPATH=. python3 -m unittest tests.test_pilot_kit -v
```

The proof reports `PREPARED_NOT_EXECUTED_EXTERNALLY` by design. It must not be presented as evidence that an external institution has used CEREVIA. That statement can only be made after an actual independent team conducts the blind exchange and returns its signed or otherwise auditable result set.

> **The next commit should come from someone who is not the protocol author.**

## References

[1]: https://github.com/christianpharedi-boop/cerevia "CEREVIA reference implementation"
[2]: https://github.com/christianpharedi-boop/cerevia/blob/main/docs/institutional-exchange-v2.1.md "CEREVIA V2.1 Institutional Exchange Profile"
