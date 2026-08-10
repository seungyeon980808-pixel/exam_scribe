# -*- coding: utf-8 -*-
"""참고 HWPX를 분석해 대왕중 시험지 물감과 팔레트를 설치한다."""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hwp_palette.model import reference_exam_palette as refpal  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reference", help="기준 HWPX 파일")
    ap.add_argument("--page-form",
                    help="쪽 테두리·머리표·꼬리말이 든 원안지 HWP/HWPX")
    ap.add_argument("--work-dir", default="data/reference_palette",
                    help="중간·검증 산출물 폴더")
    ap.add_argument("--no-install", action="store_true",
                    help="HWP 물감까지만 만들고 라이브러리에는 설치하지 않음")
    args = ap.parse_args(argv)

    work = pathlib.Path(args.work_dir).resolve()
    page_form_hwpx = None
    if args.page_form:
        page_form = pathlib.Path(args.page_form).resolve()
        if page_form.suffix.lower() == ".hwpx":
            page_form_hwpx = page_form
        else:
            page_form_hwpx = work / "원안지_양식_원본.hwpx"
            from pyhwpx import Hwp
            hwp = Hwp(new=True, visible=False, register_module=True, on_quit=False)
            try:
                if not hwp.open(str(page_form)):
                    raise RuntimeError(f"원안지 양식을 열지 못했습니다: {page_form}")
                if not hwp.save_as(str(page_form_hwpx.resolve()), format="HWPX"):
                    raise RuntimeError(f"원안지 양식을 HWPX로 변환하지 못했습니다: {page_form}")
            finally:
                hwp.quit()
    variants = refpal.build_hwpx_variants(
        args.reference, work, page_form_hwpx=page_form_hwpx)
    template_hwp = refpal.convert_hwpx_to_hwp(
        variants["template"], work / "대왕중_합답형_그림빈칸.hwp")
    form_hwp = refpal.convert_hwpx_to_hwp(
        variants["form"], work / "대왕중_원안지_전체_틀.hwp")
    score_hwp = None
    if "score" in variants:
        score_hwp = refpal.convert_hwpx_to_hwp(
            variants["score"], work / "대왕중_배점_현황.hwp")
    print(f"문항 물감: {template_hwp}")
    print(f"양식 물감: {form_hwp}")
    if score_hwp:
        print(f"배점 물감: {score_hwp}")
    if not args.no_install:
        result = refpal.install(template_hwp, form_hwp, score_hwp=score_hwp)
        print(f"팔레트 설치: {result['tab']['name']} / 블럭 {len(result['tab']['blocks'])}개")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
