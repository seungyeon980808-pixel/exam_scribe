# -*- coding: utf-8 -*-
"""EXE/portable/installer 배포 규약.

소스 실행은 자원을 바로 읽으므로 spec 누락을 못 잡는다. 배포형에서만
아이콘·엑셀 틀이 사라지는 회귀를 문자 규약으로 막는다.
"""
import pathlib
import os
import tempfile
import unittest
import zipfile

import build_release


ROOT = pathlib.Path(__file__).resolve().parent.parent


class SpecTest(unittest.TestCase):

    def test_실행_자원을_모두_담는다(self):
        spec = (ROOT / "hwp_palette.spec").read_text(encoding="utf-8")
        self.assertIn('("assets/icons", "assets/icons")', spec)
        self.assertIn("excel_block_template.xlsm", spec)

    def test_onedir_배포다(self):
        spec = (ROOT / "hwp_palette.spec").read_text(encoding="utf-8")
        self.assertIn("exclude_binaries=True", spec)
        self.assertIn("COLLECT(", spec)

    def test_설치형은_배포_폴더를_통째로_넣는다(self):
        iss = (ROOT / "installer" / "hwp_palette.iss").read_text(encoding="utf-8")
        self.assertIn(r"dist\hwp_palette\*", iss)
        self.assertIn("recursesubdirs", iss)

    def test_사용자_계정_Inno_Setup도_찾는다(self):
        expected = str(pathlib.Path(os.environ.get("LOCALAPPDATA", ""))
                       / "Programs" / "Inno Setup 6" / "ISCC.exe")
        self.assertIn(expected, build_release._ISCC_CANDIDATES)


class PortableZipTest(unittest.TestCase):

    def test_onedir을_상위_폴더와_함께_묶는다(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            app = root / "hwp_palette"
            (app / "_internal" / "assets" / "icons").mkdir(parents=True)
            (app / "hwp_palette.exe").write_bytes(b"exe")
            (app / "_internal" / "assets" / "icons" / "dock-24.png").write_bytes(b"png")
            old_dist = build_release.DIST
            build_release.DIST = root
            try:
                out = build_release.make_portable_zip(app)
            finally:
                build_release.DIST = old_dist
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
                top = f"HwpPalette-{build_release.appinfo.VERSION}"
                self.assertIn(f"{top}/hwp_palette.exe", names)
                self.assertIn(f"{top}/_internal/assets/icons/dock-24.png", names)
                self.assertIsNone(zf.testzip())


if __name__ == "__main__":
    unittest.main()
