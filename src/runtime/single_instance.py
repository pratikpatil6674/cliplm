from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QWidget


class QtSingleInstanceApp:
    def __init__(self, server_name: str, message: str = "Keep it real!"):
        self.server_name = server_name
        self.server: Optional[QLocalServer] = None
        self.message: str = message

    def already_running(self, timeout_ms: int = 200) -> bool:
        """
        Returns True if another instance is already running.
        If found, sends a small message to the running instance.
        """
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)

        if socket.waitForConnected(timeout_ms):
            socket.write(self.message.encode("utf-8"))
            socket.flush()
            socket.waitForBytesWritten(timeout_ms)
            socket.disconnectFromServer()
            return True

        return False

    def start(
        self,
        on_message: Callable[[], None],
        remove_stale_server: bool = True,
    ) -> None:
        """
        Starts the local server for the first instance.
        """
        if remove_stale_server:
            QLocalServer.removeServer(self.server_name)

        self.server = QLocalServer()

        if not self.server.listen(self.server_name):
            raise RuntimeError(f"Could not start local server: {self.server_name}")

        def handle_connection():
            client = self.server.nextPendingConnection()
            if not client:
                return

            if client.waitForReadyRead(1000):
                msg = bytes(client.readAll()).decode("utf-8")
                print(f"Received message: {msg}")
                on_message()

            client.disconnectFromServer()

        self.server.newConnection.connect(handle_connection)