import tempfile
import unittest
from pathlib import Path

from core.token_registry import ensure_token_registry, resolve_token, registry_path, route_summary, token_summary


class TokenRegistryTests(unittest.TestCase):
    def test_registry_is_created_and_summarized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = ensure_token_registry(root)

            self.assertTrue(registry_path(root).exists())
            summary = token_summary(registry)
            self.assertGreaterEqual(summary["token_count"], 6)
            self.assertIn("C:\\mini_ark\\asset_pipeline\\inbox", summary["reserved_roots"])
            policies = summary["policies"]
            self.assertIn("Always observe", policies["ambient_congruence_policy"])
            self.assertIn("Foreground responsiveness wins", policies["resource_doctrine"])
            self.assertIn("Prompts are for real judgment", policies["prompt_policy"])
            self.assertIn("index and manifest updates", policies["auto_apply_policy"])
            self.assertIn("folder deletion", policies["do_not_auto_apply_policy"])

    def test_alias_resolution_supports_old_and_new_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ensure_token_registry(Path(tmp))

            journey = resolve_token(registry, "mini_ark")
            corestone = resolve_token(registry, "opalstone")
            wishstone = resolve_token(registry, "asset ark")
            carebloom = resolve_token(registry, "CareBloom")

            self.assertIsNotNone(journey)
            self.assertEqual(journey[0], "journey")
            self.assertIsNotNone(corestone)
            self.assertEqual(corestone[0], "corestone")
            self.assertIsNotNone(wishstone)
            self.assertEqual(wishstone[0], "wishstone")
            self.assertIsNotNone(carebloom)
            self.assertEqual(carebloom[0], "carebloomos")

    def test_route_summary_distinguishes_routes_from_representations(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ensure_token_registry(Path(tmp))
            summary = route_summary(registry)

            routed_ids = {token["id"] for token in summary["tokens"]}
            self.assertIn("journey", routed_ids)
            self.assertIn("wishstone", routed_ids)
            self.assertIn("carebloomos", routed_ids)
            carebloom = next(token for token in summary["tokens"] if token["id"] == "carebloomos")
            self.assertEqual(carebloom["representations"]["canonical"], "R:\\Projects\\CareBloomOS")
            self.assertIn("source of truth", summary["rule"])
            self.assertIn("natural canonical home", summary["routing_policy"])


if __name__ == "__main__":
    unittest.main()
