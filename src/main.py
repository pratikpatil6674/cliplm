
from App import App
from PySide6.QtWidgets import QApplication
import asyncio
from qasync import QEventLoop, asyncSlot

if __name__ == "__main__":
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = App(); window.show()
    with loop:
        loop.run_forever()

