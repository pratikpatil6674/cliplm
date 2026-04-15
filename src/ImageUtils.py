from PySide6.QtCore import Qt, QBuffer, QIODevice, QByteArray
from PySide6.QtGui import QImage, QPixmap
import logging
logger = logging.getLogger(__name__)

def serialize(image: QImage | QPixmap, fmt: str = "PNG") -> bytes:
    if isinstance(image, QPixmap):
        qimg = image.toImage()
    else:
        qimg = image

    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    # Save into specified format
    qimg.save(buffer, fmt)
    b = bytes(buffer.data())
    buffer.close()
    return b

def deserialize(data: bytes) -> QImage:
    """
    Create a QImage from bytes.
    """
    qba = QByteArray(data)
    img = QImage()
    img.loadFromData(qba)
    return img

def create_thumbnail(img: QImage, max_size: int = 128) -> QImage:
    """
    Returns a thumbnail QImage with the longest side == max_size.
    Aspect ratio is preserved.
    """
    if img.isNull():
        logger.warning("Null image received when creating thumbnail")
        return QImage()

    return img.scaled(
        max_size,
        max_size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )