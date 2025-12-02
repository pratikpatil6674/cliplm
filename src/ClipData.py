from __future__ import annotations
from enum import Enum
from typing import Optional, List, Callable, Any, Dict
from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
import base64
import io

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
        data: Any,
        subtype: Optional[str] = None,
    ):
        self.mime_type = mime_type
        self.data = data
        # optional subtype for OTHER, or for more precise content-type
        self.subtype = subtype
        # cached preview widget (created on demand, must be created on GUI thread)
        self._preview: Optional[QWidget] = None

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
            return cls(MimeType.IMAGE, qimg)

        # Text (plain)
        if qmime.hasText():
            txt = qmime.text()
            return cls(MimeType.TEXT, str(txt))

        # HTML
        if qmime.hasHtml():
            html = qmime.html()
            return cls(MimeType.HTML, str(html))

        # URLs (file lists)
        if qmime.hasUrls():
            urls = list(qmime.urls())  # list of QUrl
            return cls(MimeType.URLS, urls)

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
            return cls(MimeType.OTHER, bytes(raw), subtype=fmt)

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
    def from_database(cls, db_row: dict, data_col: str = 'preview_text') -> "ClipData":
        mime_type = db_row.get('content_type')
        if mime_type == MimeType.IMAGE:
            data_col = 'thumbnail'
            data = db_row.get(data_col)
            try:
                qimage = ImageUtils.deserialize(data)
                return cls(MimeType.IMAGE, qimage)
            except Exception:
                # If deserialization fails, fall back to raw bytes
                pass
        if mime_type == MimeType.TEXT or mime_type == MimeType.HTML:
            data = db_row.get(data_col)
            if data:
                return cls(mime_type, data)
        return cls(mime_type, None)
    

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
        if self._preview is not None:
            return self._preview

        if widget_factory:
            self._preview = widget_factory(self)
            return self._preview

        # default lightweight previews using QLabel
        if self.mime_type == MimeType.IMAGE:
            lbl = QLabel()
            pix = QPixmap.fromImage(self.data)
            lbl.setPixmap(pix.scaledToHeight(max_height, Qt.SmoothTransformation))
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._preview = lbl
            return lbl

        # TEXT / HTML / URLS / OTHER -> textual preview
        lbl = QLabel()
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
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lbl.setMaximumHeight(max_height)
        self._preview = lbl
        return lbl

    def clear_preview_cache(self) -> None:
        """If you need to recreate the preview widget (e.g. for DPI changes)."""
        if self._preview:
            try:
                # don't delete widget in non-GUI thread
                self._preview.deleteLater()
            except Exception:
                pass
        self._preview = None

    # ---------------------------
    # conversion to QMimeData (fresh object every call)
    # ---------------------------
    @property
    def mime_data(self) -> QMimeData:
        """Create and return a fresh QMimeData representing this ClipData."""
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
            md.setText(self._strip_html(self.data))
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

    @property
    def bytes_data(self) -> bytes:
        if self.mime_type == MimeType.IMAGE:
            # For images, convert QImage to bytes
            return ImageUtils.serialize(self.data, "PNG")
        if self.mime_type == MimeType.TEXT or self.mime_type == MimeType.HTML:
            return self.data.encode("utf-8") if isinstance(self.data, str) else bytes(self.data)
        if self.mime_type == MimeType.URLS:
            return "\n".join([url.toString() for url in self.data]).encode("utf-8")
        """Return the raw bytes data."""
        return self.data if isinstance(self.data, (bytes, bytearray)) else bytes(str(self.data), "utf-8")
    # ---------------------------
    # utilities
    # ---------------------------
    def as_dict(self) -> Dict[str, Any]:
        """
        Minimal serializable representation (suitable for persistence).
        Note: images are base64 encoded here; heavy use may be inefficient.
        """
        if self.mime_type == MimeType.IMAGE:
            # convert QImage -> PNG bytes
            buffer = QPixmap.fromImage(self.data).toImage().bits().asstring(self.data.byteCount()) if False else None
            # fallback approach: use QPixmap save to bytes via QBuffer if needed by your app
            # For clarity we will not implement full-image serialization here.
            raise NotImplementedError("Image serialization: implement via QBuffer or skip images in JSON.")
        if self.mime_type in (MimeType.TEXT, MimeType.HTML):
            return {"mime_type": self.mime_type.value, "data": self.data}
        if self.mime_type == MimeType.URLS:
            return {"mime_type": self.mime_type.value, "data": [u.toString() for u in self.data]}
        return {"mime_type": self.mime_type.value, "data": base64.b64encode(self.data).decode("ascii"), "subtype": self.subtype}

    @staticmethod
    def _strip_html(html: str) -> str:
        # simple fallback: Qt can also provide plain text via QTextDocument, but avoid extra dependency here.
        import re
        return re.sub("<[^<]+?>", "", html)

    def __repr__(self) -> str:
        return f"<ClipData type={self.mime_type} data_repr={type(self.data).__name__}>"
