import logging

import struct
import zlib
from PySide6.QtCore import Qt, QBuffer, QIODevice, QByteArray
from PySide6.QtGui import QImage, QPixmap

logger = logging.getLogger(__name__)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

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

def is_complete_png(data: bytes) -> bool:
    """Check PNG completeness before passing clipboard bytes to libpng."""
    if not data or not data.startswith(PNG_SIGNATURE):
        return False

    position = len(PNG_SIGNATURE)
    while position < len(data):
        if position + 12 > len(data):
            return False

        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        payload_start = position + 8
        payload_end = payload_start + length
        chunk_end = payload_end + 4
        if chunk_end > len(data):
            return False

        expected_crc = struct.unpack(">I", data[payload_end:chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(data[payload_start:payload_end], actual_crc)
        if expected_crc != actual_crc & 0xFFFFFFFF:
            return False

        position = chunk_end
        if chunk_type == b"IEND":
            return position == len(data)

    return False

def deserialize(data: bytes) -> QImage:
    """Create a QImage from valid encoded bytes, or return a null image."""
    if not data:
        return QImage()
    if data.startswith(PNG_SIGNATURE) and not is_complete_png(data):
        logger.warning("Ignored incomplete or corrupt PNG image data")
        return QImage()

    qba = QByteArray(data)
    img = QImage()
    if not img.loadFromData(qba):
        logger.warning("Could not decode clipboard image data")
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