# -*- coding: utf-8 -*-
"""2009년 9월 물리 II 참고본으로 `수능양식 ai` 팔레트를 만든다."""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hwp_palette.model import csat_ai_palette  # noqa: E402
from hwp_palette.model.csat_reference_fragments import (  # noqa: E402
    REFERENCE_FRAGMENT_SPECS,
    build_all_reference_fragments,
    build_reference_fragment,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_hwpx", help="한글에서 저장한 기준 HWPX")
    parser.add_argument("--work-dir", default="data/csat_ai_palette")
    parser.add_argument("--no-install", action="store_true")
    args = parser.parse_args(argv)

    work = pathlib.Path(args.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    blank_hwpx = csat_ai_palette.build_blank_reference(
        args.reference_hwpx, work / "수능_AI_물리II_4쪽_그림빈칸.hwpx")
    blank_hwp = csat_ai_palette.convert_hwpx_to_hwp(
        blank_hwpx, work / "수능_AI_물리II_4쪽_그림빈칸.hwp")
    fragment_dir = work / "reference_fragments"
    fragment_hwpxs = build_all_reference_fragments(blank_hwpx, fragment_dir)
    # 시각 검증용 그림형은 흰 이미지가 아니라 실제 원본 그래프를 보존한다.
    for spec in REFERENCE_FRAGMENT_SPECS:
        if spec.get("use_original_images"):
            fragment_hwpxs[spec["key"]] = build_reference_fragment(
                args.reference_hwpx,
                fragment_dir / f"수능_AI_실제_{spec['key']}.hwpx",
                spec,
            )
    fragment_hwps = {}
    for spec in REFERENCE_FRAGMENT_SPECS:
        source = fragment_hwpxs[spec["key"]]
        fragment_hwps[spec["key"]] = csat_ai_palette.convert_hwpx_to_hwp(
            source, source.with_suffix(".hwp"))
    from hwp_palette.model import library
    source_form = next(item for item in library.load()["양식"]
                       if item.get("name") == "수능양식")
    flow_safe_form = csat_ai_palette.build_flow_safe_form(
        library.template_path(source_form), work / "수능_AI_첫면_흐름보정.hwp")
    metrics = work / "수능_AI_참고본_측정값.json"
    metrics.write_text(
        json.dumps(csat_ai_palette.REFERENCE_METRICS, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"그림 빈칸 비교본: {blank_hwp}")
    print(f"측정값: {metrics}")
    if not args.no_install:
        result = csat_ai_palette.install(
            blank_hwp, first_page_form_hwp=flow_safe_form,
            template_hwps=fragment_hwps)
        print(f"팔레트 설치: {result['tab']['name']} / {len(result['tab']['blocks'])}개 물감")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
