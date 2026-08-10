# -*- coding: utf-8 -*-
import pathlib
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hwp_palette.model import reference_exam_palette as refpal  # noqa: E402


class ReferenceTransformTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = pathlib.Path(
            r"C:\Users\user\Desktop\Exam Project\대왕중 시험문제 복원.hwpx")

    def setUp(self):
        if not self.reference.exists():
            self.skipTest("로컬 참고 HWPX가 없음")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @staticmethod
    def _local(elem):
        return elem.tag.rsplit("}", 1)[-1]

    def _section(self, path):
        with zipfile.ZipFile(path) as zf:
            return ET.fromstring(zf.read("Contents/section0.xml"))

    def test_문항_하나와_그림없는_12슬롯을_만든다(self):
        out = refpal.build_hwpx_variants(self.reference, self.tmp.name)
        root = self._section(out["template"])
        tables = [e for e in root.iter() if self._local(e) == "tbl"]
        pics = [e for e in root.iter() if self._local(e) == "pic"]
        cells = [e for e in root.iter() if self._local(e) == "tc"]
        image_size = next(e for e in cells[3].iter() if self._local(e) == "cellSz")
        text = "".join(root.itertext())
        self.assertEqual(len(tables), 1)
        self.assertEqual((tables[0].get("rowCnt"), tables[0].get("colCnt")), ("9", "16"))
        self.assertEqual(pics, [])
        self.assertEqual(image_size.get("height"), "14386")
        for name in refpal.SLOT_NAMES:
            self.assertIn(f"\\{name}\\", text)
        self.assertIn("<보 기>", text)
        self.assertNotIn("〈보 기〉", text)
        self.assertIn(" \\선지3\\", text)
        self.assertIn("\\선지5\\ ", text)

    def test_양식은_쪽설정과_2단을_보존하고_본문표시만_남긴다(self):
        out = refpal.build_hwpx_variants(self.reference, self.tmp.name)
        root = self._section(out["form"])
        text = "".join(root.itertext())
        tables = [e for e in root.iter() if self._local(e) == "tbl"]
        col = next(e for e in root.iter() if self._local(e) == "colPr")
        page = next(e for e in root.iter() if self._local(e) == "pagePr")
        margin = next(e for e in root.iter() if self._local(e) == "margin")
        self.assertEqual(tables, [])
        self.assertEqual(text, "\\본문\\")
        self.assertEqual((col.get("colCount"), col.get("sameGap")), ("2", "2267"))
        self.assertEqual((page.get("width"), page.get("height")), ("59528", "84186"))
        self.assertEqual((margin.get("left"), margin.get("right")), ("1984", "1984"))

    def test_전체_원안지_양식은_머리표_꼬리말_쪽틀을_보존한다(self):
        page_form = pathlib.Path("data/reference_analysis/exam_form_source.hwpx")
        if not page_form.exists():
            self.skipTest("원안지 양식 HWPX가 없음")
        out = refpal.build_hwpx_variants(
            self.reference, self.tmp.name, page_form_hwpx=page_form)
        root = self._section(out["form"])
        text = "".join(root.itertext())
        tables = [e for e in root.iter() if self._local(e) == "tbl"]
        col = next(e for e in root.iter() if self._local(e) == "colPr")
        margin = next(e for e in root.iter() if self._local(e) == "margin")
        self.assertEqual(len(tables), 1)
        self.assertEqual((col.get("colCount"), col.get("sameGap")), ("2", "1133"))
        self.assertEqual((margin.get("left"), margin.get("right")), ("2834", "2834"))
        for name in ("과목", "학년", "고사구분", "과목코드", "시행일시", "본문"):
            self.assertIn(f"\\{name}\\", text)
        self.assertIn("대왕중학교 ( 2 )학년 ( 과학 )과", text)
        self.assertNotIn("문제_스타일", text)
        score = self._section(out["score"])
        score_text = "".join(score.itertext())
        self.assertEqual(len([e for e in score.iter() if self._local(e) == "tbl"]), 1)
        for name in ("배점제목", "배점1", "배점2"):
            self.assertIn(f"\\{name}\\", score_text)

    def test_AI_문항유형_이름표_수는_원형_물감과_일치한다(self):
        expected = {
            "학교정답0사진1선지": 8,
            "학교합답0사진5선지": 11,
            "학교합답2사진5선지": 14,
        }
        for spec in refpal.REFERENCE_TEMPLATE_SPECS:
            self.assertEqual(len(spec["slots"]), expected[spec["source"]])
            self.assertEqual(len(set(spec["slots"])), len(spec["slots"]))


if __name__ == "__main__":
    unittest.main()
