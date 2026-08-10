# -*- coding: utf-8 -*-
import pathlib
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

from hwp_palette.model import csat_ai_palette as csat
from hwp_palette.model.csat_reference_fragments import build_reference_fragment


class CsatAiPaletteTest(unittest.TestCase):
    def test_팔레트_이름과_AI_슬롯이_명시적이다(self):
        self.assertEqual(csat.PALETTE_NAME, "수능양식 ai")
        self.assertEqual(csat.FORM_SLOT_NAMES, ("시험지머리문구", "영역과목명"))
        labels = set()
        names = set()
        for spec in csat.TEMPLATE_SPECS:
            name, label, slots = spec["name"], spec["label"], spec["slots"]
            self.assertTrue(slots)
            self.assertEqual(len(slots), len(set(slots)))
            self.assertNotIn(name, names)
            self.assertNotIn(label, labels)
            self.assertIn("range", spec)
            self.assertNotIn("source", spec)
            names.add(name)
            labels.add(label)

    def test_학교_시험지_물감을_소스로_재사용하지_않는다(self):
        old_school_paints = {
            "합답형1사진3선지", "합답형2사진3선지", "합답형실험3선지",
            "소1사진", "소2사진", "대1사진", "보기", "1행답안", "2행답안",
            "3행답안", "5행답안", "3행답안표", "5행답안표",
        }
        self.assertTrue(all(spec.get("source") not in old_school_paints
                            for spec in csat.TEMPLATE_SPECS))
        self.assertEqual(
            {spec["key"] for spec in csat.TEMPLATE_SPECS},
            {"diagram_hapdap", "direct", "hapdap", "people", "experiment", "comparison", "data_table"},
        )

    def test_그림합답형은_원본_그래프와_배점문단을_보존한다(self):
        reference = pathlib.Path("data/csat_ai_analysis/reference.hwpx")
        if not reference.exists():
            self.skipTest("로컬 기준 HWPX가 없음")
        spec = next(item for item in csat.TEMPLATE_SPECS
                    if item["key"] == "diagram_hapdap")
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "diagram.hwpx"
            build_reference_fragment(reference, output, spec)
            with zipfile.ZipFile(output) as archive:
                xml = archive.read("Contents/section0.xml").decode("utf-8")
            self.assertIn("<hp:pic", xml)
            self.assertIn("[\\\\]", xml)
            self.assertGreaterEqual(xml.count("\\\\"), len(spec["slots"]))

    def test_그림만_흰색으로_바꾸고_XML은_보존한다(self):
        reference = pathlib.Path("data/csat_ai_analysis/reference.hwpx")
        if not reference.exists():
            self.skipTest("로컬 기준 HWPX가 없음")
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "blank.hwpx"
            csat.build_blank_reference(reference, output)
            with zipfile.ZipFile(reference) as before, zipfile.ZipFile(output) as after:
                self.assertEqual(before.read("Contents/section0.xml"), after.read("Contents/section0.xml"))
                self.assertEqual(before.read("Contents/masterpage0.xml"), after.read("Contents/masterpage0.xml"))
                image_names = [name for name in before.namelist() if name.startswith("BinData/image")]
                self.assertEqual(len(image_names), 21)
                for name in image_names:
                    with Image.open(after.open(name)) as image:
                        extrema = image.convert("RGB").getextrema()
                        self.assertTrue(all(lo >= 250 and hi == 255 for lo, hi in extrema))

    def test_합답형은_원본의_보기표와_그림자리를_보존한다(self):
        reference = pathlib.Path("data/csat_ai_analysis/reference.hwpx")
        if not reference.exists():
            self.skipTest("로컬 기준 HWPX가 없음")
        spec = next(item for item in csat.TEMPLATE_SPECS if item["key"] == "hapdap")
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "hapdap.hwpx"
            build_reference_fragment(reference, output, spec)
            with zipfile.ZipFile(output) as archive:
                xml = archive.read("Contents/section0.xml").decode("utf-8")
            self.assertGreaterEqual(xml.count("\\\\"), len(spec["slots"]))
            self.assertIn("rowCnt=\"3\"", xml)
            self.assertIn("colCnt=\"3\"", xml)
            self.assertIn("<hp:pic", xml)
            self.assertNotIn("pageBreak=\"1\"", xml)
            self.assertNotIn("columnBreak=\"1\"", xml)

    def test_직접형_질문은_수식용_10pt가_아닌_수능본문_크기다(self):
        reference = pathlib.Path("data/csat_ai_analysis/reference.hwpx")
        if not reference.exists():
            self.skipTest("로컬 기준 HWPX가 없음")
        spec = next(item for item in csat.TEMPLATE_SPECS if item["key"] == "direct")
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "direct.hwpx"
            build_reference_fragment(reference, output, spec)
            with zipfile.ZipFile(output) as archive:
                xml = archive.read("Contents/section0.xml").decode("utf-8")
                header_xml = archive.read("Contents/header.xml").decode("utf-8")
            self.assertNotIn("<hp:pic", xml)
            self.assertIn("배점", spec["slots"])
            # 질문 슬롯 run은 기준 문서의 11.48pt charPr 18을 사용한다.
            root = ET.fromstring(xml)
            local = lambda node: node.tag.rsplit("}", 1)[-1]
            runs = [node for node in root.iter()
                    if local(node) == "run" and node.get("charPrIDRef") == "18"]
            self.assertTrue(any("\\\\" in "".join(run.itertext()) for run in runs))
            numbered = next(node for node in root if node.get("styleIDRef") == "0"
                            and "\\\\. \\\\" in "".join(node.itertext()))
            header = ET.fromstring(header_xml)
            para_id = numbered.get("paraPrIDRef")
            para_pr = next(node for node in header.iter()
                           if local(node) == "paraPr" and node.get("id") == para_id)
            values = {(local(node), node.get("value")) for node in para_pr.iter()}
            self.assertIn(("left", "1130"), values)
            self.assertIn(("intent", "-1130"), values)
            self.assertIn(("lineSpacing", "145"), values)
            properties = next(node for node in header.iter()
                              if local(node) == "paraProperties")
            self.assertEqual(int(properties.get("itemCnt")),
                             sum(local(node) == "paraPr" for node in list(properties)))
            paragraphs = [node for node in root if local(node) == "p"]
            score = next(node for node in paragraphs if "[\\\\]" in "".join(node.itertext()))
            score_para_pr = next(node for node in header.iter()
                                 if local(node) == "paraPr"
                                 and node.get("id") == score.get("paraPrIDRef"))
            score_align = next(node for node in score_para_pr.iter()
                               if local(node) == "align")
            self.assertEqual(score_align.get("horizontal"), "RIGHT")
            self.assertEqual(paragraphs.index(score), paragraphs.index(numbered) + 2)


if __name__ == "__main__":
    unittest.main()
