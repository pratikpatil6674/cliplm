import sys
from pathlib import Path

from PySide6.QtGui import QColor, QImage


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.image_utils import deserialize, is_complete_png, serialize


def _valid_png() -> bytes:
    image = QImage(2, 2, QImage.Format_ARGB32)
    image.fill(QColor("blue"))
    return serialize(image)


def test_complete_png_is_accepted():
    assert is_complete_png(_valid_png())


def test_truncated_png_is_rejected_before_qt_decoding():
    truncated = _valid_png()[:-4]
    assert not is_complete_png(truncated)
    assert deserialize(truncated).isNull()
