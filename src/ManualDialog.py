from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPlainTextEdit, QDialogButtonBox, QSizePolicy
from PySide6.QtGui import QIcon
class ManualEntryDialog(QDialog):
    def __init__(self, parent=None, init_title: str = "", init_text: str = ""):
        super().__init__(parent)
        self.init_title = init_title
        self.setObjectName("manual_entry_dialog")
        self.init_text = init_text
        self._setup_ui()
        # self.setWindowTitle("New Manual Entry")

        # self.layout = QVBoxLayout(self)

        # self.title_input = QLineEdit(self)
        # self.title_input.setPlaceholderText("Enter title")
        # self.title_input.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 5px;") 
        
        # self.title_input.setText(init_title)
        # self.layout.addWidget(self.title_input)

        # self.text_input = QPlainTextEdit(self)
        # self.text_input.setPlaceholderText("Enter main text")
        # self.text_input.setStyleSheet("background-color: #ffffff; color: #000000;  padding: 10px; margin: 10px;") 
        # self.text_input.setStyleSheet("""
        #     QPlainTextEdit {
        #         border: 1px solid #ccc; /* default border */
        #         background-color: #ffffff; color: #000000;font-size: 15px; font-family: Ubuntu, sans-serif;
        #         margin-bottom: 12px;
        #     }

        #     QPlainTextEdit:hover {
        #         border: 2px solid #2979ff; /* Add border on focus */
        #     }
        # """)
        # self.text_input.setPlainText(init_text)
        # self.layout.addWidget(self.text_input)

        # # Custom button row
        # button_layout = QHBoxLayout()
        # button_layout.setSpacing(0)
        # button_layout.setContentsMargins(0, 0, 0, 0)

        # self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        # # Access individual buttons
        # ok_button = self.button_box.button(QDialogButtonBox.Ok)
        # cancel_button = self.button_box.button(QDialogButtonBox.Cancel)

        # # Customize OK button
        # ok_button.setText("Save")
        # ok_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: #1A73E8;
        #         color: white;
        #         border-radius: 4px;
        #         padding: 6px 12px;
        #         min-width: 80px;
        #         text-transform: none; 
        #         font-size: 15px; font-family: Ubuntu, sans-serif;
        #     }
        #     QPushButton:hover {
        #         background-color: #2B7DE9;
        #     }
        # """)
        # ok_button.setIcon(QIcon())
        # # ok_button.setFixedSize(100, 35)
        # ok_button.setFixedHeight(35)  # Fix the height
        # ok_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # # Customize Cancel button
        # cancel_button.setText("Cancel")
        # cancel_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: #ffffff;
        #         color: #2979ff;
        #         border-radius: 4px;
        #         padding: 6px 12px;
        #         min-width: 80px;
        #         border: 1px solid #ccc;
        #         text-transform: none; 
        #         font-size: 15px; font-family: Ubuntu, sans-serif;
        #     }
        #     QPushButton:hover {
        #         background-color: #F8FBFF;
        #     }
        # """)
        # cancel_button.setIcon(QIcon())
        # # cancel_button.setFixedSize(100, 35)
        # cancel_button.setFixedHeight(35)  # Fix the height
        # cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # # Add stretch before, between, and after buttons
        # button_layout.addStretch()
        # button_layout.addWidget(cancel_button)
        # button_layout.addStretch()
        # button_layout.addWidget(ok_button)
        # button_layout.addStretch()

        # self.layout.addStretch()
        # self.layout.addLayout(button_layout)
        # self.button_box.accepted.connect(self.accept)
        # self.button_box.rejected.connect(self.reject)
        # # self.layout.addWidget(self.button_box)

    def _setup_ui(self):
        self.setWindowTitle("New note")
        self.resize(500, 300)

        self.layout = QVBoxLayout(self)

        self.title_input = QLineEdit(self)
        self.title_input.setObjectName("note_title_input")
        self.title_input.setPlaceholderText("Enter note title")
        self.layout.setContentsMargins(16, 16, 16, 14)
        self.layout.setSpacing(10)
        
        self.title_input.setText(self.init_title)
        self.layout.addWidget(self.title_input)

        self.text_input = QPlainTextEdit(self)
        self.text_input.setObjectName("note_content_input")
        self.text_input.setPlaceholderText("Enter note content")
        self.text_input.setPlainText(self.init_text)
        self.layout.addWidget(self.text_input)

        # Custom button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        # Access individual buttons
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.cancel_button = self.button_box.button(QDialogButtonBox.Cancel)

        # Customize OK button
        self.ok_button.setText("Save")
        self.ok_button.setObjectName("primary_button")
        self.ok_button.setIcon(QIcon())
        # ok_button.setFixedSize(100, 35)
        self.ok_button.setFixedHeight(35)  # Fix the height
        self.ok_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Customize Cancel button
        self.cancel_button.setText("Cancel")
        self.ok_button.setProperty("role", "primary")
        self.cancel_button.setIcon(QIcon())
        # cancel_button.setFixedSize(100, 35)
        self.cancel_button.setFixedHeight(35)  # Fix the height
        self.cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Add stretch before, between, and after buttons
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        self.cancel_button.setProperty("role", "secondary")
        for button in (self.ok_button, self.cancel_button):
            button.style().unpolish(button)
            button.style().polish(button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()

        self.layout.addStretch()
        self.layout.addLayout(button_layout)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # self.layout.addWidget(self.button_box)
        
    def _setup_styles(self):
        self.title_input.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 12pt; padding: 0px; margin: 5px;") 
        self.text_input.setStyleSheet("background-color: #ffffff; color: #000000;  padding: 10px; margin: 10px;") 
        self.text_input.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #ccc; /* default border */
                background-color: #ffffff; color: #000000;font-size: 12pt;
                margin-bottom: 12pt;
            }

            QPlainTextEdit:hover {
                border: 2px solid #2979ff; /* Add border on focus */
            }
        """)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                padding: 6px 12px;
                border-radius: 8px;
                min-width: 80px;
                text-transform: none; 
                font-size: 12pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
        """)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #2c62d6;
                border: 1px solid rgba(44,98,214,0.18);
                padding: 6px 12px;
                border-radius: 8px;
                min-width: 80px;
                text-transform: none; 
                font-size: 12pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f0f5ff;
            }
        """)
        
    def get_inputs(self):
        return self.title_input.text(), self.text_input.toPlainText()
