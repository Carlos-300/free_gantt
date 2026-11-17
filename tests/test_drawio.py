import html
import unittest
import xml.etree.ElementTree as ET
from datetime import date

from gantt.drawio import DAY_W, LABEL_W, task_label, to_drawio
from gantt.models import Project


def _cells(xml: str) -> list[ET.Element]:
    return ET.fromstring(xml).findall(".//mxCell")


class DrawioExportTest(unittest.TestCase):
    def test_empty_project_is_valid_xml(self):
        cells = _cells(to_drawio(Project("Vacío")))
        self.assertEqual(cells[2].get("value"), "Vacío")

    def test_task_label_includes_responsible(self):
        p = Project()
        con = p.add_task("Diseño", date(2026, 1, 1), responsible="Ana")
        sin = p.add_task("QA", date(2026, 1, 1))
        self.assertEqual(task_label(con), "Diseño [Ana]")
        self.assertEqual(task_label(sin), "QA")

    def test_bars_positioned_by_date_and_months_cover_range(self):
        p = Project("P & <Q>")
        p.add_task("A", date(2026, 1, 30), duration=2, progress=50, responsible="Ana")
        p.add_task("B", date(2026, 2, 3), duration=3)
        cells = _cells(to_drawio(p))
        valores = [html.unescape(c.get("value") or "") for c in cells]
        self.assertIn("P & <Q>", valores)  # special chars survive XML + HTML escaping
        self.assertIn("A [Ana]", valores)
        self.assertEqual([v for v in valores if v and "2026" in v], ["enero 2026", "febrero 2026"])

        geo = {c.get("value"): c.find("mxGeometry") for c in cells}
        b = geo["0 %"]
        self.assertEqual(float(b.get("x")), LABEL_W + 4 * DAY_W)  # Feb 3 is 4 days after Jan 30
        self.assertEqual(float(b.get("width")), 3 * DAY_W)


if __name__ == "__main__":
    unittest.main()
