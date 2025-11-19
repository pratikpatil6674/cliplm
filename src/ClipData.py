import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QImage, QPixmap
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QListWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QListWidgetItem,
    QDialog,
    QCheckBox,
    QFrame,
)
from PySide6.QtWidgets import QSizePolicy
import os
import datetime

def check_clipboard():
    # 1. Start the QApplication (required for clipboard access)
    # The QApplication instance is necessary to interact with the window system.
    # We check if an instance already exists to avoid errors.
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 2. Get the QClipboard object
    clipboard = QGuiApplication.clipboard()
    
    # 3. Get the QMimeData object
    mime_data = clipboard.mimeData()
    
    print("--- Clipboard Content Analysis ---")
    # 4. Check for common data types (for demonstrating the type)
    if mime_data.hasImage():
        print("Type: Image (QMimeData.hasImage() is True)")
        
        # 5. Get the QImage object
        image = mime_data.imageData() #clipboard.image()
        
        # Check if the image is valid (not null)
        if not image.isNull():
            # Generate a unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clipboard_image_{timestamp}.png"
            
            # Save the image
            if image.save(filename, "PNG"):
                print(f"✅ Success: Image saved as '{filename}'")
            else:
                print(f"❌ Error: Could not save image to disk.")
        else:
            print("❌ Error: Image data found, but QImage is null.")
            
    elif mime_data.hasText():
        print(f"Type: Text")
        print(mime_data.hasUrls())
        text_data = mime_data.text() #clipboard.text()
        # Display the first 50 characters of the text
        display_text = text_data #[:50].replace('\n', ' ')
        print(f"Content (Preview): '{display_text}...'")
        
    elif mime_data.hasUrls():
        print("Type: URLs/Files")
        urls = [url.toLocalFile() or url.toString() for url in mime_data.urls()]
        print(f"Content: {urls}")
        
    elif mime_data.hasHtml():
        print("Type: HTML")
        html_data = mime_data.html()
        display_html = html_data[:50].replace('\n', ' ')
        print(f"Content (Preview): '{display_html}...'")
        
    else:
        # 6. Fallback: Check all available MIME formats
        formats = mime_data.formats()
        print("Type: Unknown/Other")
        if formats:
            print(f"Available MIME Formats: {formats}")
        else:
            print("Clipboard is empty or contains unsupported data.")

    print(mime_data.formats())
    print("-" * 34)

class ClipData:
    def __init__(self, mime_data: QMimeData):
        self.mime_type = None
        self._widget = None
        self.data = None
        self.set_data(mime_data)

    def set_data(self, mime_data: QMimeData):
        if mime_data.hasImage():
            image = mime_data.imageData()
            self.mime_type = "image"
            self._widget = QLabel()
            self._widget.setPixmap(QPixmap.fromImage(image))
            self.data = image
            return image
        elif mime_data.hasText():
            self.mime_type = "text"
            self._widget = QLabel(mime_data.text())
            self._widget.setWordWrap(True)
            self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._widget.setMaximumHeight(180 - 30)  # allow padding
            self.data = mime_data.text() # str
            return mime_data.text() # str
        elif mime_data.hasUrls():
            self.mime_type = "urls"
            self._widget = QLabel(mime_data.urls())
            self.data = mime_data.urls() # list of QUrl
            return mime_data.urls() # list of QUrl
        elif mime_data.hasHtml():
            self.mime_type = "html"
            self._widget = QLabel(mime_data.html())
            self._widget.setWordWrap(True)
            self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._widget.setMaximumHeight(180 - 30)  # allow padding
            self.data = mime_data.html() # str
            return mime_data.html() # str
        else:
            print("Unknown/Other MIME type")
            return None

    @property
    def widget(self):
        return self._widget
    
    @property
    def mime_data(self):
        # new mime data object must be created everytime, beacause ownership is transferred to the clipboard
        if self.mime_type == "image":
            mime_data = QMimeData()
            mime_data.setImageData(self.data)
            return mime_data
        elif self.mime_type == "text":
            mime_data = QMimeData()
            mime_data.setText(self.data)
            return mime_data
        elif self.mime_type == "urls":
            mime_data = QMimeData()
            mime_data.setUrls(self.data)
            return mime_data
        elif self.mime_type == "html":
            mime_data = QMimeData()
            mime_data.setHtml(self.data)
            return mime_data
        else:
            return None

    @staticmethod
    def from_data(data: bytes, mime_type: str):
        mime_data = QMimeData()
        mime_data.setData(mime_type, data)
        return ClipData(mime_data)
# Execute the function
# if __name__ == "__main__":
#     check_clipboard()