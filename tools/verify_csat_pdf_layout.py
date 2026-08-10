# -*- coding: utf-8 -*-
"""그림을 제외한 기준/결과 PDF 렌더의 픽셀 위치가 같은지 검사한다."""

import argparse
import json
import pathlib

import numpy as np
from PIL import Image


def dilate(mask, rounds=6):
    for _ in range(rounds):
        padded = np.pad(mask, 1)
        mask = (
            padded[:-2, 1:-1] | padded[2:, 1:-1]
            | padded[1:-1, :-2] | padded[1:-1, 2:]
            | padded[1:-1, 1:-1]
        )
    return mask


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_prefix")
    parser.add_argument("result_prefix")
    parser.add_argument("--pages", type=int, default=4)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    reports = []
    for page in range(1, args.pages + 1):
        before_path = pathlib.Path(f"{args.reference_prefix}-{page}.png")
        after_path = pathlib.Path(f"{args.result_prefix}-{page}.png")
        before = np.asarray(Image.open(before_path).convert("L"), dtype=np.int16)
        after = np.asarray(Image.open(after_path).convert("L"), dtype=np.int16)
        if before.shape != after.shape:
            raise ValueError(f"{page}쪽 크기가 다릅니다: {before.shape} != {after.shape}")
        # 기준에는 잉크가 있고 결과는 흰색인 픽셀 = 비워 낸 그림 영역.
        picture = (before < 245) & (after > 250)
        excluded = dilate(picture)
        outside = ~excluded
        delta = np.abs(before - after)
        report = {
            "page": page,
            "size_px": [int(before.shape[1]), int(before.shape[0])],
            "blanked_picture_pixels_pct": round(float(picture.mean() * 100), 4),
            "outside_picture_diff_pixels_pct": round(float(((delta > 12) & outside).mean() * 100), 6),
            "outside_picture_mean_abs_error": round(float(delta[outside].mean()), 6),
        }
        reports.append(report)
    result = {
        "pages": reports,
        "pass": all(row["outside_picture_diff_pixels_pct"] == 0 for row in reports),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        pathlib.Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
