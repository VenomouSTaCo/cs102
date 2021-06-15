import http.client
import typing as tp
from urllib.parse import parse_qsl

from slowapi.request import Request
from slowapi.router import Route


class SlowAPI:
    def __init__(self):
        self.routes: tp.List[Route] = []
        self.middlewares = []

    def __call__(self, environ, start_response):
        route = self._find_route(environ)

        args = self.__get_args(route, environ)

        query = dict(parse_qsl(environ["QUERY_STRING"]))

        request = Request(
            environ["PATH_INFO"], environ["REQUEST_METHOD"], query, environ["wsgi.input"], environ
        )
        response = route.func(request, *args)
        start_response(
            f"{response.status} {http.client.responses[response.status]}", response.headers
        )

        return [str(response).encode()]

    def _find_route(self, environ) -> Route:
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"]
        path_splitted = environ["PATH_INFO"].rsplit("/", 1)[0]

        for route in self.routes:
            if route.method == method and (
                path == route.path or path_splitted == route.path.rsplit("/", 1)[0]
            ):
                return route
        raise Exception("No such route")

    @staticmethod
    def __get_args(route: Route, environ) -> tp.List[str]:
        if "{" in route.path:
            args = environ["PATH_INFO"][route.path.find("{") :].split("/")
            if len(args) == 1 and args[0] == "":
                args = []
        else:
            args = []
        return args

    def route(self, path=None, method=None, **options):
        def decorator(func):
            self.routes.append(Route(path, method, func))

        return decorator

    def get(self, path=None, **options):
        return self.route(path, method="GET", **options)

    def post(self, path=None, **options):
        return self.route(path, method="POST", **options)

    def patch(self, path=None, **options):
        return self.route(path, method="PATCH", **options)

    def put(self, path=None, **options):
        return self.route(path, method="PUT", **options)

    def delete(self, path=None, **options):
        return self.route(path, method="DELETE", **options)

    def add_middleware(self, middleware) -> None:
        self.middlewares.append(middleware)
