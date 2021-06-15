import dataclasses
import io
import sys
import typing as tp
from urllib.parse import unquote

from myhttpserver import HTTPRequest


def path_resolver(path: str) -> str:
    splitted = path.split("/")
    curr: tp.List[str] = []
    for i in splitted:
        if i == "..":
            try:
                curr.pop()
            except IndexError:
                pass
        elif i == ".":
            continue
        else:
            curr.append(i)
    try:
        if "." in curr[-2] and curr[-1] == "":
            del curr[-1]
    except IndexError:
        pass
    curr[-1] = curr[-1].split("?", 1)[0]
    return "/".join(curr)


def url_normalize(path: str) -> str:
    normalized_path = path_resolver(path.replace("//", "/"))
    return unquote(normalized_path) + (
        "index.html" if len(normalized_path) == 0 or normalized_path[-1] == "/" else ""
    )


@dataclasses.dataclass
class WSGIRequest(HTTPRequest):  # type:ignore
    def to_environ(self) -> tp.Dict[str, tp.Any]:
        environ = {
            "REQUEST_METHOD": self.method.decode(),
            "SCRIPT_NAME": "",
            "PATH_INFO": self._get_path_info(),  # type:ignore
            "QUERY_STRING": self._get_query_string(),  # type:ignore
            "CONTENT_TYPE": self.headers.get(b"Content-Type", b"").decode(),  # type:ignore
            "CONTENT_LENGTH": self.headers.get(b"Content-Length", b"").decode(),
            "SERVER_NAME": "127.0.0.1",
            "SERVER_PORT": "8080",
            "SERVER_PROTOCOL": b"HTTP/1.1",
            "HTTP_Variables": None,
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": b"http",
            "wsgi.input": io.BytesIO(self.body),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": True,
            "wsgi.multiprocess": False,
            "wsgi.run_once": True,
        }

        environ.update(
            {
                self.get_var_name(header_name): self.headers[header_name].decode()  # type:ignore
                for header_name in self.headers
            }
        )

        return environ
