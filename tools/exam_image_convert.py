# -*- coding: utf-8 -*-
r"""이미지 -> 평가원 시험지 삽화 스타일 변환 CLI.

    python tools/exam_image_convert.py input.png [--style contour] [--output output.png]
    python tools/exam_image_convert.py --batch input_dir/ --output-dir out_dir/ [--style exam-clean]
    python tools/exam_image_convert.py --prompt "화학 실험 장치" [--style science] [--output out.png]

스타일:
    contour       가장자리 검출 - 사진,복잡한 그림
    contour-thin  얇은 윤곽선
    contour-bold  굵은 윤곽선
    sketch        필기감 - 손그림에 가까운 느낌
    threshold     단순 이진화 - 이미 깔끔한 도식
    adaptive      적응형 이진화 - 얼룩 있는 스캔본
    exam-clean    평가원 실전 - 깔끔한 윤곽선 (기본)
    exam-diagram  평가원 도표 - 선명한 선,잡점 최소
"""

import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from hwp_palette.hwp import exam_image


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="exam_image_convert",
        description="이미지를 평가원 시험지 삽화 스타일로 변환")
    ap.add_argument("input", nargs="?", help="입력 이미지 경로 (--batch/--prompt 사용 시 생략)")
    ap.add_argument("--output", "-o", help="출력 이미지 경로 (기본: 원본명_exam.png)")
    ap.add_argument("--style", "-s", default="exam-clean",
                    choices=list(exam_image.STYLES),
                    help="변환 스타일 (기본: exam-clean)")
    ap.add_argument("--margin", type=int, default=20,
                    help="하얀 여백 px (기본: 20)")
    ap.add_argument("--dpi", type=int, default=300,
                    help="저장 DPI (기본: 300)")
    ap.add_argument("--batch", help="여러 이미지가 들어 있는 디렉터리")
    ap.add_argument("--output-dir", help="일괄 변환 출력 디렉터리 (--batch 와 함께)")
    ap.add_argument("--list-styles", action="store_true",
                    help="사용 가능한 스타일 목록 출력")
    ap.add_argument("--prompt", "-p",
                    help="AI 생성 후 평가원 스타일 변환 (예: '화학 실험 장치')")
    ap.add_argument("--prompt-style", default="science",
                    choices=["science", "graph", "map", "general"],
                    help="AI 프롬프트 스타일 (기본: science)")
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "local", "hf-api"],
                    help="AI 생성 백엔드 (기본: auto)")
    ap.add_argument("--status", action="store_true",
                    help="AI 생성 가능 여부 확인")
    args = ap.parse_args(argv)

    if args.list_styles:
        _print_styles()
        return 0

    if args.status:
        from hwp_palette.hwp import exam_image_ai
        s = exam_image_ai.is_ready()
        print(f"GPU: {'YES' if s['gpu'] else 'NO'}")
        print(f"HF_API: {'YES' if s['hf_api'] else 'NO (HF_TOKEN 환경변수 없음)'}")
        print(f"Recommended: {s['recommended']}")
        return 0

    if args.prompt:
        from hwp_palette.hwp import exam_image_ai
        try:
            out = exam_image_ai.generate(
                args.prompt, args.output, style=args.prompt_style,
                backend=args.backend)
            print(f"생성 완료: {out}")
        except Exception as e:
            print(f"생성 실패: {e}", file=sys.stderr)
            return 2
        return 0

    if args.batch:
        if not args.output_dir:
            print("--batch 사용 시 --output-dir 이 필요합니다.", file=sys.stderr)
            return 2
        results = exam_image.convert_batch(
            args.batch, args.output_dir, style=args.style)
        ok = sum(1 for _, r, _ in results if r)
        fail = len(results) - ok
        print(f"{ok}개 변환 성공" + (f", {fail}개 실패" if fail else ""))
        for name, success, detail in results:
            if not success:
                print(f"  x {name} -- {detail}", file=sys.stderr)
        return 0 if fail == 0 else 2

    if not args.input:
        ap.print_help()
        return 2

    src = pathlib.Path(args.input)
    if not src.is_file():
        print(f"파일이 없습니다: {src}", file=sys.stderr)
        return 2

    try:
        out = exam_image.convert(src, args.output, style=args.style,
                                  margin=args.margin, dpi=args.dpi)
        print(f"변환 완료: {out}")
    except Exception as e:
        print(f"변환 실패: {e}", file=sys.stderr)
        return 2
    return 0


def _print_styles():
    print("사용 가능한 스타일:")
    print()
    desc = {
        "contour": "가장자리 검출(Canny) - 사진,복잡한 그림",
        "contour-thin": "얇은 윤곽선 - 섬세한 도면",
        "contour-bold": "굵은 윤곽선 - 강조 삽화",
        "sketch": "필기감(Laplacian) - 손그림,필기 느낌",
        "threshold": "단순 이진화(Otsu) - 깔끔한 도식",
        "adaptive": "적응형 이진화 - 얼룩 있는 스캔본",
        "exam-clean": "평가원 실전 - 깔끔한 윤곽선 (기본)",
        "exam-diagram": "평가원 도표 - 선명한 선,잡점 제거",
    }
    for name in exam_image.STYLES:
        print(f"  {name:<16} {desc.get(name, '')}")


if __name__ == "__main__":
    sys.exit(main())


def _print_styles():
    print("사용 가능한 스타일:")
    print()
    desc = {
        "contour": "가장자리 검출(Canny) - 사진,복잡한 그림",
        "contour-thin": "얇은 윤곽선 - 섬세한 도면",
        "contour-bold": "굵은 윤곽선 - 강조 삽화",
        "sketch": "필기감(Laplacian) - 손그림,필기 느낌",
        "threshold": "단순 이진화(Otsu) - 깔끔한 도식",
        "adaptive": "적응형 이진화 - 얼룩 있는 스캔본",
        "exam-clean": "평가원 실전 - 깔끔한 윤곽선 (기본)",
        "exam-diagram": "평가원 도표 - 선명한 선,잡점 제거",
    }
    for name in exam_image.STYLES:
        print(f"  {name:<16} {desc.get(name, '')}")


if __name__ == "__main__":
    sys.exit(main())
