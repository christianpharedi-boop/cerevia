from __future__ import annotations

import copy
import unittest
from pathlib import Path

from cerevia.interoperability.conformance import validate_cross_domain_composition, validate_profile, validate_profiles
from cerevia.interoperability.cross_domain import compose_cross_domain_bundle, load_bundle
from cerevia.interoperability.profile import EvidenceInteroperabilityProfile
from cerevia.interoperability.reference_profiles import REFERENCE_PROFILES


class InteroperabilityConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.bundles = {"neuroscience": load_bundle(root / "examples/bids_eeg/verification_bundle.json"), "proteomics": load_bundle(root / "examples/proteomics/proteomics_bundle.json"), "earthspace": load_bundle(root / "examples/earthspace/earthspace_bundle.json")}
        cls.results = validate_profiles(REFERENCE_PROFILES, cls.bundles)
        cls.cross_bundle, _, _ = compose_cross_domain_bundle(cls.bundles)
        cls.cross_result = validate_cross_domain_composition(cls.cross_bundle, REFERENCE_PROFILES)

    def test_all_reference_adapters_are_conformant(self):
        self.assertTrue(all(result.conformant for result in self.results.values()), {domain: result.to_dict() for domain, result in self.results.items()})
        self.assertTrue(self.cross_result.conformant, self.cross_result.to_dict())
        for result in self.results.values():
            self.assertIn("evidence_contract:source_identity", result.checks)
            self.assertIn("lineage_contract:observable_lineage", result.checks)
            self.assertIn("verification_contract:independent_bundle", result.checks)
            self.assertIn("claim_contract:required_fields", result.checks)
            self.assertIn("invalidation_contract:downstream_impact", result.checks)

    def test_profile_round_trip_is_stable(self):
        for profile in REFERENCE_PROFILES.values():
            self.assertEqual(profile, EvidenceInteroperabilityProfile.from_dict(profile.to_dict()))

    def test_profile_is_immutable(self):
        with self.assertRaises(Exception):
            REFERENCE_PROFILES["neuroscience"].domain = "other"  # type: ignore[misc]

    def test_missing_claim_field_is_rejected(self):
        bundle = copy.deepcopy(self.bundles["earthspace"])
        final = next(record for record in bundle["artifacts"] if record["artifact_id"] == "earthspace-finding-001")
        claim_id = final["payload"]["analysis_id"]
        claim = next(record for record in bundle["artifacts"] if record["artifact_id"] == claim_id)
        del claim["payload"]["experimental_context"]
        result = validate_profile(REFERENCE_PROFILES["earthspace"], bundle)
        self.assertFalse(result.conformant)
        self.assertTrue(any("claim_contract:missing:experimental_context" in failure for failure in result.failures))


if __name__ == "__main__":
    unittest.main()
