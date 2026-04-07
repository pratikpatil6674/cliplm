from __future__ import annotations
from enum import Enum
from typing import Optional, List, Callable, Any, Dict
from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget, QTextEdit
import base64
import io
import logging
logger=logging.getLogger(__name__)

import ImageUtils

class MimeType(str, Enum):
    TEXT = "text"
    HTML = "html"
    IMAGE = "image"
    URLS = "urls"
    OTHER = "other"


class ClipData:
    """
    Data-only representation of a clipboard entry.

    - Keeps canonical raw data types:
        TEXT/HTML -> str
        IMAGE -> QImage
        URLS -> List[QUrl]
        OTHER -> bytes (raw mime payload)

    - Does NOT create UI widgets by default. Call `create_preview_widget()` to get
      a lightweight preview (QLabel) when running on the GUI thread.

    - Use `mime_data` property to obtain a fresh QMimeData ready to set on QApplication.clipboard().
    """

    def __init__(
        self,
        mime_type: MimeType,
        data: Any = None,
        preview_data: Any = None,
        database_id: Optional[int] = None,
        subtype: Optional[str] = None,
    ):
        self.mime_type = mime_type
        self.data = data    # str, QImage, List[QUrl], or bytes
        self.data_bytes = None # str, full QImage bytes
        self.database_id = database_id

        self.preview = preview_data # str, QImage
        self.preview_text = None # str, preview text
        self.preview_bytes = None # thumbnail bytes

        # optional subtype for OTHER, or for more precise content-type
        self.subtype = subtype
        # cached preview widget (created on demand, must be created on GUI thread)
        self._preview_widget: Optional[QWidget] = None

    # ---------------------------
    # factories
    # ---------------------------
    @classmethod
    def from_qmime(cls, qmime: QMimeData) -> Optional["ClipData"]:
        """Create ClipData from a QMimeData; returns None if empty/unknown."""
        # Image: QMimeData.hasImage() may return True for QImage/QPixmap
        if qmime.hasImage():
            img = qmime.imageData()
            # ensure canonical QImage
            qimg = QImage(img) if isinstance(img, QImage) else QPixmap(img).toImage()
            obj = cls(MimeType.IMAGE, qimg)

            obj.data_bytes = ImageUtils.serialize(qimg, "PNG")

            obj.preview = ImageUtils.create_thumbnail(qimg, max_size=256)
            obj.preview_bytes = ImageUtils.serialize(obj.preview, "PNG")

            obj.image_b64 = base64.b64encode(obj.data_bytes).decode("utf-8") # this will be sent to LLM service
            return obj
        # Text (plain)
        if qmime.hasText():
            text = qmime.text()
            obj = cls(MimeType.TEXT, str(text))
            obj.data_bytes = text.encode("utf-8") if isinstance(text, str) else bytes(text)
            obj.preview_text = text[:1000]  # limit preview size
            return obj

        # HTML
        if qmime.hasHtml():
            html = qmime.html()
            obj = cls(MimeType.HTML, str(html))
            obj.data_bytes = html.encode("utf-8") if isinstance(html, str) else bytes(html)
            obj.preview_text = html[:1000]  # limit preview size
            return obj

        # URLs (file lists)
        if qmime.hasUrls():
            urls = list(qmime.urls())  # list of QUrl
            obj = cls(MimeType.URLS, urls)
            obj.data_bytes = str(urls).encode("utf-8")
            obj.preview_text = str(urls)[:1000]  # limit preview size
            return obj

        # Fallback: preserve raw bytes for a specific subtype if available
        # Attempt to pick the first available format
        formats = qmime.formats()
        if formats:
            # pick first format and store raw bytes
            fmt = formats[0].data().decode("utf-8") if isinstance(formats[0], bytes) else str(formats[0])
            try:
                raw = qmime.data(fmt)
            except Exception:
                # last-resort: empty
                raw = b""
            obj = cls(MimeType.OTHER, bytes(raw), subtype=fmt)
            obj.data_bytes = raw
            return obj

        return None

    @classmethod
    def from_text(cls, text: str) -> "ClipData":
        return cls(MimeType.TEXT, text)

    @classmethod
    def from_html(cls, html: str) -> "ClipData":
        return cls(MimeType.HTML, html)

    @classmethod
    def from_image(cls, qimage: QImage) -> "ClipData":
        return cls(MimeType.IMAGE, qimage)

    @classmethod
    def from_urls(cls, urls: List[QUrl]) -> "ClipData":
        return cls(MimeType.URLS, list(urls))

    @classmethod
    def from_database(cls, db_row: dict, data_key: str = "content") -> "ClipData":
        mime_type = db_row.get('content_type')
        if mime_type == MimeType.IMAGE:
            data = db_row.get(data_key)
            try:
                qimage = ImageUtils.deserialize(data)
                if qimage.isNull():
                    logger.debug("DEBUG: QImage is null after deserialization")
                
                return cls(MimeType.IMAGE, qimage, database_id=db_row.get('clip_id'))
            except Exception as e:
                logger.debug(f"DEBUG: Exception during image deserialization: {e}")

        elif mime_type == MimeType.TEXT or mime_type == MimeType.HTML:
            data = db_row.get(data_key)
            obj = cls(mime_type, data=data, database_id=db_row.get('clip_id'))
            return obj
        return cls(mime_type, database_id=db_row.get('clip_id'))
    

    def is_text_like(self) -> bool:
        return self.mime_type in (MimeType.TEXT, MimeType.HTML)
    
    def is_image_like(self) -> bool:
        return self.mime_type == MimeType.IMAGE
    
    # ---------------------------
    # preview widget creation (GUI-thread)
    # ---------------------------
    def create_preview_widget(self, max_height: int = 150, widget_factory: Optional[Callable[["ClipData"], QWidget]] = None) -> QWidget:
        """
        Returns a QWidget preview for display in lists.
        - `widget_factory` optional: a callable that receives ClipData and returns QWidget.
        - The created widget is cached; if you want a fresh widget, call `clear_preview_cache()` first.
        Note: Must be called on the GUI thread.
        """
        if self._preview_widget is not None:
            return self._preview_widget

        if widget_factory:
            self._preview_widget = widget_factory(self)
            return self._preview_widget

        # default lightweight previews using QLabel
        if self.mime_type == MimeType.IMAGE:
            lbl = QLabel()
            if self.data is not None:
                pix = QPixmap.fromImage(self.data)
                # lbl.setPixmap(pix.scaledToHeight(max_height, Qt.SmoothTransformation))
                lbl.setPixmap(pix)
            else:
                lbl.setText("Image data not available")
                logger.debug("Image data not available for preview")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._preview_widget = lbl
            return lbl

        # TEXT / HTML / URLS / OTHER -> textual preview
        lbl = QLabel("temp")
        if self.mime_type == MimeType.HTML:
            lbl.setText(self.data)
            lbl.setTextFormat(Qt.RichText)
        elif self.mime_type == MimeType.TEXT:
            lbl.setText(self.data)
            lbl.setTextFormat(Qt.PlainText)
        elif self.mime_type == MimeType.URLS:
            # join URLs into a readable string
            lbl.setText("\n".join([u.toString() for u in self.data]))
            lbl.setTextFormat(Qt.PlainText)
        else:
            # OTHER: show basic summary (hex/snippet)
            snippet = (self.data[:200] if isinstance(self.data, (bytes, bytearray)) else str(self.data)) 
            if isinstance(snippet, (bytes, bytearray)):
                snippet = base64.b64encode(snippet[:120]).decode("ascii")
            lbl.setText(snippet)
            lbl.setTextFormat(Qt.PlainText)

        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.PlainText)
        lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self._preview_widget = lbl
        return lbl

    def clear_preview_cache(self) -> None:
        """If you need to recreate the preview widget (e.g. for DPI changes)."""
        if self._preview_widget:
            try:
                # don't delete widget in non-GUI thread
                self._preview_widget.deleteLater()
            except Exception:
                pass
        self._preview_widget = None

    # ---------------------------
    # conversion to QMimeData (fresh object every call)
    # ---------------------------
    @property
    def mime_data(self) -> QMimeData:
        """
        Creates a new QMimeData object with the full data (image or text) included.
        The data is fully preserved in the returned object.
        The returned object can be used with QClipboard.setMimeData() to paste the item.
        
        Returns:
            QMimeData: A fresh QMimeData object containing the full clipboard data.
        """
        md = QMimeData()
        if self.mime_type == MimeType.IMAGE:
            # QMimeData.setImageData accepts QImage or QPixmap
            md.setImageData(self.data)
            return md
        if self.mime_type == MimeType.TEXT:
            md.setText(self.data)
            return md
        if self.mime_type == MimeType.HTML:
            md.setHtml(self.data)
            return md
        if self.mime_type == MimeType.URLS:
            md.setUrls(self.data)
            return md
        # OTHER
        if self.subtype:
            md.setData(self.subtype, self.data)
        else:
            # generic blob
            md.setData("application/octet-stream", self.data if isinstance(self.data, (bytes, bytearray)) else bytes(str(self.data), "utf-8"))
        return md

    def delete_full_data(self) -> None:
        """Delete the full data to free up memory."""
        self.data = None
        self.data_bytes = None