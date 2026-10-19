from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
from pathlib import Path

import pourbase as pb
from pourbase.mcp_server import Tools

ROOT = Path(__file__).resolve().parents[1]


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tools = Tools()

    def test_results_are_json_with_sources(self) -> None:
        species = self.tools.get_species("Fe")
        json.dumps(species)
        hematite = next(item for item in species if item["record_id"] == "gfe-fe-fe2o3-q+0-solid-hematite")
        self.assertIn("Nuclear Energy Agency", hematite["source"])
        record = self.tools.get_record("gfe-fe-fe2o3-q+0-solid-hematite")
        json.dumps(record)
        self.assertTrue(record["reported"])

    def test_diagram_matches_the_package(self) -> None:
        result = self.tools.calculate_diagram("Fe")
        json.dumps(result)
        direct = pb.calculate(pb.Scenario("Fe", allow_incomplete=True))
        self.assertEqual({item["record_id"] for item in result["stable_species"]},
                         {item.record_id for item in direct.stable_species})
        self.assertAlmostEqual(sum(item["share_of_diagram"] for item in result["stable_species"]), 1.0, places=3)

    def test_probe_reports_margin_and_ligands_work(self) -> None:
        point = self.tools.probe_point("Fe", 7.0, 0.0)
        self.assertEqual(point["species"], "Fe₂O₃")
        self.assertIsNotNone(point["margin_kJ_mol_metal"])
        result = self.tools.calculate_diagram(
            "Cu", ligands=[{"ligand_id": "chloride-cl", "log10_free_activity": -1.0}])
        self.assertTrue(any("Cl" in item["species"] for item in result["stable_species"]))

    def test_policy_comparison(self) -> None:
        text = (ROOT / "src" / "pourbase" / "data" / "selection-policy.toml").read_text(encoding="utf-8")
        self.assertEqual(self.tools.compare_policy(text), [])


@unittest.skipUnless(__import__("importlib").util.find_spec("mcp"), "mcp is not installed")
class ServerTests(unittest.TestCase):
    def test_stdio_session(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))

        async def session() -> tuple[list[str], str, str]:
            parameters = StdioServerParameters(command=sys.executable, args=["-m", "pourbase.mcp_server"],
                                               env=environment)
            async with stdio_client(parameters) as (read, write), ClientSession(read, write) as client:
                await client.initialize()
                names = [tool.name for tool in (await client.list_tools()).tools]
                probe = await client.call_tool("probe_point", {"symbol": "Fe", "pH": 7.0, "U_V": 0.0})
                image = await client.call_tool("render_diagram", {"symbol": "Cu"})
                return names, probe.content[0].text, image.content[0].type

        names, probe, kind = asyncio.run(session())
        self.assertIn("calculate_diagram", names)
        self.assertEqual(json.loads(probe)["record_id"], "gfe-fe-fe2o3-q+0-solid-hematite")
        self.assertEqual(kind, "image")


if __name__ == "__main__":
    unittest.main()
