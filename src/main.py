import multiprocessing
import os
import sys

from LinuxSetupVerifier import verify_linux_system_setup


def main():
    multiprocessing.freeze_support()

    if sys.platform == "linux":
        if not verify_linux_system_setup():
            sys.exit(1)
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    from QtSingleInstanceApp import QtSingleInstanceApp
    from PySide6.QtCore import QCoreApplication, Qt
    from AppVersion import APP_VERSION
    from resources import APP_ICON

    single = QtSingleInstanceApp("cliplm-app")
    if single.already_running():
        print("Another instance is already running. Exiting.")
        sys.exit(0)

    from PySide6.QtWidgets import QApplication
    import asyncio
    from qasync import QEventLoop
    from PySide6.QtGui import QFont, QGuiApplication

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication.instance() or QApplication([])
    app.setWindowIcon(APP_ICON)
    QCoreApplication.setApplicationVersion(APP_VERSION)

    from ThemeManager import apply_app_theme

    apply_app_theme(app)

    from App import App

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = App()
    window.setWindowIcon(APP_ICON)
    single.start(window.move_near_cursor)
    # QApplication.setQuitOnLastWindowClosed(False)

    window.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
