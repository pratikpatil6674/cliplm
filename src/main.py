import sys
from QtSingleInstanceApp import QtSingleInstanceApp
from PySide6.QtCore import Qt
from resources import APP_ICON
def main():
    single = QtSingleInstanceApp("neuroclip-app")
    if single.already_running():
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    from App import App
    from PySide6.QtWidgets import QApplication
    import asyncio
    from qasync import QEventLoop
    from PySide6.QtGui import QFont, QGuiApplication
    import os
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication([])
    app.setWindowIcon(APP_ICON)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = App()
    window.setWindowIcon(APP_ICON)
    # app.setFont(QFont("Courier New", 12))
    single.start(window.move_near_cursor)
    QApplication.setQuitOnLastWindowClosed(False)

    window.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
