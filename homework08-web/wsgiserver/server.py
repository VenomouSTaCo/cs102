import typing
import typing as tp

from .request import WSGIRequest
from .response import WSGIResponse
import socket

from myhttpserver import BaseHTTPRequestHandler, HTTPServer

Address = tp.Tuple[str, int]


class ApplicationType:
    def __call__(self, *args: tp.Tuple, **kwargs) -> typing.Iterable[bytes]:  # type:ignore
        pass


class WSGIServer(HTTPServer):  # type:ignore
    def __init__(self, timeout: tp.Optional[float] = 0.5, **kwargs) -> None:  # type:ignore
        if "request_handler_cls" not in kwargs:
            kwargs["request_handler_cls"] = WSGIRequestHandler
        super().__init__(timeout=timeout, **kwargs)
        self.app: tp.Optional[ApplicationType] = None

    def set_app(self, app: ApplicationType) -> None:
        self.app = app

    def get_app(self) -> tp.Optional[ApplicationType]:
        return self.app


class WSGIRequestHandler(BaseHTTPRequestHandler):  # type:ignore
    request_klazz = WSGIRequest
    response_klazz = WSGIResponse

    def __init__(
        self, client_socket: socket.socket, address: Address, server: WSGIServer, *args, **kwargs
    ) -> None:
        super().__init__(client_socket, address, server, *args, **kwargs)
        self.server = server  # because we want to explicitly specify that we have wsgi server

    def handle_request(self, request: WSGIRequest) -> WSGIResponse:
        environ = request.to_environ()
        environ["SERVER_NAME"] = self.address[0]
        environ["SERVER_PORT"] = self.address[1]
        response = WSGIResponse()
        app = self.server.get_app()
        body_iterable = app(environ, response.start_response)  # type:ignore
        response.body = b"".join(body_iterable)
        return response
