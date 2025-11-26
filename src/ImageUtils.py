from PySide6.QtCore import QBuffer, QIODevice, QByteArray
from PySide6.QtGui import QImage, QPixmap

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