from __future__ import annotations

import socket
import traceback
import typing as tp
from datetime import datetime

from httptools import HttpRequestParser
from httptools.parser.errors import *

from .request import HTTPRequest
from .response import HTTPResponse

if tp.TYPE_CHECKING:
    from .server import TCPServer

Address = tp.Tuple[str, int]

BUFFER_SIZE = 1024


class BaseRequestHandler:
    def __init__(self, client_socket: socket.socket, address: Address, server: TCPServer) -> None:
        self.client_socket = client_socket
        self.address = address
        self.server = server

    def handle(self) -> None:
        self.close()

    def close(self) -> None:
        self.client_socket.close()


class EchoRequestHandler(BaseRequestHandler):
    def handle(self) -> None:
        try:
            data = self.client_socket.recv(BUFFER_SIZE)
        except (socket.timeout, BlockingIOError):
            pass
        else:
            self.client_socket.sendall(data)
        finally:
            self.close()


class BaseHTTPRequestHandler(BaseRequestHandler):
    request_klazz = HTTPRequest
    response_klazz = HTTPResponse

    def __init__(self, *args, **kwargs) -> None:  # type:ignore
        super().__init__(*args, **kwargs)
        self.parser = HttpRequestParser(self)

        self._url: bytes = b""
        self._headers: tp.Dict[bytes, bytes] = {}
        self._body: bytes = b""
        self._parsed = False

    def handle(self) -> None:
        request = self.parse_request()
        if request:
            try:
                response = self.handle_request(request)
            except Exception:
                print(datetime.now())
                traceback.print_exc()
                print()
                response = self.response_klazz(status=500, headers={}, body=b"")
        else:
            response = self.response_klazz(status=400, headers={}, body=b"")
        self.handle_response(response)
        self.close()

    def parse_request(self) -> tp.Optional[HTTPRequest]:
        while not self._parsed:
            try:
                data = self.client_socket.recv(BUFFER_SIZE)
            except (
                socket.timeout,
                BlockingIOError,
            ):
                break
            if data == b"":
                break
            try:
                self.parser.feed_data(data)
            except (
                HttpParserError,  # type: ignore
                HttpParserInvalidMethodError,  # type: ignore
                HttpParserInvalidURLError,  # type: ignore
                HttpParserCallbackError,  # type: ignore
                HttpParserInvalidStatusError,  # type: ignore
                HttpParserUpgrade,  # type: ignore
            ):
                break
        if self._parsed:
            return self.request_klazz(
                self.parser.get_method(), self._url, self._headers, self._body
            )
        return None

    def handle_request(self, request: HTTPRequest) -> HTTPResponse:
        return self.response_klazz(200, {}, self.create_response(request))

    @staticmethod
    def create_response(request):
        return "Hello from HTTP Server. Your request: [".encode() + request.body + "]".encode()

    def handle_response(self, response: HTTPResponse) -> None:
        self.client_socket.sendall(response.to_http1())

    def on_url(self, url: bytes) -> None:
        self._url = url

    def on_header(self, name: bytes, value: bytes) -> None:
        self._headers[name] = value

    def on_body(self, body: bytes) -> None:
        self._body = body

    def on_message_complete(self) -> None:
        self._parsed = True
