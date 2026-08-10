# -*- coding: utf-8 -*-
from pathlib import Path

from PIL import Image
import pytest

from hwp_palette.hwp.engine_library import _image_size_mm


def test_jpeg_print_size_is_available_for_column_clamping(tmp_path: Path):
    path = tmp_path / "diagram.jpg"
    Image.new("RGB", (600, 300), "white").save(path, dpi=(300, 300))
    width, height = _image_size_mm(path)
    assert width == pytest.approx(50.8, abs=0.2)
    assert height == pytest.approx(25.4, abs=0.2)
