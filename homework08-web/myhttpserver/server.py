import datetime
import socket
import threading
import traceback
import typing as tp

from .handlers import BaseHTTPRequestHandler, BaseRequestHandler


class CountDownLatch(object):
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()

    def count_down(self):
        self.lock.acquire()
        self.count -= 1
        if self.count <= 0:
            self.lock.notifyAll()
        self.lock.release()

    def wait(self):
        self.lock.acquire()
        while self.count > 0:
            self.lock.wait()
        self.lock.release()


class TCPServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        backlog_size: int = 1,
        max_workers: int = 1,
        timeout: tp.Optional[float] = None,
        request_handler_cls: tp.Type[BaseRequestHandler] = BaseRequestHandler,
    ) -> None:
        self.host = host
        self.port = port
        self.server_address = (host, port)
        self.backlog_size = backlog_size
        self.request_handler_cls = request_handler_cls
        self.max_workers = max_workers
        self.timeout = timeout
        self._threads: tp.List[threading.Thread] = []
        self._ended = False

    def serve_forever(self) -> None:
        server_socket = socket.socket()
        server_socket.bind(self.server_address)
        server_socket.listen(self.backlog_size)
        server_socket.settimeout(1)

        latch = CountDownLatch(self.max_workers)

        try:
            for i in range(self.max_workers):
                self._threads.append(
                    threading.Thread(target=self.handle_accept, args=(server_socket, latch,))
                )
                self._threads[-1].start()

            print("=" * 100)
            print("SERVER STARTED")
            print("=" * 100)

        except KeyboardInterrupt:
            print("Exiting")
            self._ended = True

        latch.wait()
        server_socket.close()

    def handle_accept(self, server_socket: socket.socket, latch: CountDownLatch) -> None:
        while not self._ended:
            try:
                conction, adres = server_socket.accept()
                conction.settimeout(self.timeout)
                handler = self.request_handler_cls(conction, adres, self)
                print("Handling request... ", end="")
                handler.handle()
                print("OK")
            except socket.timeout:
                pass
            except Exception:
                print("FAILED")
                print(datetime.datetime.now())
                traceback.print_exc()
                print()

        latch.count_down()


class HTTPServer(TCPServer):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        backlog_size: int = 1,
        max_workers: int = 1,
        timeout: tp.Optional[float] = None,
        request_handler_cls: tp.Type[BaseRequestHandler] = BaseHTTPRequestHandler,
    ):
        super().__init__(host, port, backlog_size, max_workers, timeout, request_handler_cls)

