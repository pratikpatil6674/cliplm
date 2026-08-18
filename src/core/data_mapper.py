from __future__ import annotations
from enum import Enum
from typing import Optional, List, Callable, Any, Dict
from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QImage, QPixmap, QTextDocument
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget, QTextEdit
import base64
import io
import logging
logger=logging.getLogger(__name__)

from core import image_utils as ImageUtils
from core.clip_data import ClipData, MimeType

class DataMapper:
   
   
    @staticmethod
    def from_mime_data(qmime: QMimeData) -> ClipData:
        """Create ClipData from a QMimeData; returns None if empty/unknown."""
        # Image: QMimeData.hasImage() may return True for QImage/QPixmap
        if qmime.hasImage():
            img = qmime.imageData()
            # ensure canonical QImage
            qimg = QImage(img) if isinstance(img, QImage) else QPixmap(img).toImage()
            data_bytes = ImageUtils.serialize(qimg, "PNG")
            obj = ClipData(MimeType.IMAGE, qimg, data=qimg, data_bytes=data_bytes)
            return obj
        if qmime.hasText():
            text = qmime.text()
            obj = ClipData(MimeType.TEXT, str(text))
            obj.data_bytes = text.encode("utf-8") if isinstance(text, str) else bytes(text)
            return obj
        if qmime.hasHtml():
            html = qmime.html()
            obj = ClipData(MimeType.HTML, str(html))
            obj.data_bytes = html.encode("utf-8") if isinstance(html, str) else bytes(html)
            return obj
        if qmime.hasUrls():
            urls = list(qmime.urls())  # list of QUrl
            obj = ClipData(MimeType.URLS, urls)
            obj.data_bytes = str(urls).encode("utf-8")
            return obj

        formats = qmime.formats()
        if formats:
            fmt = formats[0].data().decode("utf-8") if isinstance(formats[0], bytes) else str(formats[0])
            try:
                raw = qmime.data(fmt)
            except Exception:
                raw = b""
            obj = ClipData(MimeType.OTHER, bytes(raw), subtype=fmt)
            obj.data_bytes = raw
            return obj

        return None
    
    @staticmethod
    def to_base64(clip_data: ClipData) -> str:
        if clip_data.mime_type == MimeType.IMAGE:
            return base64.b64encode(clip_data.data_bytes).decode("utf-8")
        return ""

    @staticmethod
    def to_plain_text(clip_data: ClipData) -> ClipData:
        if clip_data.mime_type == MimeType.HTML:
            doc = QTextDocument()
            doc.setHtml(clip_data.data)
            return ClipData(MimeType.TEXT, doc.toPlainText())
        return clip_data