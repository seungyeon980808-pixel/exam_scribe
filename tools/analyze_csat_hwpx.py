# -*- coding: utf-8 -*-
"""Print a compact top-level structure summary for an HWPX section."""

import argparse
import pathlib
import zipfile
import xml.etree.ElementTree as ET


def local(element):
    return element.tag.rsplit("}", 1)[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hwpx")
    args = parser.parse_args()
    with zipfile.ZipFile(pathlib.Path(args.hwpx)) as archive:
        root = ET.fromstring(archive.read("Contents/section0.xml"))
    for index, child in enumerate(list(root)):
        text = "".join(
            (node.text or "") for node in child.iter() if local(node) == "t"
        ).replace("\n", " ")
        kinds = {local(node) for node in child.iter()}
        controls = [
            name for name in sorted(kinds)
            if name in {"header", "footer", "pageNum", "pageHiding",
                        "pageBreak", "columnBreak"}
        ]
        tables = sum(local(node) == "tbl" for node in child.iter())
        pictures = sum(local(node) == "pic" for node in child.iter())
        print(
            f"{index:03d} id={child.get('id')} text={text[:110]!r} "
            f"tbl={tables} pic={pictures} sec={'secPr' in kinds} "
            f"col={'colPr' in kinds} ctrl={controls}"
        )


if __name__ == "__main__":
    main()
