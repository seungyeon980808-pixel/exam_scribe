# -*- coding: utf-8 -*-
import pathlib
import unittest

from hwp_palette.typesetter_pack import contract, library_payload, load_pack


class TypesetterPackTest(unittest.TestCase):
    def test_csat_pack_is_self_contained_and_has_stable_contract(self):
        pack = load_pack(pathlib.Path("typesetting_packs/csat_science"))
        self.assertEqual(pack["version"], "0.1.0")
        self.assertEqual(contract(pack)["수능AI실제직접형"], 9)
        self.assertEqual(contract(pack)["수능AI실제그림합답형"], 12)
        payload = library_payload(pack)
        self.assertEqual(len(payload["양식"]), 1)
        self.assertEqual(len(payload["템플릿"]), 7)
        self.assertTrue(all("pack_version" in item
                            for item in payload["양식"] + payload["템플릿"]))

    def test_template_only_pack_is_supported(self):
        pack = load_pack(pathlib.Path("typesetting_packs/school_exam"))
        payload = library_payload(pack)
        self.assertEqual(payload["양식"], [])
        self.assertEqual(contract(pack)["학교합답0사진5선지"], 11)


if __name__ == "__main__":
    unittest.main()
