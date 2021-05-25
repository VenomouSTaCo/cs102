import dataclasses
import http.client
import typing as tp


@dataclasses.dataclass
class HTTPResponse:
    status: int
    headers: tp.Dict[str, str] = dataclasses.field(default_factory=dict)
    body: bytes = b""

    def to_http1(self) -> bytes:
        response = b"HTTP/1.1 "
        response += f"{self.status} {http.client.responses[self.status]}\r\n".encode()
        for header_key in self.headers:
            response += header_key.encode() + b": " + self.headers[header_key].encode() + b"\r\n"
        return response + b"\r\n" + self.body
