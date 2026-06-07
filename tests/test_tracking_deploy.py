import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.tracking_deploy import TrackingDeployExporter, build_tracking_deploy_manifest


class TrackingDeployTests(unittest.TestCase):
    def test_manifest_lists_server_side_env_and_public_endpoints(self):
        manifest = build_tracking_deploy_manifest(public_base_url="https://revenue.example")

        self.assertIn("SUPABASE_URL", manifest["required_env"])
        self.assertIn("SUPABASE_KEY", manifest["required_env"])
        self.assertIn("CONVERSION_WEBHOOK_TOKEN", manifest["required_env"])
        self.assertEqual(manifest["endpoints"]["click"], "https://revenue.example/click")
        self.assertEqual(
            manifest["provider_webhooks"]["stripe"],
            "https://revenue.example/webhooks/conversion/stripe",
        )
        self.assertNotIn("buymeacoffee", manifest["provider_webhooks"])
        self.assertEqual(manifest["docker"]["build_command"], "docker build -f out/tracking-deploy/Dockerfile -t infinite-revenue-tracker .")

    def test_exporter_writes_docker_env_manifest_and_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = TrackingDeployExporter(
                Path(directory) / "tracking-deploy",
                public_base_url="https://revenue.example/",
            )

            paths = exporter.export()

            output_dir = Path(directory) / "tracking-deploy"
            dockerfile = (output_dir / "Dockerfile").read_text(encoding="utf-8")
            env_example = (output_dir / ".env.tracking.example").read_text(encoding="utf-8")
            markdown = (output_dir / "DEPLOY_TRACKING_APP.md").read_text(encoding="utf-8")
            manifest = json.loads((output_dir / "tracking_deploy.json").read_text(encoding="utf-8"))

        self.assertEqual(
            [path.name for path in paths],
            ["Dockerfile", ".env.tracking.example", "tracking_deploy.json", "DEPLOY_TRACKING_APP.md"],
        )
        self.assertIn("COPY farm_loop ./farm_loop", dockerfile)
        self.assertIn("python -m farm_loop.http_app --host 0.0.0.0", dockerfile)
        self.assertIn("SUPABASE_KEY=", env_example)
        self.assertIn("CONVERSION_WEBHOOK_TOKEN=", env_example)
        self.assertIn("# Tracking App Deploy", markdown)
        self.assertIn("https://revenue.example/webhooks/conversion/stripe", markdown)
        self.assertEqual(manifest["endpoints"]["buymeacoffee_webhook"], "https://revenue.example/webhooks/buymeacoffee")


if __name__ == "__main__":
    unittest.main()
