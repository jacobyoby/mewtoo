"""Tests for OCR region association."""

from unittest.mock import Mock

import numpy as np

from ocr_enhancer import OCREnhancer, TextRegion


def test_dialog_text_stays_paired_after_short_reads_are_dropped():
    """A dropped short read must not shift later strings onto earlier regions."""
    enhancer = OCREnhancer()
    image = np.zeros((144, 160, 3), dtype=np.uint8)
    regions = [
        {"type": TextRegion.MENU, "confidence": 0.2, "bbox": (0, 0, 10, 10)},
        {"type": TextRegion.MENU, "confidence": 0.4, "bbox": (0, 20, 10, 10)},
        {"type": TextRegion.DIALOG_BOX, "confidence": 0.9, "bbox": (0, 104, 40, 20)},
    ]
    enhancer.detect_text_regions = Mock(return_value=regions)
    enhancer.extract_text_from_region = Mock(
        side_effect=["HI", "OPEN MENU", "OAK SPEAKS"]
    )

    text = enhancer.extract_text_enhanced(image, prioritize_dialog=False)

    assert text == "OAK SPEAKS"
