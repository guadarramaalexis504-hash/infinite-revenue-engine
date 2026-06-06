import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.assets import AssetDraft
from farm_loop.launch_queue import LaunchQueueExporter, build_launch_queue
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="microtool_seo", source="idea_catalog", external_id="tool-1"):
    return RevenueOpportunity(
        source=source,
        external_id=external_id,
        title="Supabase policy checker",
        url="file://ideas#tool-1",
        problem="Developers need RLS feedback.",
        tags=["supabase", "rls"],
        channel=channel,
        payout_estimate_usd=300,
        conversion_probability=0.08,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=45,
    )


def make_assets():
    return [
        AssetDraft(
            asset_type="microtool_spec",
            title="Microtool Spec",
            body_markdown="# Spec",
        ),
        AssetDraft(
            asset_type="landing_page_copy",
            title="Landing Copy",
            body_markdown="# Landing",
        ),
    ]


class LaunchQueueTests(unittest.TestCase):
    def test_build_launch_queue_prioritizes_activation_blockers(self):
        report = {
            "ready": False,
            "next_actions": [
                "Replace placeholder .env values: SUPABASE_KEY, OPENAI_API_KEY",
                "Add git remote origin",
            ],
        }

        tasks = build_launch_queue(
            [(make_opportunity(), make_assets())],
            activation_report=report,
        )

        self.assertGreater(len(tasks), 2)
        self.assertTrue(tasks[0].blocking)
        self.assertEqual(tasks[0].category, "activation")
        self.assertIn("Replace placeholder", tasks[0].title)
        self.assertLess(tasks[0].priority, tasks[-1].priority)

    def test_build_launch_queue_creates_safe_revenue_steps_per_opportunity(self):
        tasks = build_launch_queue([(make_opportunity(), make_assets())])
        titles = [task.title for task in tasks]

        self.assertIn("Review assets for Supabase policy checker", titles)
        self.assertIn("Publish owned page for Supabase policy checker", titles)
        self.assertIn("Connect payment/support CTA for Supabase policy checker", titles)
        self.assertIn("Measure clicks and conversions for Supabase policy checker", titles)
        for task in tasks:
            self.assertEqual(task.external_id, "tool-1")
            self.assertNotIn("Stack Overflow", task.detail)
            self.assertIn(task.status, {"blocked", "pending"})

    def test_build_launch_queue_keeps_stackexchange_as_discovery_only(self):
        opportunity = make_opportunity(channel="stackexchange", source="stackexchange", external_id="123")

        tasks = build_launch_queue([(opportunity, make_assets())])

        publish_task = next(task for task in tasks if task.category == "publish")
        self.assertIn("owned", publish_task.detail.lower())
        self.assertIn("Do not publish AI-generated answers", publish_task.detail)

    def test_launch_queue_exporter_writes_json_and_markdown(self):
        tasks = build_launch_queue([(make_opportunity(), make_assets())])

        with tempfile.TemporaryDirectory() as directory:
            written = LaunchQueueExporter(directory).export(tasks)
            output_dir = Path(directory)
            json_rows = json.loads((output_dir / "launch_queue.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "LAUNCH_QUEUE.md").read_text(encoding="utf-8")

        self.assertEqual(
            sorted(path.name for path in written),
            ["LAUNCH_QUEUE.md", "launch_queue.json"],
        )
        self.assertEqual(json_rows[0]["external_id"], "tool-1")
        self.assertIn("# Launch Queue", markdown)
        self.assertIn("Supabase policy checker", markdown)


if __name__ == "__main__":
    unittest.main()
